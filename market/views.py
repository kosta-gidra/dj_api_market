from pprint import pprint

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from requests import get
from django.shortcuts import render
from rest_framework.filters import SearchFilter

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from yaml import load as load_yaml, Loader

from market.models import ProductInfo, Category, Product, Shop, Parameter, ProductParameter
from market.serializers import ProductInfoSerializer, CategorySerializer, ProductSerializer


class MarketView(ReadOnlyModelViewSet):
    """
    Класс для отображения товаров с возможностью поиска по имени и фильтрации по магазину и категории.
    """
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['shop', 'product__category']
    search_fields = ['product__name']


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                pprint(data)

                shop, _ = Shop.objects.get_or_create(name=data['shop'])
                Shop.objects.update(url=url)
                for category in data['categories']:
                    category_obj, _ = Category.objects.get_or_create(id=category['id'],
                                                                     name=category['name'],
                                                                     )
                    category_obj.shops.add(shop.id)
                    category_obj.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for product in data['goods']:
                    product_obj, _ = Product.objects.get_or_create(name=product['name'],
                                                                   category_id=product['category']
                                                                   )

                    product_info_obj, _ = ProductInfo.objects.get_or_create(product_id=product_obj.id,
                                                                            shop_id=shop.id,
                                                                            model=product['model'],
                                                                            quantity=product['quantity'],
                                                                            price=product['price'],
                                                                            price_rrc=product['price_rrc'],
                                                                            external_id=product['id']
                                                                            )
                    for parameter, value in product['parameters'].items():
                        parameter_obj, _ = Parameter.objects.get_or_create(name=parameter)
                        ProductParameter.objects.create(product_info_id=product_info_obj.id,
                                                        parameter_id=parameter_obj.id,
                                                        value=value)
            return JsonResponse({'Status': True})
