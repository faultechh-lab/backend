from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Product,  Payment, Order,OrderNotification,IbanNumber
from .serializers import ProductSerializer, PaymentSerializer, OrderSerializer, OrderNotificationSerializer,IbanNumberSerializer
import random
from django.db import transaction
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from accounts.models import MembershipChoices

# Create your views here.

class ProductListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class IbanNumberView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        products = IbanNumber.objects.all()
        serializer = IbanNumberSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PaymentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        """Create a payment intent/record for a product and quantity."""
        product_id = request.data.get('product') or request.data.get('product_id')
        amount = request.data.get('amount')
        pay_type = request.data.get('type') or 'CREDIT_CARD'
        if not product_id:
            return Response({'detail': 'product_id gerekli'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Ürün bulunamadı'}, status=status.HTTP_404_NOT_FOUND)
        # Eğer amount verilmemişse indirimi varsa onu, yoksa ürün fiyatını kullan
        try:
            amount_val = float(amount) if amount is not None else float(product.discount_price or product.price)
        except Exception:
            return Response({'detail': 'amount geçersiz'}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(user=request.user, product=product, amount=amount_val, type=pay_type)
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

class OrderCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        """Create an order from an existing payment record."""
        payment_id = request.data.get('payment') or request.data.get('payment_id')
        if not payment_id:
            return Response({'detail': 'payment_id gerekli'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payment = Payment.objects.get(pk=payment_id, user=request.user)
        except Payment.DoesNotExist:
            return Response({'detail': 'Ödeme bulunamadı'}, status=status.HTTP_404_NOT_FOUND)
        order_number = f"{random.randint(0, 999999):06d}"
        order = Order.objects.create(
            user=request.user,
            payment=payment,
            product=payment.product,
            quantity=1,
            total_price=payment.amount,
            number=order_number,
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderNotificationCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        product_id = request.data.get('product') or request.data.get('product_id')
        order_number = request.data.get('order_number') or request.data.get('number') or request.data.get('code')
        quantity = request.data.get('quantity') or 1
        if not product_id or not order_number:
            return Response({'detail': 'product ve order_number gerekli'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Ürün bulunamadı'}, status=status.HTTP_404_NOT_FOUND)
        existing = OrderNotification.objects.filter(user=request.user, product=product, order_number=str(order_number)).first()
        if existing:
            data = OrderNotificationSerializer(existing).data
            self._send_notification_email(request.user, existing)
            return Response(data, status=status.HTTP_200_OK)
        serializer = OrderNotificationSerializer(data={
            'product': product_id,
            'quantity': quantity,
            'order_number': str(order_number),
            'status': 'PENDING',
        })
        if serializer.is_valid():
            instance = serializer.save(user=request.user)
            self._send_notification_email(request.user, instance)
            return Response(OrderNotificationSerializer(instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_notification_email(self, user, notif: OrderNotification):
        if user.membership_status != MembershipChoices.FREE:
            return
        subject = f"Yeni Ödeme Bildirimi - {notif.order_number}"
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
            f"Ürün: {getattr(notif.product, 'title', '-')}",
            f"Adet: {notif.quantity}",
            f"Sipariş Numarası: {notif.order_number}",
        ])
        html_body = f"""
        <html><body>
        <div style='font-family:Arial,Helvetica,sans-serif;color:#0f172a;'>
          <h2 style='margin:0 0 12px 0;'>Yeni Ödeme Bildirimi</h2>
          <p><strong>Kullanıcı:</strong> {user.username}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Ürün:</strong> {getattr(notif.product, 'title', '-')}</p>
          <p><strong>Adet:</strong> {notif.quantity}</p>
          <p><strong>Sipariş Numarası:</strong> <span style='font-weight:800;color:#0ea5e9'>{notif.order_number}</span></p>
        </div>
        </body></html>
        """
        msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
        msg.attach_alternative(html_body, "text/html")
        try:
            msg.send()
        except Exception:
            pass

class MyOrderNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):        
        items = OrderNotification.objects.filter(user=request.user)
        serializer = OrderNotificationSerializer(items, many=True)    
        return Response(serializer.data, status=status.HTTP_200_OK)



class PurchaseCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        product_id = request.data.get('product') or request.data.get('product_id')
        amount = request.data.get('amount')
        pay_type = request.data.get('type') or 'CREDIT_CARD'
        if not product_id:
            return Response({'detail': 'product_id gerekli'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Ürün bulunamadı'}, status=status.HTTP_404_NOT_FOUND)
        # amount yoksa ürünün indirimli fiyatını, o da yoksa normal fiyatını kullan
        try:
            amount_val = float(amount) if amount is not None else float(product.discount_price or product.price)
        except Exception:
            return Response({'detail': 'amount geçersiz'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            payment = Payment.objects.create(user=request.user, product=product, amount=amount_val, type=pay_type)
            order_number = f"{random.randint(0, 999999):06d}"
            order = Order.objects.create(
                user=request.user,
                payment=payment,
                product=product,
                quantity=1,
                total_price=amount_val,
                number=order_number,
            )
        # Basit birleşik cevap: payment ve order
        return Response({
            'payment': PaymentSerializer(payment).data,
            'order': OrderSerializer(order).data,
        }, status=status.HTTP_201_CREATED)
