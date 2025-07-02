from datetime import datetime, timedelta
import requests
import pandas as pd
import io 
import os 

from django.db import transaction
from django.core.management.base import CommandError
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from ..models import Ticker, Quote
from ..serializers import TickerSerializer
from ..utils import get_tickers_info, console_log


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
        try:

            ticker = Ticker.objects.prefetch_related('quotes').get(symbol=symbol)
            serialized = TickerSerializer(ticker).data

            quotes_data = serialized.get('quotes', []) 
            needs_api_fetch = False

            if not quotes_data:
                needs_api_fetch = True
            else:    
                quote = quotes_data[0]
                quote_date_str = quote.get('date')
                quote_created_at_str = quote.get('created_at')

                if quote_date_str:
                    
                    try:
            
                        quote_date = datetime.fromisoformat(quote_date_str.replace('Z', '+00:00')).date()
                        quote_created_at = datetime.fromisoformat(quote_created_at_str.replace('Z', '+00:00')).date()
                      
                        now_utc = timezone.now()       
                        yesterday_utc = now_utc - timedelta(days=1)          
                        yesterday = yesterday_utc.date()

                   
                        if quote_date < yesterday or quote_created_at < yesterday: 
                            needs_api_fetch = True

                    except ValueError:
                        print(f"Could not parse date string: {quote_date_str}")
                        needs_api_fetch = True
                else:
                     needs_api_fetch = True

            if needs_api_fetch:

                get_tickers_info([symbol])
                ticker = Ticker.objects.prefetch_related('quotes').get(symbol=symbol)
                serialized = TickerSerializer(ticker).data
              
                
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