from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Product,  Payment, Order,OrderNotification
from .serializers import ProductSerializer, PaymentSerializer, OrderSerializer, OrderNotificationSerializer
import random
from django.db import transaction

# Create your views here.

class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
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
        serializer = OrderNotificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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