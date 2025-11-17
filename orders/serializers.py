from rest_framework import serializers
from .models import Product, Payment, Order, OrderNotification, IbanNumber


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class IbanNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = IbanNumber
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    type_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        extra_fields = ['type_display']

    def get_type_display(self, obj):
        # Aktif dile göre çevirilmiş choice label'ı döner
        return obj.get_type_display()


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class OrderNotificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderNotification
        fields = '__all__'
        extra_fields = ['status_display']

    def get_status_display(self, obj):
        # Aktif dile göre çevirilmiş choice label'ı döner
        return obj.get_status_display()
