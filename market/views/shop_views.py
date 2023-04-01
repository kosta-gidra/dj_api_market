from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from market.models import ProductInfo, Order, OrderItem
from market.serializers import ProductInfoSerializer, OrderSerializer, OrderItemSerializer
# from market.signals import new_order
from market.tasks import send_simple_mail_task


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


class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """

    permission_classes = [IsAuthenticated]

    # получить корзину
    def get(self, request, *args, **kwargs):
        basket = Order.objects.filter(user=request.user, state='basket').distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    # добавить позиции в корзину
    def post(self, request, *args, **kwargs):

        basket, _ = Order.objects.get_or_create(user=request.user, state='basket')
        objects_created = 0
        ordered_items = request.data.get('ordered_items')
        if ordered_items:
            for order_item in ordered_items:
                order_item.update({'order': basket.id})
                print(order_item)
                serializer = OrderItemSerializer(data=order_item)
                if serializer.is_valid():
                    try:
                        serializer.save()
                    except IntegrityError as error:
                        return JsonResponse({'Status': False, 'Errors': str(error)})
                    else:
                        objects_created += 1
                else:
                    JsonResponse({'Status': False, 'Errors': serializer.errors})
            return JsonResponse({'Status': True, 'Создано объектов': objects_created})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # удалить товары из корзины
    def delete(self, request, *args, **kwargs):

        items_string = request.data.get('items')
        if items_string:
            items_list = items_string.split(',')
            basket = Order.objects.filter(user=request.user, state='basket')
            if basket:
                query = Q()
                objects_deleted = False
                for order_item_id in items_list:
                    if order_item_id.isdigit():
                        query = query | Q(order_id=basket[0].id, id=order_item_id)
                        objects_deleted = True
                if objects_deleted:
                    deleted_count = OrderItem.objects.filter(query).delete()[0]

                    return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
            return JsonResponse({'Status': False, 'Errors': 'Корзина не существует'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # редактировать корзину
    def put(self, request, *args, **kwargs):

        ordered_items = request.data.get('ordered_items')
        if ordered_items:
            basket = Order.objects.filter(user=request.user, state='basket')
            if basket:
                objects_updated = 0
                for order_item in ordered_items:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(
                            order_id=basket[0].id,
                            id=order_item['id']).update(quantity=order_item['quantity'])

                return JsonResponse({'Status': True, 'Обновлено объектов': objects_updated})
            return JsonResponse({'Status': False, 'Errors': 'Корзина не существует'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderView(APIView):
    """
    Класс для получения и размешения заказов пользователями
    """

    permission_classes = [IsAuthenticated]

    # получить мои заказы
    def get(self, request, *args, **kwargs):
        order = Order.objects.filter(
            user_id=request.user.id).exclude(state='basket').distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    # разместить заказ из корзины
    def post(self, request, *args, **kwargs):
        if {'contact'}.issubset(request.data):
            try:
                is_updated = Order.objects.filter(
                    user_id=request.user.id, state='basket').update(
                    contact_id=request.data['contact'],
                    state='new')
            except IntegrityError as error:
                print(error)
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
            else:
                if is_updated:
                    # отправить email о создании нового заказа, используя Signals:
                    # new_order.send(user_id=request.user.id)

                    # используя Celery
                    send_simple_mail_task.delay(user_id=request.user.id,
                                                title='Django-API-market: Обновление статуса заказа',
                                                message='Заказ сформирован')
                    return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
