from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from ..models import Quote
from ..serializers import QuoteSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5          
    page_size_query_param = 'perPage' 
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'items': data
        })

class QuotesView(APIView):
    def get(self, request):
        quotes = Quote.objects.all().order_by('date')

        
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(quotes, request, view=self)
        serializer = QuoteSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


    def post(self, request):
       
        serializer = QuoteSerializer(data=request.data)
        if serializer.is_valid():
            ticker = serializer.validated_data.get('ticker')
            date = serializer.validated_data.get('date')

            try:
              if Quote.objects.filter(ticker=ticker, date=date).exists():
                  return Response(
                    {'error': 'There is already a quote for this Ticker on this date.'},
                    status=status.HTTP_409_CONFLICT
                  )
            except TypeError:
                
                return Response(
                    {'error': 'Invalid date format for verification.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class QuoteWithTickerView(APIView):
    def get(self, request, ticker):

        try:
            quote = Quote.objects.get(ticker=ticker)
            serializer = QuoteSerializer(quote)
            return Response(serializer.data)
        except Quote.DoesNotExist:
            return Response({'error': 'Ticker not found'}, status=status.HTTP_404_NOT_FOUND)
       
