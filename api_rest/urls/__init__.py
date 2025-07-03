from django.urls import path, include

from .quote import urlpatterns as quote_urlpatterns
from .ticker import urlpatterns as ticker_urlpatterns

urlpatterns = [
    path('quotes/', include(quote_urlpatterns)),
    path('tickers/', include(ticker_urlpatterns)),
]