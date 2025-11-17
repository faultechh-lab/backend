from django.urls import path
from .views import (
    ProductListView,
    PaymentCreateView,
    OrderCreateView,
    OrderNotificationCreateView,
    PurchaseCreateView,
    IbanNumberView,
    MyOrderNotificationView
)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('iban-number/', IbanNumberView.as_view(), name='iban-number'),
    path('payments/create/', PaymentCreateView.as_view(), name='payment-create'),
    path('orders/create/', OrderCreateView.as_view(), name='order-create'),
    path('order-notifications/create/', OrderNotificationCreateView.as_view(), name='order-notification-create'),
    path('my-order-notifications/', MyOrderNotificationView.as_view(), name='my-order-notification'),
    
    path('purchase/', PurchaseCreateView.as_view(), name='purchase-create'),
]
