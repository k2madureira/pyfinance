
from django.urls import path

from ..views import QuotesView, QuoteWithTickerView

urlpatterns = [
  path('quotes', QuotesView.as_view(), name='functions_quotes'),
  path('quotes/<str:ticker>', QuoteWithTickerView.as_view(), name='functions_quotes_ticker'),
]
