from pprint import pprint

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from requests import get

from django.shortcuts import render
from rest_framework.filters import SearchFilter
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from yaml import load as load_yaml, Loader

from market.models import ProductInfo, Category, Product, Shop, Parameter, ProductParameter, ConfirmEmailToken
from market.serializers import ProductInfoSerializer, CategorySerializer, ProductSerializer, UserSerializer


class RegisterAccount(APIView):
    """
    Класс для регистрации пользователей.
    При успешной регистрации пользователю высылается email с токеном
    """
    def post(self, request, *args, **kwargs):

        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            # errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                # request.data._mutable = True
                # request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()

                    # Отправить пользователю письмо с токеном для подтверждения email
                    # new_user_registered.send(sender=self.__class__, user_id=user.id)

                    # удалить строку ---
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    # ------------------

                    return JsonResponse({'Status': True, 'Token': token.key})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса.
    При успешном подтверждении адреса изменяет статус пользователя на "активный"
    """
    def post(self, request, *args, **kwargs):

        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class MarketView(ReadOnlyModelViewSet):
    """
    Класс для отображения товаров
    с возможностью поиска по имени и фильтрации по магазину и категории
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
