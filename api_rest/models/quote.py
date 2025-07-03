from django.db import models
from django.utils import timezone

from .ticker import Ticker

class Quote(models.Model):
  ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='quotes')
  close_price = models.DecimalField(max_digits=20, decimal_places=2)
  volume = models.BigIntegerField(default=0)
  date = models.DateTimeField(default=timezone.now)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f'Ticker: {self.ticker} | Date: {self.date}'