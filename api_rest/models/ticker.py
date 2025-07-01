from django.db import models
from django.utils import timezone

class Ticker(models.Model):
  symbol = models.CharField(max_length=20, unique=True)
  name = models.CharField(max_length=200)
  exchange = models.CharField(max_length=40)
  asset_type = models.CharField(max_length=40, null=True, blank=True)
  ipo_date = models.DateTimeField(default=timezone.now)
  delisting_date = models.DateTimeField(null=True, blank=True, default=None)
  status = models.CharField(max_length=20)

  def __str__(self):
    return f'Ticker: {self.symbol} | Name: {self.name}'