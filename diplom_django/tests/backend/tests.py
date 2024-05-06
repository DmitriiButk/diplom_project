import pytest
from backend.models import User
from model_bakery import baker
from rest_framework.test import APIClient
from django.urls import reverse


new_user = {
    'first_name': 'Andrei',
    'last_name': 'Ponomarenko',
    'email': 'Andryusha@mail.ru',
    'password': 'andrei1234',
    'company': 'Google',
    'position': 'CEO',
    'type': 'buyer'
}


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_factory():
    def factory(*args, **kwargs):
        return baker.make(User, *args, **kwargs)

    return factory


@pytest.mark.django_db
def test_create_user(client):
    """
    This test checks if a new user can be created successfully.
    """
    url = reverse('backend:user-register')
    response = client.post(path=url, data=new_user)
    assert response.status_code in (200, 201)
    assert response.json()['status'] is True


@pytest.mark.django_db
def test_login_user(client, user_factory):
    """
    This test checks if a new user can log in successfully after registration.
    """
    url = reverse('backend:user-register')
    response = client.post(path=url, data=new_user)
    assert response.json()['status'] is True

    user = User.objects.get(email=new_user['email'])
    user.is_active = True
    user.save()

    url = reverse('backend:user-login')
    response = client.post(path=url, data={'email': new_user['email'], 'password': new_user['password']})
    assert response.json()['status'] is True
    assert response.status_code in (200, 201)


@pytest.mark.django_db
def test_account_details(client, user_factory):
    """
    This test checks the account details endpoint.
    """
    url = reverse('backend:account-details')
    user = user_factory()
    response = client.post(path=url, data=new_user)
    assert response.status_code == 403
    assert response.json()['status'] is False
    assert response.json()['error'] == 'Not authenticated'

    client.force_authenticate(user=user)
    response = client.get(path=url)
    assert response.status_code in (200, 201)

    create_user = client.post(path=url, data=new_user)
    assert create_user.status_code in (200, 201)
    assert create_user.json()['status'] is True


@pytest.mark.django_db
def test_contacts_create(client, user_factory):
    """
    This test checks the creation of user contacts.
    """
    url = reverse('backend:user-contact')
    user = user_factory()
    client.force_authenticate(user=user)
    contacts = {
        'city': 'Norilsk',
        'street': 'Talnahskaya',
        'house': '1',
        'frame': '1',
        'apartment': '1',
        'phone': '88005553535'
    }
    response = client.post(path=url, data=contacts)
    assert response.status_code in (200, 201)
    assert response.json()['status'] is True
    assert response.json()['message'] == 'contacts created'
    data = client.get(path=url)
    assert data.json()[0]['city'] == 'Norilsk'
