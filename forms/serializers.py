from rest_framework import serializers
from .models import Form,FormImage
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','avatar']

class FormImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormImage
        fields = '__all__'

class FormSerializer(serializers.ModelSerializer):
    images = FormImageSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    class Meta:
        model = Form
        fields = '__all__'
