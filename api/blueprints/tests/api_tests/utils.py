import json
from random import choice

import mimesis

from api.blueprints.models import Post, User

p = mimesis.Person()
t = mimesis.Text()


def post(app, url, headers=None, **data):
    data = json.dumps(data)
    r = app.post(url, data=data, headers=headers,
                 mimetype='application/json')
    return r.status_code, json.loads(r.get_data())


def get(app, url, headers):
    r = app.get(url, headers=headers)
    return r.status_code, json.loads(r.get_data())


def delete(app, url, headers, mimetype=None, data=None):
    if data is not None:
        data = json.dumps(data)
    r = app.delete(url, headers=headers, mimetype=mimetype, data=data)
    return r.status_code, json.loads(r.get_data())


def create_users(quantity):
    for _ in range(quantity):
        User.from_dict({
            'username': p.username(),
            'email': p.email(),
            'password': p.password(),
        })


def create_posts(quantity, users_list=None):
    users = users_list or list(User.select())
    for _ in range(quantity):
        Post.from_dict({
            'title': t.title(),
            'text': t.text(),
            'author': choice(users),
        })
