from datetime import datetime
from flaskblog import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(20), unique=False, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    user_type = db.Column(db.String(10), nullable=False, default='customer')
    food_type = db.Column(db.String(50), nullable=True)  # Type of food

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Float, nullable=False)

    restaurant_owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_owner = db.relationship('User', backref=db.backref('dishes', lazy=True))

    def __repr__(self):
        return f"Food('{self.name}', '{self.description}', '{self.cost}')"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.String(50), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='open')  # open, wait, approved, disapproved

    def __repr__(self):
        return f"Food('{self.id}', '{self.status}')"


class OrderDish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    quantity = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dish = db.relationship('Dish', backref=db.backref('order_dishes', lazy=True))
    order = db.relationship('Order', backref=db.backref('order_dishes', lazy=True))
    status = db.Column(db.String(50), nullable=False, default='open')  # open, wait, approved, disapproved

    def __repr__(self):
        return f"OrderDish('{self.dish_id}', '{self.order_id}', '{self.quantity}')"

    def increase_quantity(self, quantity):
        self.quantity += quantity