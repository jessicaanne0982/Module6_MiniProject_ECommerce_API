from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, validate
from marshmallow import ValidationError
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:my_password@localhost/e_com_api_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ('name', 'email', 'phone')

class ProductSchema(ma.Schema):
    name = fields.String(required=True)
    price = fields.Float(required=True)

    class Meta:
        fields = ('name', 'price', 'id')

class CustomerAccountSchema(ma.Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)
    
    class Meta:
        fields = ('username', 'password')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

customer_account_schema = CustomerAccountSchema()
customer_accounts_schema = CustomerSchema(many=True)

class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))
    # Create a One-to-Many Relationship
    orders = db.relationship('Order', backref = 'customer')

class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    # Create a one-to-one relationship
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

# Association Table for many-to-many relationship between Orders and Products
order_product = db.Table('Order_Product', 
        db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True), 
        db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True),
        db.Column('quantity', db.Integer, nullable=False, default=1)
        )

class Order(db.Model):
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    products = db.relationship('Product', secondary=order_product, backref=db.backref('orders'))

class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    # orders = db.relationship('Order', secondary=order_product, backref=db.backref('products'))

# END POINTS FOR CUSTOMER
# View all Customers (For testing purposes)
@app.route('/customers', methods=['GET'])
def get_customers():
   customers = Customer.query.all()
   return customers_schema.jsonify(customers)


# Create Customer Route (POST)
@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_customer = Customer(name=customer_data['name'],
                            email=customer_data['email'],
                            phone=customer_data['phone']
                            )
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message':'New customer successfully added'})

# Read Specific Customer Route (GET) - by-id
# retrieve by unique id
@app.route('/customers/by-id', methods=['GET'])
def query_customer_by_id():
    id = request.args.get('id')
    customer = Customer.query.filter_by(id=id).first()
    if customer:
        return customer_schema.jsonify(customer)
    else:
        return jsonify({'message':'Customer not found'}), 404
    
# Update Customer - PUT
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
  customer = Customer.query.get_or_404(id)
  try:
    customer_data = customer_schema.load(request.json)
  except ValidationError as e:
    return jsonify(e.messages), 400
 
  customer.name = customer_data['name']
  customer.email = customer_data['email']
  customer.phone = customer_data['phone']
 
  db.session.commit()
  return jsonify({'messages': 'Customer information has successfully been updated'}), 200
 
 # Delete Customer - DELETE
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message':'Customer has successfully been removed'})
   
    
# Create new customer_account - POST - Tie customer to customer account by customer id
@app.route('/customer_accounts/<int:id>', methods=['POST'])
def new_customer_account(id):
  customer = Customer.query.get_or_404(id)
  try:
    customer_account_data = customer_account_schema.load(request.json)
  except ValidationError as e:
    return jsonify(e.messages), 400
   
  new_customer_account = CustomerAccount(username=customer_account_data['username'],
                                         password=customer_account_data['password'],
                                         customer_id=customer.id)
  
  db.session.add(new_customer_account)
  db.session.commit()
  return jsonify({'message':'New customer account successfully added'})

# Retrieve customer account information as well as linked customer information - GET 
@app.route('/customer_accounts/by-username', methods=['GET'])
def query_customer_account_by_username():
  username = request.args.get('username')
    
  customer_account = CustomerAccount.query.filter_by(username=username).first()
  if not customer_account:
    return jsonify({'error': 'Customer Account not found'}), 404
    
  customer = Customer.query.filter_by(id = customer_account.customer_id).first()
  if not customer:
    return jsonify({'error':'Customer not found'}), 404
    
  display_data = {
      'customer_account': customer_account_schema.dump(customer_account),
      'customer': customer_schema.dump(customer)}
 
  return jsonify(display_data)
   
# Update Customer Account by-username - PUT
@app.route('/customer_accounts/by-username', methods=['PUT'])
def update_customer_account_by_username():
    username = request.args.get('username')

    if not username:
        return jsonify({"message": "Username is required"}), 400
        
    customer_account = CustomerAccount.query.filter_by(username=username).first()
 
    if not customer_account:
        return jsonify({"message": "Customer Account not found"}), 404

    try:
        account_data = customer_account_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
 
    customer_account.username = account_data['username']
    customer_account.password = account_data['password']
 
    db.session.commit()
    return jsonify({'message':'Customer account details have been successfully updated'}), 200

# Delete a Customer Account - Delete - Uses Customer Account id as id, NOT Customer id
@app.route('/customer_accounts/<int:id>', methods=['DELETE'])
def delete_customer_account(id):
  customer_account = CustomerAccount.query.get_or_404(id)
  db.session.delete(customer_account)
  db.session.commit()
  return jsonify({'message':'Customer account successfully deleted'})  

# Endpoints for Products
# Add a new product - POST
@app.route('/products', methods=['POST'])
def add_new_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
   
    new_product = Product(name=product_data['name'], price=product_data['price'])

    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message':'New product successfully added'}), 201

# List all products in the platform - GET 
@app.route('/products', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

# Update a Product - PUT
@app.route('/products/<int:id>', methods=['PUT']) 
def update_product(id):
  product = Product.query.get_or_404(id)
 
  try:
    product_data = product_schema.load(request.json)
  except ValidationError as e:
    return jsonify(e.messages), 400
   
  product.name = product_data['name']
  product.price = product_data['price']
 
  db.session.commit()
  return jsonify({'message':'Product has been successfully updated'}), 200

# Delete a product - Delete
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
  product = Product.query.get_or_404(id)
  db.session.delete(product)
  db.session.commit()
  return jsonify({'message':'Product has successfully been deleted'}), 200

# Get specific product details - GET
@app.route('/products/by-id', methods=['GET'])
def specific_product_details():
  id = request.args.get('id')
  product = Product.query.filter_by(id=id).first()
  if product:
    return product_schema.jsonify(product)
  else:
    return jsonify({'message':'Product not found'}), 404

#########################################################################################
"""
I'm lost right here.  I've been able to create all the other endpoints, but I can't seem
to figure out how to tie the tables together to create a new order.  I'm attempting to
access the customer id and the products and then check to make sure the customer is
actually a customer.  Then I create the variable for the new order and try to add products
to the order. Finally I attempt to add the new order to the order_products association
table I created above.  I keep getting error after error...  Run as is, I receive an
Internal Server Error, 500 stating 'Table' object is not callable'
"""
# Place new order - POST 
@app.route('/orders', methods=['POST'])
def place_order():
  data = request.get_json()
  customer_id = data.get('customer_id')
  products = data.get('products')
 
  customer = Customer.query.get(customer_id)
  if not customer:
    return jsonify({"message": "Customer not found"}), 404
  
  new_order = Order(customer_id=customer_id, date=datetime.now())
 
  for item in products:
    product_id = item.get('product_id')
    quantity = item.get('quantity', 1)
    product = Product.query.get(product_id)
    if not product:
      return jsonify({"message": f"Product {product_id} not found"}), 404
    
    #Add the products to the order
    order_product_instance = order_product(order=new_order, product=product, quantity=quantity)
    db.session.add(order_product_instance)
  
  # Add the new order to the table
  db.session.add(new_order)
  db.session.commit()
 
  return jsonify({'message':'Order placed successfully'}), 201

#########################################################################################

# Retrieve order details by order id - GET
# @app.route('/orders/by-id', method=['GET'])
# def retrieve_order_details_by_id():
#   id = request.args.get('id')
#   order = Order.query.filter_by(id=id).first()
 
#   if order:
#     return order.schema.jsonify(order) # Should return order date and products
#   else:
#     return jsonify({'message':'Order not found'}), 404
  
  
#Initialize the database and create tables
with app.app_context():
  db.create_all()
 
if __name__ == '__main__':
  app.run(debug=True)