from distutils.util import strtobool

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Sum, F, QuerySet
from django.http import JsonResponse

from requests import get
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from yaml import load as load_yaml, Loader

from market.models import ProductInfo, Category, Product, Shop, Parameter, ProductParameter, Order
from market.permissions import IsShop
from market.serializers import ShopSerializer, OrderSerializer


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    # Администратор магазина устанавливается в момент создания магазина.
    # Если магазин уже существует, то при запросе обновления прайса происходит
    # проверка - является ли отправитель запроса администратором этого магазина.

    permission_classes = [IsAuthenticated, IsShop]

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

                shop_obj, created = Shop.objects.get_or_create(name=data['shop'])

                # привязываем пользователя к созданному магазину
                if created:
                    shop_obj.user = request.user
                    shop_obj.url = url
                    shop_obj.save()

                # проверяем является ли пользователь администратором магазина
                if shop_obj.user == request.user or created:

                    for category in data['categories']:
                        category_obj, _ = Category.objects.get_or_create(id=category['id'],
                                                                         name=category['name'],
                                                                         )
                        category_obj.shops.add(shop_obj.id)
                        category_obj.save()
                    ProductInfo.objects.filter(shop_id=shop_obj.id).delete()

                    for product in data['goods']:
                        product_obj, _ = Product.objects.get_or_create(name=product['name'],
                                                                       category_id=product['category']
                                                                       )

                        product_info_obj, _ = ProductInfo.objects.get_or_create(product_id=product_obj.id,
                                                                                shop_id=shop_obj.id,
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
                else:
                    return JsonResponse({'Status': False, 'Errors': 'Обновлять прайс может '
                                                                    'только администратор магазина'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PartnerState(APIView):
    """
    Класс для работы со статусом поставщика

    """

    permission_classes = [IsAuthenticated, IsShop]

    # получить текущий статус
    def get(self, request, *args, **kwargs):
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    # изменить текущий статус
    def post(self, request, *args, **kwargs):
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


# class PartnerOrders(APIView):
#     """
#     Класс для получения заказов поставщиками
#     """
#     def get(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
#
#         if request.user.type != 'shop':
#             return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
#
#         order = Order.objects.filter(
#             ordered_items__product_info__shop__user_id=request.user.id).exclude(state='basket').prefetch_related(
#             'ordered_items__product_info__product__category',
#             'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
#             total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
#
#         serializer = OrderSerializer(order, many=True)
#         return Response(serializer.data)


class PartnerOrders(ReadOnlyModelViewSet):
    """
    Класс для получения заказов поставщиками
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsShop]

    def get_queryset(self):
        queryset = Order.objects.filter(
            ordered_items__product_info__shop__user_id=self.request.user.id).exclude(state='basket').distinct()

        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset
