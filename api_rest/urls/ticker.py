
from django.urls import path

from ..views import TickersView, TickerWithSymbolView, LoadTickers

urlpatterns = [
  path('tickers', TickersView.as_view(), name='functions_tickers'),
  path('tickers/load', LoadTickers.as_view(), name='functions_tickers_load'),
  path('tickers/<str:symbol>', TickerWithSymbolView.as_view(), name='functions_tickers_symbol'),
  
]
