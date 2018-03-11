from flask import jsonify, request

from blueprints.api.utils import create_user, error, message, token_required, user_exists, data_required
from blueprints.models import Post, User
from . import api


@api.route('/admin/register', methods=['POST'])
@token_required(admin_required=True, return_user=False)
def register_admin():
    data = request.get_json()
    return create_user(data, admin=True)


@api.route('/admin/users', methods=['GET'])
@token_required(admin_required=True, return_user=False)
def get_users():
    users = [user.to_dict() for user in User.select()]
    return jsonify(users), 200


@api.route('/admin/user/<user_id>', methods=['GET'])
@token_required(admin_required=True, return_user=False)
def get_user(user_id):
    user = user_exists(user_id, return_user=True)
    if not user:
        return error('User does not exist.', 404)
    return jsonify(user.to_dict()), 200


@api.route('/admin/user/<user_id>', methods=['DELETE'])
@token_required(admin_required=True, return_user=False)
def delete_user(user_id):
    data = request.get_json() or {}
    user = user_exists(user_id, return_user=True)
    if not user:
        return error('User does not exist.', 404)
    if data.get('delete_posts'):
        for post in user.posts:
            post.delete_instance()
    user.delete_instance()
    return message('Deleted.', 200)


@api.route('/admin/user/<user_id>/posts', methods=['GET'])
@token_required(admin_required=True, return_user=False)
def get_users_posts(user_id):
    user = user_exists(user_id, return_user=True)
    if not user:
        return error('User does not exist.', 404)
    posts = [post.to_dict() for post in user.posts]
    return jsonify(posts), 200


@api.route('/admin/user/<user_id>/post/<post_id>', methods=['POST'])
@data_required
@token_required(admin_required=True, return_user=False)
def edit_users_post(user_id, post_id):
    user = user_exists(user_id, return_user=True)
    if not user:
        return error('User does not exist.', 404)
    if user.posts.where(Post.id == post_id).first() is None:
        return error('Selected user does not have the post.', 404)
    data = request.get_json()
    post_data = {field: data[field] for field in Post._meta.allowed_fields
                 if data.get(field) is not None}
    Post.update(post_data).where(Post.id == post_id).execute()
    post = Post.get_by_id(post_id)
    return jsonify(post.to_dict()), 200


@api.route('/admin/user/<user_id>/post/<post_id>', methods=['GET'])
@token_required(admin_required=True, return_user=False)
def get_users_post(user_id, post_id):
    user = user_exists(user_id, return_user=True)
    if not user:
        return error('User does not exist.', 404)
    post = user.posts.where(Post.id == post_id).first()
    if post is not None:
        return jsonify(post.to_dict()), 200
    return error('Selected user does not have the post.', 404)


@api.route('/admin/user/<user_id>/post/<post_id>', methods=['DELETE'])
@token_required(admin_required=True, return_user=False)
def delete_users_post(user_id, post_id):
    user = user_exists(user_id, return_user=True)
    if not user:
        return error('User does not exist.', 404)
    post = user.posts.where(Post.id == post_id).first()
    if post is not None:
        post.delete_instance()
        return message('Deleted.', 200)
    return error('Selected user does not have the post.', 404)
