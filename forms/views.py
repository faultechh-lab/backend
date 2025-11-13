from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Form,FormImage
from .serializers import FormSerializer,FormImageSerializer
from .paginations import FormPagination

# Create your views here.

class FormListView(APIView):
    def get(self, request):
        queryset = Form.objects.filter(verified=True).order_by('-created_at')
        paginator = FormPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = FormSerializer(page, many=True,context={'request':request})
        return paginator.get_paginated_response(serializer.data)

class FormMyListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        queryset = Form.objects.filter(user=request.user).order_by('-created_at')
        paginator = FormPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = FormSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class FormCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = FormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FormVerifiedView(APIView):
    def put(self, request, pk):
        form = Form.objects.get(pk=pk)
        form.verified = True
        form.save()
        return Response({'message': 'Form verified successfully'},status=status.HTTP_200_OK)

class FormDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, pk):
        form = Form.objects.get(pk=pk)
        if not (form.user_id == request.user.id or request.user.is_staff):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        form.delete()
        return Response({'message': 'Form deleted successfully'},status=status.HTTP_200_OK)

class FormUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def put(self, request, pk):
        form = Form.objects.get(pk=pk)
        if not (form.user_id == request.user.id or request.user.is_staff):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = FormSerializer(form, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FormImageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        try:
            form = Form.objects.get(pk=pk)
        except Form.DoesNotExist:
            return Response({'detail': 'Form not found'}, status=status.HTTP_404_NOT_FOUND)
        if not (form.user_id == request.user.id or request.user.is_staff):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({'detail': 'image file required'}, status=status.HTTP_400_BAD_REQUEST)
        image = FormImage.objects.create(form=form, image=file_obj)
        return Response(FormImageSerializer(image).data, status=status.HTTP_201_CREATED)