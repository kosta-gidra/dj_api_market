import pytest
from rest_framework.test import APIClient


@pytest.fixture()
def client():
    """Фикстура создания клиента"""
    return APIClient()


@pytest.fixture()
def create_user(client):
    """Фикстура создания нового пользователя"""
    response = client.post('/api/user/register', data=dict(first_name='First',
                                                           last_name='Second',
                                                           email='FirstSecond@mail.ru',
                                                           password='qwer1234A',
                                                           company='CompanyOne',
                                                           position='worker',
                                                           type='shop',
                                                           test='test'))
    return response


@pytest.fixture()
def confirm_created_user(create_user, client):
    """Фикстура подтверждения регистрации"""
    data = create_user.json()
    if data['Status']:
        response = client.post('/api/user/register/confirm', data=dict(email='FirstSecond@mail.ru',
                                                                       token=data['Token']))
        return response


@pytest.mark.django_db
def test_reg(create_user):
    """Тест регистрации пользователя"""
    assert create_user.status_code == 200
    data = create_user.json()
    assert data['Status']


@pytest.mark.django_db
def test_confirm_reg(confirm_created_user):
    """Тест подтверждения регистрации пользователя"""
    assert confirm_created_user.status_code == 200
    data = confirm_created_user.json()
    assert data['Status']


@pytest.mark.django_db
def test_login(confirm_created_user, client):
    """Тест авторизации"""
    response = client.post('/api/user/login', data=dict(email='FirstSecond@mail.ru', password='qwer1234A'))
    assert response.status_code == 200
    data = response.json()
    assert data['Status']
