from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Form, FormImage, Report, BlockedUser
from .serializers import FormSerializer, FormImageSerializer, ReportSerializer, BlockedUserSerializer
from .paginations import FormPagination
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from accounts.models import MembershipChoices

# Create your views here.

class FormListView(APIView):
    def get(self, request):
        queryset = Form.objects.filter(verified=True)
        
        # Filter out content from blocked users
        if request.user.is_authenticated:
            blocked_user_ids = BlockedUser.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
            queryset = queryset.exclude(user_id__in=blocked_user_ids)
            
        queryset = queryset.order_by('-created_at')
        paginator = FormPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = FormSerializer(page, many=True, context={'request': request})
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
    
    def _send_notification_email(self, user, form_instance):
        if user.membership_status != MembershipChoices.FREE:
            return
        subject = f"Yeni Form Bildirimi - {form_instance.title}"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
        admin_mail = getattr(settings, 'ORDER_NOTIFICATION_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
        
        to = [admin_mail] if admin_mail else []
        if not to:
            return

        text_body = "\n".join([
            subject,
            "",
            f"Kullanıcı: {user.username}",
            f"Email: {user.email}",
            f"Başlık: {form_instance.title}",
            f"Mesaj: {form_instance.message}",
            f"Tarih: {form_instance.created_at.strftime('%d.%m.%Y %H:%M')}",
        ])
        
        html_body = f"""
        <html><body>
        <div style='font-family:Arial,Helvetica,sans-serif;color:#0f172a;'>
          <h2 style='margin:0 0 12px 0;'>Yeni Form Bildirimi</h2>
          <p><strong>Kullanıcı:</strong> {user.username}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Başlık:</strong> {form_instance.title}</p>
          <p><strong>Mesaj:</strong><br/>{form_instance.message}</p>
          <p><strong>Tarih:</strong> {form_instance.created_at.strftime('%d.%m.%Y %H:%M')}</p>
        </div>
        </body></html>
        """
        
        msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
        msg.attach_alternative(html_body, "text/html")
        try:
            msg.send()
        except Exception:
            pass

    def post(self, request):
        serializer = FormSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(user=request.user)
            self._send_notification_email(request.user, instance)
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

class ReportCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserBlockView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        blocked_id = request.data.get('blocked_id')
        if not blocked_id:
            return Response({'detail': 'blocked_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if str(blocked_id) == str(request.user.id):
            return Response({'detail': 'You cannot block yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        BlockedUser.objects.get_or_create(blocker=request.user, blocked_id=blocked_id)
        return Response({'message': 'User blocked successfully'}, status=status.HTTP_201_CREATED)

class UserUnblockView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        blocked_id = request.data.get('blocked_id')
        if not blocked_id:
            return Response({'detail': 'blocked_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        BlockedUser.objects.filter(blocker=request.user, blocked_id=blocked_id).delete()
        return Response({'message': 'User unblocked successfully'}, status=status.HTTP_200_OK)
