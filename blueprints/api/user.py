import datetime

import jwt
from flask import jsonify, request

from blueprints import app
from blueprints.api.utils import create_user, data_required, error, message, post_exists, token_required
from blueprints.models import Post, User
from . import api


@api.route('/auth/register', methods=['POST'])
def auth_register():
    data = request.get_json()
    return create_user(data)


@api.route('/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json()
    email, username = data.get('email'), data.get('username')
    password = data.get('password')
    if not any((email, username)) or password is None:
        return error('Both email/username and password are required.', 401)
    user = User.select().where((User.email == email) |
                               (User.username == username)).first()
    if user is None:
        return error('User does not exist.', 403)
    if not user.check_password(password):
        return error('Wrong password.', 403)
    token = jwt.encode({
        'id': user.get_id(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    data = user.to_dict()
    data['token'] = token.decode('UTF-8')
    return jsonify(data), 200


@api.route('/me/post', methods=['POST'])
@data_required
@token_required()
def add_post(current_user):
    data = request.get_json()
    if not data:
        return error('Data was not provided.', 403)
    if None in (data.get('title'), data.get('text')):
        return error('Both title and text are required.', 403)
    data['author'] = current_user
    post = Post.from_dict(data)
    return jsonify(post.to_dict()), 201


@api.route('/me/post/:<post_id>', methods=['GET'])
@token_required(return_user=False)
def get_post(post_id):
    post = post_exists(post_id, return_post=True)
    if not post:
        return error('Post does not exist.', 404)
    return jsonify(post.to_dict()), 200


@api.route('/me/post/:<post_id>', methods=['POST'])
@data_required
@token_required(return_user=False)
def edit_post(post_id):
    if not post_exists(post_id):
        return error('Post does not exist.', 404)
    data = request.get_json()
    post_data = {field: data[field] for field in Post._meta.allowed_fields
                 if data.get(field) is not None}
    Post.update(post_data).where(Post.id == post_id).execute()
    return jsonify(Post.get_by_id(post_id).to_dict()), 200


@api.route('/me/post/:<post_id>', methods=['DELETE'])
@token_required(return_user=False)
def delete_post(post_id):
    if not post_exists(post_id):
        return error('Post does not exist.', 404)
    Post.delete_by_id(post_id)
    return message('Deleted.', 200)


@api.route('/posts', methods=['GET'])
@token_required()
def search_posts(current_user):
    select_query = current_user.posts
    query = request.args.get('query')
    if query is not None:
        select_query = select_query.where((Post.title.contains(query)) |
                                          (Post.text.contains(query)))
    try:
        posts = [post.to_dict() for post in select_query]
    except AttributeError:
        return error('No such posts.', 404)
    return jsonify(posts), 200


@api.route('/me/posts/others', methods=['GET'])
@token_required()
def get_others_posts(current_user):
    posts = [post.to_dict() for post in
             Post.select().where(Post.author != current_user)]
    if not posts:
        return error('No posts from other users.', 404)
    return jsonify(posts), 200
