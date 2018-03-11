import functools

import jwt
from flask import jsonify, request

from blueprints import app
from blueprints.models import Post, User


def error(msg: str, code: int):
    return jsonify({'error': msg.capitalize()}), code


def message(msg: str, code: int):
    return jsonify({'message': msg}), code


def token_required(admin_required=False, return_user=True):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            token = request.headers.get('x-access-token')
            if token is None:
                return error('Token is missing.', 401)
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            except jwt.InvalidTokenError:
                return error('Token is invalid.', 401)
            user = User.get_by_id(data['id'])
            if admin_required and not user.is_admin:
                return error('Admin rights required to perform this action.', 401)
            if return_user:
                return func(user, *args, **kwargs)
            return func(*args, **kwargs)
        return inner
    return decorator


def data_required(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        if not request.get_json():
            return error('Json-data was not provided.', 403)
        return func(*args, **kwargs)
    return inner


def create_user(data, admin=False):
    fields = User._meta.allowed_fields
    if any(field not in data or data.get(field) is None for field in fields):
        return error('Must include {}, {} and {} fields.'.format(*fields), 403)
    if 'is_admin' in data:
        if not isinstance(data['is_admin'], bool):
            return error('"is_admin" must be boolean', 403)
        if data['is_admin'] and not admin:
            return error('Admin rights are required for this action.', 401)
    try:
        user = User.from_dict(data)
    except ValueError:
        return error('User with this email or username already exists.', 403)
    return jsonify(user.to_dict()), 201


def user_exists(user_id, return_user=False):
    try:
        user = User.get_by_id(user_id)
    except User.DoesNotExist:
        return False
    if return_user:
        return user
    return True


def post_exists(post_id, return_post=False):
    try:
        post = Post.get_by_id(post_id)
    except Post.DoesNotExist:
        return False
    if return_post:
        return post
    return True
