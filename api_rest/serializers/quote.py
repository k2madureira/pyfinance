from rest_framework import serializers

from ..models import Quote

class QuoteSerializer(serializers.ModelSerializer):
  class Meta:
    model = Quote
    fields = '__all__'
    ordering = ['-date']

class QuoteTickerSerializer(serializers.ModelSerializer):
  class Meta:
    model = Quote
    fields = ['id', 'volume']
    ordering = ['-date']

  