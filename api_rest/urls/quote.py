
from django.urls import path

from ..views import QuotesView, QuoteWithTickerView

urlpatterns = [
  path('', QuotesView.as_view(), name='functions_quotes'),
]
