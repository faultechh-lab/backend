from django.shortcuts import render
from .serializers import NotificationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
# Create your views here.

class NotificationListView(APIView):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

class NotificationCreateView(APIView):
    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationDeleteView(APIView):
    def delete(self, request, pk):
        notification = Notification.objects.get(pk=pk)
        notification.delete()
        return Response({"message": "Notification deleted successfully"},status=status.HTTP_200_OK)