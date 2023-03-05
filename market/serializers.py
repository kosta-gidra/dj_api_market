from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer

from market.models import Shop, Category, Product, ProductInfo, ProductParameter, Parameter, User, Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone']
        read_only_fields = ['id']
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts', 'type']
        read_only_fields = ['id', 'type']


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'url']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['name', 'category']


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['name']


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = ParameterSerializer(read_only=True)

    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ['model', 'quantity', 'price', 'price_rrc', 'external_id', 'product', 'product_parameters']
