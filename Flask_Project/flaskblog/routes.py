import os
import secrets
from datetime import datetime

from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, DishForm, OrderForm, OrderDishForm
from flaskblog.models import User, Post, Dish, Order, OrderDish
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    db.create_all()
    try:
        posts = Post.query.get_or_404.all()
    except:
        posts = []
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    db.create_all()
    if current_user and current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, address=form.address.data, password=hashed_password, user_type=form.user_type.data, food_type=form.food_type.data)
        db.session.add(user)
        db.create_all()
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.address = form.address.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.address.data = current_user.address
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')

@app.route("/create-order", methods=['GET', 'POST'])
@login_required
def create_order():
    restaurants = User.query.filter_by(user_type='restaurant owner').all()
    return render_template('create_order.html', restaurants=restaurants)


@app.route('/restaurant/<int:restaurant_id>/dishes', methods=['GET', 'POST'])
def restaurant_dishes(restaurant_id):
    restaurant = User.query.get_or_404(restaurant_id)
    dishes = Dish.query.filter_by(restaurant_owner_id=restaurant_id).all()
    order_dish_form = OrderDishForm()
    if order_dish_form.validate_on_submit():
        existed_order_dish = OrderDish.query.filter_by(customer_id=current_user.id,
                                  dish_id=order_dish_form.dish_id.data,
                                  status='open').first()
        if existed_order_dish:
            existed_order_dish.increase_quantity(order_dish_form.quantity.data)
        else:
            order_dish = OrderDish(
                dish_id=order_dish_form.dish_id.data,
                quantity=order_dish_form.quantity.data,
                customer_id=current_user.id,
                status='open'
            )
            db.session.add(order_dish)
        db.session.commit()
    order_dishes = OrderDish.query.filter_by(customer_id=current_user.id, status='open').all()
    return render_template('restaurant_dishes.html', restaurant=restaurant, dishes=dishes, order_dishes=order_dishes, order_dish_form=order_dish_form)

@app.route('/order_all', methods=['POST'])
def order_all():
    # Assuming you have a current_user variable available for the logged-in user
    if not current_user.is_authenticated:
        return redirect(url_for('register'))
    order_dishes = OrderDish.query.filter_by(customer_id=current_user.id, status='open').all()
    if order_dishes:
        # Create a new order for all items in the cart
        order = Order(restaurant_id=order_dishes[0].dish.restaurant_owner_id, customer_id=current_user.id, created_at=datetime.utcnow(), status='waiting')
        db.session.add(order)
        db.session.commit()

        # Add ordered dishes to the order
        for order_dish in order_dishes:
            order_dish.order_id = order.id
            order_dish.status = 'waiting'
            db.session.add(order_dish)

    db.session.commit()
    return redirect(url_for('home'))


@app.route("/dishes", methods=['GET', 'POST'])
@login_required
def get_dishes():
    dishes = Dish.query.filter_by(restaurant_owner_id=current_user.id).all()
    form = DishForm()
    return render_template('dishes.html', dishes=dishes, form=form)

@app.route("/admin/orders", methods=['GET', 'POST'])
@login_required
def get_orders_admin():
    orders = Order.query.filter_by(restaurant_id=current_user.id).all()
    order_details = []
    for order in orders:
        order_dishes = OrderDish.query.filter_by(order_id=order.id).all()
        total_cost = sum(order_dish.dish.cost * order_dish.quantity for order_dish in order.order_dishes)
        order_details.append({'order': order, 'dishes': order_dishes, 'total_cost': total_cost})
    return render_template('orders_admin.html', order_details=order_details)

@app.route('/approve_order/<int:order_id>', methods=['POST'])
def approve_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status == 'waiting':
        order.status = 'approved'
        db.session.commit()
        flash('Order approved successfully!', 'success')
    return redirect(url_for('get_orders_admin'))

@app.route('/disapprove_order/<int:order_id>', methods=['POST'])
def disapprove_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status == 'waiting':
        order.status = 'disapproved'
        db.session.commit()
        flash('Order disapproved successfully!', 'success')
    return redirect(url_for('get_orders_admin'))

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/add_dish", methods=['POST'])
def add_dish():

    existing_dish = Dish.query.filter_by(name=request.form.get('name'), restaurant_owner_id=current_user.id).first()
    if not existing_dish:
        dish = Dish(name=request.form.get('name'), description=request.form.get('description'),
                    cost=request.form.get('cost'), restaurant_owner_id=current_user.id)
        db.session.add(dish)
        db.session.commit()
        flash('Dish added successfully!', 'success')
    else:
        flash('Dish existed already!', 'danger')
    return redirect(url_for('get_dishes'))

@app.route("/remove_dish/<int:dish_id>", methods=['POST'])
def remove_dish(dish_id):
    restaurant_owner_dish = Dish.query.filter_by(id=dish_id, restaurant_owner_id=current_user.id).first()
    if restaurant_owner_dish:
        db.session.delete(restaurant_owner_dish)
        db.session.commit()
        flash('Dish removed successfully!', 'success')
    else:
        flash('Dish not found!', 'danger')
    return redirect(url_for('get_dishes'))

@app.route('/update_dish/<int:dish_id>', methods=['POST'])
def update_dish(dish_id):
    dish = Dish.query.get_or_404(dish_id)  # Assuming you have a Dish model
    if not dish:  # Check if the current user is the owner of the dish
        flash('Error updating dish. Please check the form.', 'danger')

    form = DishForm(request.form)
    existed_dish_same_name = Dish.query.filter_by(name=form.name.data, restaurant_owner_id=current_user.id).first()
    if existed_dish_same_name and existed_dish_same_name.id != dish_id:
        flash('Dish name already exist.', 'danger')
    else:
        dish.name = form.name.data
        dish.description = form.description.data
        dish.cost = form.cost.data
        db.session.commit()
        flash('Dish updated successfully!', 'success')

    return redirect(url_for('get_dishes'))

@app.route('/orders')
def orders():
    orders = Order.query.filter_by(customer_id=current_user.id).all()
    order_details = []
    for order in orders:
        order_dishes = OrderDish.query.filter_by(order_id=order.id).all()
        order_details.append({'order': order, 'dishes': order_dishes})
    return render_template('orders.html', order_details=order_details)
