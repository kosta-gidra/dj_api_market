from random import randint

import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from market.models import User, Contact, ConfirmEmailToken


@pytest.fixture()
def client():
    """Фикстура создания клиента"""
    return APIClient()


@pytest.fixture()
def create_user():
    """Фикстура создания пользователя и токена для авторизации"""

    user = User.objects.create_user(first_name='First',
                                    last_name='Second',
                                    email=f'FirstSecond{randint(0, 1000)}@mail.ru',
                                    password='qwer1234A',
                                    company='CompanyOne',
                                    position='worker',
                                    type='shop',
                                    )
    return user


@pytest.fixture()
def create_token(create_user):
    """Фикстура создания пользователя и токена для авторизации"""

    create_user.is_active = True
    create_user.save()
    token, _ = Token.objects.get_or_create(user_id=create_user.id)
    return token


@pytest.fixture()
def client_auth(create_token):
    """Фикстура создания клиента с заголовками для аваторизации"""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + create_token.key)
    return client


@pytest.fixture()
def create_contact(create_token):
    """Фикстура создания контакта пользователя"""

    contact = Contact.objects.create(user_id=create_token.user.id,
                                     city='NewCity',
                                     street='WestStreet',
                                     phone=f'+7999888{randint(1000, 9999)}',
                                     house='50'
                                     )

    return contact


@pytest.mark.django_db
def test_reg(client):
    """Тест регистрации пользователя"""

    response = client.post('/api/user/register', data=dict(first_name='First',
                                                           last_name='Second',
                                                           email='FirstSecond@mail.ru',
                                                           password='qwer1234A',
                                                           company='CompanyOne',
                                                           position='worker',
                                                           type='shop',
                                                           test='test'
                                                           ))
    user = User.objects.get(first_name='First',
                            last_name='Second',
                            email='FirstSecond@mail.ru',
                            company='CompanyOne',
                            position='worker',
                            type='shop',
                            is_active=False
                            )

    token = ConfirmEmailToken.objects.get(user_id=user.id)

    assert response.status_code == 200
    data = response.json()
    assert data['Status']
    assert data['Token'] == token.key
    assert user


@pytest.mark.django_db
def test_confirm_reg(create_user, client):
    """Тест подтверждения регистрации пользователя"""

    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=create_user.id)
    response = client.post('/api/user/register/confirm', data=dict(email=f'{create_user.email}', token=token.key))

    user = User.objects.get(id=create_user.id, is_active=True)

    assert response.status_code == 200
    data = response.json()
    assert data['Status']
    assert user


@pytest.mark.django_db
def test_login(create_user, client):
    """Тест авторизации"""
    create_user.is_active = True
    create_user.save()

    response = client.post('/api/user/login', data=dict(email=f'{create_user.email}', password='qwer1234A'))
    assert response.status_code == 200
    data = response.json()
    assert data['Status']


@pytest.mark.django_db
def test_edit_user(client_auth):
    """Тест изменения данных пользователя"""

    response = client_auth.post('/api/user/details', data=dict(first_name='First',
                                                               last_name='Third',
                                                               email='Third@mail.ru',
                                                               password='qwer1234AA',
                                                               company='CompanyTwo',
                                                               position='Dir',
                                                               test='test'
                                                               ))

    # Проверка на корректное изменение данных пользователя, после смены пароля статус активности - False
    user = User.objects.get(first_name='First',
                            last_name='Third',
                            email='Third@mail.ru',
                            company='CompanyTwo',
                            position='Dir',
                            is_active=False
                            )

    assert response.status_code == 200
    data = response.json()
    assert data['Status']
    assert user


@pytest.mark.django_db
def test_create_contact(create_token, client):
    """Тест создания контактов пользователя"""

    client.credentials(HTTP_AUTHORIZATION='Token ' + create_token.key)

    response = client.post('/api/user/contact/', data=dict(city='NewCity',
                                                           street='WestStreet',
                                                           phone='+79998883344',
                                                           house='50'
                                                           ))

    contact = Contact.objects.get(user_id=create_token.user.id,
                                  city='NewCity',
                                  street='WestStreet',
                                  phone='+79998883344',
                                  house='50'
                                  )

    assert response.status_code == 200
    data = response.json()
    assert data['city'] == contact.city
    assert data['street'] == contact.street
    assert data['phone'] == contact.phone
    assert data['house'] == contact.house


@pytest.mark.django_db
def test_edit_contact(create_contact, client):
    """Тест редактирования контакта пользователя"""

    token = Token.objects.get(user_id=create_contact.user.id)
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    response = client.put(f'/api/user/contact/{create_contact.id}/', data=dict(city='OtherCity',
                                                                               street='OtherStreet',
                                                                               phone='+79998883300',
                                                                               house='01'
                                                                               ))
    contact = Contact.objects.get(user_id=create_contact.user.id,
                                  city='OtherCity',
                                  street='OtherStreet',
                                  phone='+79998883300',
                                  house='01'
                                  )

    assert response.status_code == 200
    data = response.json()
    assert data['city'] == contact.city
    assert data['street'] == contact.street
    assert data['phone'] == contact.phone
    assert data['house'] == contact.house
