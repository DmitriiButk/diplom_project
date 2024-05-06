# ***Diploma project for the profession Python developer “API Service for ordering goods.”***

# *Description*:

*The application is designed to automate purchases in a retail network. Users of the service are the buyer (a retail
chain manager who purchases goods for sale in the store) and the supplier of goods.*

Client(buyer):

* An API purchasing manager makes daily purchases from a catalog that contains products from several suppliers.
* You can specify goods from different suppliers in one order - this will affect the delivery cost.
* The user can log in, register and recover the password via the API.

Provider(shop):

* Informs the service about the price list update via API.
* Can enable or disable order acceptance.
* Can receive a list of placed orders (with goods from its price list).

#

*Here's what you need to start the project:*

```shell
git clone https://github.com/DmitriiButk/diplom_project.git
```

```shell
cd diplom_project\diplom_django
```

```shell
pip install -r requirements.txt
```

```shell
createdb -U postgres diplom_db
````

```shell
python manage.py makemigrations
```

```shell
python manage.py migrate
```

```shell
python manage.py runserver
```

*Run tests:*
```shell
pytest
```
----------------------------------------------------------------
*[Use the API documentation](https://documenter.getpostman.com/view/31517712/2sA3JFCQpU#97c8475a-301c-4f85-bffa-4446b2619179)*
----------------------------------------------------------------
*You need to create 2 users of different types (buyer and shop) to fully manage the API.*

*User:*
* *We register a new user with the required fields, and also be sure to indicate the user type (buyer or shop), remember the token to confirm your email*
* *Confirm your email and change the status to is_active.*
* *The next step is login*
* *Creating user contacts*
* *You can get, change, delete contacts. You can also obtain complete information about the user or change user information.*
* *You can also reset your password*

*Shop:*
* *You can get a list of shops and products. Also look for different products with different categories.*
* *Manage your shopping basket. Add, change quantity, delete products. To place an order. View orders.*

*Partner:*
* *You can change the partner status, find out information about the order, and also update the price list.*
* *To upload ready-made product data, in the partner tab using the POST method and use the seller token. Here is the link https://raw.githubusercontent.com/netology-code/python-final-diplom/master/data/shop1.yaml*
----------------------------------------------------------------
*The API documentation has all the information and all the required fields to fill out.*
----------------------------------------------------------------
*The project was written in python 3.11*




