
from django.urls import path

from ..views import TickersView, TickerWithSymbolView, LoadTickers, QuoteWithTickerView

urlpatterns = [
  path('', TickersView.as_view(), name='functions_tickers'),
  path('load', LoadTickers.as_view(), name='functions_tickers_load'),
  path('<str:symbol>', TickerWithSymbolView.as_view(), name='functions_tickers_symbol'),
  path('<str:ticker>/quotes', QuoteWithTickerView.as_view(), name='functions_quotes_ticker'),
  
]
