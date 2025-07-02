from rest_framework import serializers

from ..models import Ticker
from .quote import QuoteSerializer

class TickerSerializer(serializers.ModelSerializer):
  quotes = serializers.SerializerMethodField()
  class Meta:
    model = Ticker
    fields = ['id', 'symbol', 'name', 'exchange', 'asset_type', 'ipo_date', 'delisting_date', 'status', 'quotes']
  
  def get_quotes(self, obj): 
    quotes_queryset = obj.quotes.all().order_by('-date') 
    return QuoteSerializer(quotes_queryset, many=True).data
  
class TickerListSerializer(serializers.ModelSerializer):
  class Meta:
    model = Ticker
    fields = fields = ['id', 'symbol', 'name', 'exchange', 'asset_type', 'ipo_date', 'delisting_date', 'status']
    ordering = ['-date']