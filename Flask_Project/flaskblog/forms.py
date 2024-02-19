from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from sqlalchemy.exc import ProgrammingError, OperationalError
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DecimalField, \
    HiddenField, SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from flaskblog.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    address = StringField('Address',
                          validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('User Type', choices=[('customer', 'Customer'), ('restaurant owner', 'Restaurant Owner')], validators=[DataRequired()])
    food_type = SelectField('Food Type', choices=[('italian', 'Italian'), ('mexican', 'Mexican'), ('chinese', 'Chinese'), ('vegetarian', 'Vegetarian')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        try:
            user = User.query.filter_by(username=username.data).first()
        except OperationalError:
            user = None
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        try:
            user = User.query.filter_by(email=email.data).first()
        except OperationalError:
            user = None
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    address = StringField('Address',
                          validators=[DataRequired(), Length(min=2, max=20)])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')


class DishForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[DataRequired()])
    cost = DecimalField('Cost', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Dish')


class OrderForm(FlaskForm):
    restaurant_id = HiddenField('Restaurant ID', validators=[DataRequired()])
    submit = SubmitField('Place Order')


class OrderDishForm(FlaskForm):
    dish_id = IntegerField('Dish ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add to cart')
