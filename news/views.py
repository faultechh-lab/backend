from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from rest_framework.pagination import PageNumberPagination
from .models import News
from .serializers import NewsSerializer

# Create your views here.

class NewsListView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        queryset = News.objects.all().order_by('-created_at')
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('page_size') or 10)
        page = paginator.paginate_queryset(queryset, request)
        serializer = NewsSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class NewsCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = NewsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NewsDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, pk):
        news = News.objects.get(pk=pk)
        news.delete()
        return Response({"message": "News deleted successfully"},status=status.HTTP_200_OK)

class NewsUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def put(self, request, pk):
        news = News.objects.get(pk=pk)
        serializer = NewsSerializer(news, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
