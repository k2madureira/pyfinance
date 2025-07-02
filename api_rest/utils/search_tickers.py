
from rest_framework.response import Response
from rest_framework import status
from datetime import timezone
import pandas as pd
import requests
import os 

from ..models import Quote, Ticker

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
ALPHA_VANTAGE_BASE_URL = os.getenv('ALPHA_VANTAGE_BASE_URL')

def get_tickers_info(symbols: list):
 
  for symbol in symbols: 
    
    ticker = Ticker.objects.prefetch_related('quotes').get(symbol=symbol)

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
          {'error': f"API Error: {data['Error Message']}"}, 
          status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
      if "Note" in data:
          
        return Response(
          {'error': f"API Note: {data['Note']}. Rate limit might be exceeded."}, 
          status=status.HTTP_429_TOO_MANY_REQUESTS 
        )
      if "Time Series (Daily)" not in data:

        return Response(
          {'error': f"Data not found for symbol: {symbol}"}, 
          status=status.HTTP_404_NOT_FOUND
        )

      time_series_data = data["Time Series (Daily)"]
                    
      df = pd.DataFrame.from_dict(time_series_data, orient='index')
      df.index = pd.to_datetime(df.index)
      df = df.rename(columns={'4. close': 'close', '5. volume': 'volume'})
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
  
  return True