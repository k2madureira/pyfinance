from datetime import datetime, timezone
import requests
import pandas as pd
import io 
import os 

from django.db import transaction
from django.core.management.base import CommandError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from ..models import Ticker, Quote
from ..serializers import TickerSerializer



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5          
    page_size_query_param = 'perPage' 
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'items': data
        })

class TickersView(APIView):
    def get(self, request):
        tickers = Ticker.objects.all().order_by('symbol')

        symbols_list = request.query_params.getlist('symbol')
        if symbols_list:
            tickers = tickers.filter(symbol__in=symbols_list)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(tickers, request, view=self)
        serializer = TickerSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


    def post(self, request):
       
        serializer = TickerSerializer(data=request.data)
        if serializer.is_valid():
            symbol = serializer.validated_data.get('symbol')

            if Ticker.objects.filter(symbol=symbol).exists():
                return Response(
                    { 'error': 'Already exist symbol.' },
                    status=status.HTTP_409_CONFLICT
                )
      
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class TickerWithSymbolView(APIView):
    def get(self, request, symbol):
        ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
        ALPHA_VANTAGE_BASE_URL = os.getenv('ALPHA_VANTAGE_BASE_URL')
        try:

            ticker = Ticker.objects.prefetch_related('quotes').get(symbol=symbol)
            serialized = TickerSerializer(ticker).data

            quotes_data = serialized.get('quotes', []) 

            first_quote_date = None
            needs_api_fetch = False

            if not quotes_data:
                needs_api_fetch = True
            else:    
                first_quote = quotes_data[0]
                first_quote_date_str = first_quote.get('date')

                if first_quote_date_str:
                    
                    try:
            
                        first_quote_date = datetime.fromisoformat(first_quote_date_str.replace('Z', '+00:00')).date()
                        today_utc = datetime.now(timezone.utc).date()
                        if first_quote_date < today_utc: 
                            needs_api_fetch = True

                    except ValueError:
                        print(f"Could not parse date string: {first_quote_date_str}")
                        needs_api_fetch = True
                else:
                     needs_api_fetch = True

            if needs_api_fetch:

                try:
                    params = {
                        "symbol": symbol,
                        "function": "TIME_SERIES_DAILY",
                        "apikey": ALPHA_VANTAGE_API_KEY,
                        "outputsize": "full" 
                    }

                    response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
                    response.raise_for_status() 
                    data = response.json()

                    
                    if "Error Message" in data:
                        return Response(
                            {'error': f"Alpha Vantage API Error: {data['Error Message']}"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                    if "Note" in data:
                        
                        return Response(
                            {'error': f"Alpha Vantage API Note: {data['Note']}. Rate limit might be exceeded."}, 
                            status=status.HTTP_429_TOO_MANY_REQUESTS 
                        )
                    if "Time Series (Daily)" not in data:
                        
                        return Response(
                            {'error': f"Daily time series data not found for symbol: {symbol}"}, 
                            status=status.HTTP_404_NOT_FOUND
                        )
                    
                    time_series_data = data["Time Series (Daily)"]

                    
                    df = pd.DataFrame.from_dict(time_series_data, orient='index')
                    df.index = pd.to_datetime(df.index)

                    df = df.rename(columns={'4. close': 'close', '5. volume': 'volume'})

                    for col in ['close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    quotes_from_api_list = df.reset_index().rename(columns={'index': 'date'}).to_dict(orient='records')

                    for q_data in quotes_from_api_list:
                        quote_date = q_data['date'].to_pydatetime()
                        quote_date = quote_date.replace(tzinfo=timezone.utc)

                        Quote.objects.update_or_create(
                            ticker=ticker,
                            date=quote_date,
                            defaults={
                                'close_price': q_data['close'],
                                'volume': q_data['volume'],
                            }
                        )
                    ticker = Ticker.objects.prefetch_related('quotes').get(symbol=symbol)
                    serialized = TickerSerializer(ticker).data

                    return Response(serialized)
                
                except requests.exceptions.RequestException as e:
                    return Response(
                        {'error': f'Lost connection to Alpha Vantage API: {str(e)}'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                except Exception as e:
                    return Response(
                        {'error': f'Error processing API data: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    ) 
                
            return Response(serialized)
        
        except Ticker.DoesNotExist:
            return Response(
                { 'error': 'Ticker not found' }, 
                status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
  
       

class LoadTickers(APIView):
    def get(self, request):

        ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
      
        if not ALPHA_VANTAGE_API_KEY:
            raise CommandError("ALPHA_VANTAGE_API_KEY environment variable is not set.")

    
        try:
            
            params = {
                "function": "LISTING_STATUS",
                "apikey": ALPHA_VANTAGE_API_KEY,
                "state": "active" 
            }
            response = requests.get(os.getenv('ALPHA_VANTAGE_BASE_URL'), params=params)
            response.raise_for_status() 

            csv_data = response.text
            df = pd.read_csv(io.StringIO(csv_data))
            
            with transaction.atomic():
                
                for index, row in df.iterrows():
                    symbol = row['symbol']
                    name = row['name']
                    exchange = row['exchange']
                    asset_type = row['assetType'] 
                    ipo_date_str = row['ipoDate']
                    delisting_date_str = row['delistingDate']
                    status = row['status']

                    
                    try:
                        
                        ipo_date = datetime.strptime(ipo_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue 

                    delisting_date = None
                    if pd.notna(delisting_date_str) and delisting_date_str != 'None': 
                        try:
                            delisting_date = datetime.strptime(delisting_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                        except ValueError:
                           
                            delisting_date = None

                    
                    ticker, created = Ticker.objects.update_or_create(
                        symbol=symbol, 
                        defaults={
                            'name': name,
                            'exchange': exchange,
                            'asset_type': asset_type,
                            'ipo_date': ipo_date,
                            'delisting_date': delisting_date,
                            'status': status,
                        }
                    )

            return Response({ 'msg': 'data loaded' })
        except requests.exceptions.RequestException as e:
            raise CommandError(f"Error connecting to Alpha Vantage API: {e}")
        except pd.errors.EmptyDataError:
            raise CommandError("API response is empty or not a valid CSV.")
        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e}")