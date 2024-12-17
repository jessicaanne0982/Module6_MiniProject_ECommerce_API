# E-Commerce API Project
 
The E-Commerce API Project is a Python application that demonstrates the ability to create CRUD (Create, Read, Update, Delete) endpoints for managing customers, customer accounts, products, and orders within a MySQL Database.

Future development of this application will include the ability to view and manage stock levels and improved order processing capabilties, including the option to manage order history and the option to cancel orders that have not yet been processed and shipped.
 
## Installation
 
To run this application, use the package manager [pip](https://pip.pypa.io/en/stable/) to install flask, sqlalchemy, flask-sqlalchemy, flask-marshmallow, and mysql-connector-python.
 
```bash
pip install flask sqlalchemy flask-sqlalchemy flask-marshmallow mysql-connector-python
```
Test Endpoints using [Postman](https://www.postman.com/)
 
## Usage
 
```python
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, validate
from marshmallow import ValidationError
```
Using Postman to interact with the Python application and the MySQL database, the user is able to create new customers, capturing essential information including the customer's name, email, and phone number.  Providing the customer's ID number allows the user to retrieve all information about a particular customer as well as the ability to update that information. The user is also able to delete a customer based on his or her ID.  Another set of endpoints allows the user to create, read, update, and delete Customer Account information.  These customer accounts are linked to specific customers and manage crucial information, including account username and password.  The set of product endpoints provides the user the ability to add new products to the database, capturing the item name, price, and quantity, view all products in the database, update necessary information, and even delete products when no longer needed.  Finally, these three tables are linked together when the user is able to create a new order, capturing the customer ID, the date, and the product information.  Providing the order ID also allows the user to retrieve all information linked to that order.
 
## GitHub Link
 
[Module6_MiniProject_ECommerce_API](https://github.com/jessicaanne0982/Module6_MiniProject_ECommerce_API)