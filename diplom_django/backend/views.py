from distutils.util import strtobool
from django.contrib.auth import authenticate
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from ujson import loads
from yaml import load as yaml_load, Loader
from requests import get
from rest_framework import status
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
import psycopg2
from django.views.decorators.http import require_http_methods

from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact, \
    ConfirmEmailToken
from .serializers import UserSerializer, CategorySerializer, ProductInfoSerializer, OrderSerializer, \
    OrderItemSerializer, ContactSerializer, ShopSerializer
from .signals import new_order, new_user_registered


class RegisterAccountView(APIView):
    """
    View for register a new user account.
    """

    def post(self, request, *args, **kwargs):
        """
        Register a new user.

        Parameters:
            request (HttpRequest): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: A JSON response object.

        Raises:
            ValidationError: If the password validation fails.
        """
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position', 'type'} <= set(request.data):
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                errors_list = []
                for error in password_error:
                    errors_list.append(error)
                return JsonResponse({'status': False, 'error': errors_list})
            else:
                if request.data['type'].lower() != 'shop' and request.data['type'].lower() != 'buyer':
                    return JsonResponse({'status': False, 'error': 'Invalid type'})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    return JsonResponse({'status': True, 'your token for confirm email': token.key})
                else:
                    return JsonResponse({'status': False, 'error': user_serializer.errors})

        return JsonResponse({'status': False, 'error': 'Invalid arguments'})


class ConfirmEmailView(APIView):
    """
    View for confirm the user's email address.
    """

    def post(self, request, *args, **kwargs):
        """
        Confirm the user's email address.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: A JSON response containing a status indicator and an optional error message.

        Raises:
            ValidationError: If the provided token or email is invalid.
        """
        if {'email', 'token'} <= set(request.data):
            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'status': True, 'message': 'Your status now is_active'})
            else:
                return JsonResponse({'status': False, 'error': 'Invalid token or email'})
        return JsonResponse({'status': False, 'error': 'Invalid arguments'})


class AccountDetailsView(APIView):
    """
    View for getting and updating user details.
    """

    def get(self, request, *args, **kwargs):
        """
        Retrieves the current user's details.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: An HTTP response containing the user's details serialized as JSON.

        Raises:
            Http403Forbidden: If the user is not authenticated.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Updates the current user's details.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: An HTTP response containing the updated user's details serialized as JSON.

        Raises:
            Http403Forbidden: If the user is not authenticated.
            JsonResponse: If the provided password does not meet the validation criteria.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        if {'password'} <= set(request.data):
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                errors_list = []
                for error in password_error:
                    errors_list.append(error)
                return JsonResponse({'status': False, 'error': errors_list})
            else:
                request.user.set_password(request.data['password'])

        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse(
                {'status': True, 'message': 'user with id: {}, details updated'.format(request.user.id)})
        else:
            return JsonResponse({'status': False, 'error': user_serializer.errors})


class LoginAccountView(APIView):
    """
    View for logging in a user account.
    """

    def post(self, request, *args, **kwargs):
        """
        Authenticate a user.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: A JSON response containing a token if the registration is successful,
            otherwise an error message.

        Raises:
            ValidationError: If the password does not meet the specified criteria.
        """
        if {'email', 'password'} <= set(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse({'status': True, 'your token, save it': token.key})
                return JsonResponse({'status': False, 'error': 'Account is not active'})
        return JsonResponse({'status': False, 'error': 'invalid arguments'})


class CategoryView(ListAPIView):
    """
    View for listing categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    View for listing shops.
    """
    queryset = Shop.objects.filter(status=True)
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    """
    View for getting product information.
    """

    def get(self, request, *args, **kwargs):
        """
        Get product information.

        This method retrieves product information based on the provided query parameters.
        It filters the product information based on the 'shop_id' and 'category_id' query parameters.

        Args:
            request (HttpRequest): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: An HTTP response containing a JSON representation of the product information.

        Raises:
            ValidationError: If the provided query parameters are invalid.
        """
        query = Q(shop__status=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        queryset = ProductInfo.objects.filter(query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BasketView(APIView):
    """
    View for managing the user's basket.
    """

    def get(self, request, *args, **kwargs):
        """
        Retrieves the user's basket.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: An HTTP response containing the user's basket fixture serialized as JSON.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        basket = Order.objects.filter(user_id=request.user.id, status='basket').prefetch_related(
            'order_items__product_info__product__category',
            'order_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('order_items__quantity') * F('order_items__product_info__price'))).distinct()
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Adds items in the user's basket.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: An HTTP JSON response containing the status of the operation.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
            IntegrityError: If there is a problem with the integrity of the fixture.
            ValueError: If the request format is invalid.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        items_string = request.data.get('items')
        if items_string:
            try:
                items_dict = loads(items_string)
            except ValueError as e:
                return JsonResponse({'status': False, 'error': f'Invalid request format: {e}'}, status=400)
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as e:
                            return JsonResponse({'status': False, 'error': str(e)})
                        else:
                            objects_created += 1
                    else:
                        JsonResponse({'status': False, 'error': serializer.errors})
                return JsonResponse({'status': True, 'Objects_created': objects_created})
        return JsonResponse({'status': False, 'error': 'Invalid arguments'}, status=400)

    def delete(self, request, *args, **kwargs):
        """
        Removes items from the user's basket.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: An HTTP JSON response containing the status of the operation and the number of items deleted.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
            IntegrityError: If there is a problem with the integrity of the fixture.
            ValueError: If the request format is invalid.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        items = request.data.get('items')
        if items:
            items_list = items.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'status': True, 'deleted_count': deleted_count}, status=200)
        return JsonResponse({'status': False, 'error': 'Invalid arguments'}, status=400)

    def put(self, request, *args, **kwargs):
        """
        Updates the quantity of items in the user's basket.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: An HTTP JSON response containing the status of the operation.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
            IntegrityError: If there is a problem with the integrity of the fixture.
            ValueError: If the request format is invalid.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        items_string = request.data.get('items')
        if items_string:
            try:
                items_dict = loads(items_string)
            except ValueError as e:
                return JsonResponse({'status': False, 'error': f'Invalid request format: {e}'}, status=400)
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if isinstance(order_item['id'], int) and isinstance(order_item['quantity'], int):
                        objects_updated += OrderItem.objects.filter(order_id=basket.id,
                                                                    id=order_item['id']).update(
                            quantity=order_item['quantity'])
                return JsonResponse({'status': True, 'objects_updated': objects_updated})
        return JsonResponse({'status': False, 'error': 'Invalid arguments'}, status=400)


class PartnerUpdateView(APIView):
    """
    This view is responsible for updating the partner's fixture.
    """

    def post(self, request, *args, **kwargs):
        """
        This method handles the POST request for updating the partner's fixture.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: A JSON response containing the status of the operation.

        Raises:
            ValidationError: If the URL provided in the request is not valid.
            IntegrityError: If there is a problem with the integrity of the fixture.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'status': False, 'error': 'Only for shops'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'status': False, 'error': str(e)}, status=400)
            else:
                stream = get(url).content
                data = yaml_load(stream, Loader=Loader)
                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)
                return JsonResponse({'status': True})
        return JsonResponse({'status': False, 'error': 'Invalid arguments'})


class PartnerStatusView(APIView):
    """
    This view for managing partner state.
    """

    def get(self, request, *args, **kwargs):
        """
        This method handles the GET request for fetching the partner's status.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: A JSON response containing the shop's fixture.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
            InvalidUserType: If the user is not a shop.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'status': False, 'error': 'Only for shops'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        This method handles the POST request for updating the partner's status.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: A JSON response containing the status update result.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
            InvalidUserType: If the user is not a shop.
            ValueError: If the status parameter is not a valid boolean value.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'status': False, 'error': 'Only for shops'}, status=403)

        status = request.data.get('status')
        if status:
            try:
                Shop.objects.filter(user_id=request.user.id).update(status=strtobool(status))
                return JsonResponse({'status': True}, status=200)
            except ValueError as e:
                return JsonResponse({'status': False, 'error': str(e)}, status=400)
        return JsonResponse({'status': False, 'error': 'Invalid arguments'})


class PartnerOrdersView(APIView):
    """
    This view is responsible for fetching the partner's orders.
    """

    def get(self, request, *args, **kwargs):
        """
        This method handles the GET request for fetching the partner's orders.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: A JSON response containing the partner's orders.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
            InvalidUserType: If the user is not a shop.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'status': False, 'error': 'Only for shops'}, status=403)

        order = Order.objects.filter(order_items__product_info__shop__user_id=request.user.id).exclude(
            status='basket').prefetch_related(
            'order_items__product_info__product__category',
            'order_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('order_items__quantity') * F('order_items__product_info__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data, status=200)


class ContactView(APIView):
    """
    This view is responsible for managing the user's contact information.
    """

    def get(self, request, *args, **kwargs):
        """
        This method handles the GET request for retrieving the user's contact information.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A JSON response containing the user's contact information.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data, status=200)

    def post(self, request, *args, **kwargs):
        """
        This method handles the POST request for creating a new contact for the user.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A JSON response containing the user's contact information.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        if {'city', 'street', 'phone'} <= set(request.data):
            request.POST._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'status': True, 'message': 'contacts created'})
            else:
                return JsonResponse({'status': False, 'error': serializer.errors})
        return JsonResponse({'status': False, 'error': 'Invalid arguments'}, status=400)

    def delete(self, request, *args, **kwargs):
        """
        This method handles the DELETE request for deleting a contact for the user.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A JSON response containing the user's contact information.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        items = request.data.get('items')
        if items:
            items_list = items.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'status': True, 'deleted_count': deleted_count}, status=200)
        return JsonResponse({'status': False, 'error': 'Invalid arguments'})

    def put(self, request, *args, **kwargs):
        """
        This method handles the PUT request for updating a contact for the user.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A JSON response containing the user's contact information.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        if {'id'} <= set(request.data) and request.data['id'].isdigit():
            contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
            if contact:
                serializer = ContactSerializer(contact, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({'status': True, 'message': 'your contacts have been updated'})
                else:
                    return JsonResponse({'status': False, 'error': serializer.errors})
        return JsonResponse({'status': False, 'error': 'Invalid arguments'})


class OrderView(APIView):
    """
    This view is responsible for managing the user's orders.
    """

    def get(self, request, *args, **kwargs):
        """
        This method handles the GET request for retrieving the user's orders.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A JSON response containing the user's orders.

        Raises:
            AuthenticationFailed: If the user is not authenticated.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        order = Order.objects.filter(user_id=request.user.id).exclude(status='basket').prefetch_related(
            'order_items__product_info__product__category',
            'order_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('order_items__quantity') * F('order_items__product_info__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        This method handles the POST request for updating the user's order.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A JSON response containing the user's contact information.

        Raises:
            AuthenticationFailed: If the user is not authenticated.

        """
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Not authenticated'}, status=403)

        if {'id', 'contact'} <= set(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'], status='new')
                except IntegrityError as e:
                    return JsonResponse({'status': False, 'error': str(e)}, status=400)
                else:
                    if is_updated:
                        new_order.send(sender=self.__class__, user_id=request.user.id)
                        return JsonResponse({'status': True})
                    else:
                        return JsonResponse({'status': False, 'error': 'Order not updated'}, status=400)
        return JsonResponse({'status': False, 'error': 'Invalid arguments'})


def truncate_table(table_name):
    '''Function for deleting data from a table and resetting the identifier.'''
    with psycopg2.connect(database='diplom_db', user='postgres', password='postgres') as conn:
        with conn.cursor() as cur:
            cur.execute('''TRUNCATE TABLE {} CASCADE;'''.format(table_name))
            cur.execute('''ALTER SEQUENCE {}_id_seq RESTART WITH 1;'''.format(table_name))
            conn.commit()


@require_http_methods('GET')
def upload_goods(request):
    '''Function for loading ready data into a table. When called again, the data is reset.'''
    ulr_for_upload = 'https://raw.githubusercontent.com/netology-code/python-final-diplom/master/data/shop1.yaml'
    stream = get(ulr_for_upload).content
    data = yaml_load(stream, Loader=Loader)
    shop, _ = Shop.objects.get_or_create(name=data['shop'])
    for category in data['categories']:
        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
        category_object.shops.add(shop.id)
        category_object.save()
    product = Product.objects.all()
    if product:
        truncate_table('backend_productinfo')
        truncate_table('backend_product')
        truncate_table('backend_shop')
        truncate_table('backend_category')
        truncate_table('backend_category_shops')
        truncate_table('backend_parameter')
        truncate_table('backend_productparameter')
        return JsonResponse(
            {'status': 'The data was already in the table, the data was deleted, make a new query to load the data.'})
    for item in data['goods']:
        product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
        product_info, _ = ProductInfo.objects.get_or_create(product_id=product.id,
                                                            external_id=item['id'],
                                                            model=item['model'],
                                                            price=item['price'],
                                                            price_rrc=item['price_rrc'],
                                                            quantity=item['quantity'],
                                                            shop_id=shop.id)
        for name, value in item['parameters'].items():
            parameter_object, _ = Parameter.objects.get_or_create(name=name)
            ProductParameter.objects.get_or_create(product_info_id=product_info.id,
                                                   parameter_id=parameter_object.id,
                                                   value=value)
    return JsonResponse({'status': 'products have been uploaded to the database'})
