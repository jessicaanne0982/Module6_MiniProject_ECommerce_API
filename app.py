from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from marshmallow import fields, validate
from marshmallow import ValidationError
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Braxton0630!@localhost/e_com_api_db'

db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)

class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ('name', 'email', 'phone', 'id')

class ProductSchema(ma.Schema):
    name = fields.String(required=True)
    price = fields.Float(required=True)
    quantity = fields.Integer(required=True)

    class Meta:
        fields = ('name', 'price', 'quantity', 'id')

class CustomerAccountSchema(ma.Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)
    
    class Meta:
        fields = ('username', 'password')

class OrderSchema(ma.Schema):
    id = fields.Integer()
    date = fields.Date()
    customer_id = fields.Integer()

    products = fields.List(fields.Integer())  

    class Meta:
        fields = ('id', 'date', 'customer_id', 'products')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

customer_account_schema = CustomerAccountSchema()
customer_accounts_schema = CustomerSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

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
    quantity = db.Column(db.Integer, nullable=False)

# END POINTS FOR CUSTOMER REQUESTS
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
    return jsonify({'message':'New customer successfully added'}), 201

# Read Specific Customer Route (GET) - by-id
# retrieve by unique id
@app.route('/customers/<int:id>', methods=['GET'])
def get_customer_by_id(id):
    query = select(Customer).filter(Customer.id == id)
    customer = db.session.execute(query).scalars().first()

    if customer: 
        return customer_schema.jsonify(customer)
    else:
        return jsonify({"message": "Customer not found"}), 404
    
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
    return jsonify({'message':'Customer has successfully been removed'}), 200
   

# END POINTS FOR CUSTOMER ACCOUNT REQUESTS    
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

# END POINTS FOR PRODUCT REQUESTS
# Add a new product - POST
@app.route('/products', methods=['POST'])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
   
    new_product = Product(name=product_data['name'], price=product_data['price'], quantity=product_data['quantity'])

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
def update_products(id):
  product = Product.query.get_or_404(id)
  try:
    product_data = product_schema.load(request.json)
  except ValidationError as e:
    return jsonify(e.messages), 400
   
  product.name = product_data['name']
  product.price = product_data['price']
  product.quantity = product_data['quantity']
 
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
@app.route('/products/<int:id>', methods=['GET'])
def get_product_by_id(id):
  query = select(Product).filter(Product.id == id)
  product = db.session.execute(query).scalars().first()

  if product:
    return product_schema.jsonify(product)
  else:
    return jsonify({'message':'Product not found'}), 404

# END POINTS FOR ORDER REQUESTS
# View all orders - GET
@app.route('/orders', methods=['GET'])
def get_all_orders():
  orders = Order.query.all()

  response = []

  for order in orders:
    try:
       
      order_data = order_schema.dump(order)
      customer = Customer.query.get(order.customer_id)

      if customer:
        order_data['customer_name'] = customer.name
      else:
        order_data['customer_name'] = 'Unknown'

      products_info = []
      for order_product in order.products:
        product_info = {
            'product_id': order_product.id,
            'product_name': order_product.name,
            'quantity': order_product.quantity
        }
        products_info.append(product_info)

      order_data['products'] = products_info
      response.append(order_data)
    except Exception as e:
       print(f"Error processing order {order.id}: {str(e)}")
       continue

  return jsonify(response)

# Place new order - POST 
@app.route('/orders', methods=['POST'])
def place_order():
  data = request.get_json()
  print("Received data:", data) # DELETE AFTER DEBUGGING
  customer_id = data.get('customer_id')
  products = data.get('products')
 
  customer = Customer.query.get(customer_id)
  if not customer:
    return jsonify({"message": "Customer not found"}), 404
  
  new_order = Order(customer_id=customer_id, date=datetime.now())
  db.session.add(new_order)
  db.session.commit()
 
  for item in products:
    product_id = item.get('product_id')
    quantity = item.get('quantity', 1)

    product = Product.query.get(product_id)
    if not product:
      return jsonify({"message": f"Product {product_id} not found"}), 404
    
    new_order.products.append(product)
    order_product_entry = order_product.insert().values(order_id=new_order.id, product_id=product.id, quantity=quantity)
    db.session.execute(order_product_entry)
    
  db.session.commit()

  return jsonify({
                  'Order ID': new_order.id,
                  'Date': new_order.date,
                  'Customer ID': new_order.customer_id,
                  'Products': [{'product_id': product.id,
                                'product_name': product.name,
                                'quantity': item.get('quantity')}]
    }), 201

# Retrieve order details by order id - GET
@app.route('/orders/<int:id>', methods=['GET'])
def retrieve_order_details_by_id(id):
  order = Order.query.filter_by(id)
 
  if order:
     return order_schema.jsonify(order), 200 
  else:
    return jsonify({'message':'Order not found'}), 404
  
#Initialize the database and create tables
with app.app_context():
  db.create_all()
  # db.drop_all() # Used to clear tables during testing
 
if __name__ == '__main__':
  app.run(debug=True)