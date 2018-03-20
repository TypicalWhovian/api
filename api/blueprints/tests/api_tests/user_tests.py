import json
import unittest
from random import choice

import mimesis
from flask import request

from api.blueprints import create_app
from api.blueprints.models import Post, User

MODELS = [Post, User]
URL = '/api'

p = mimesis.Person()
t = mimesis.Text()


class RegistrationTests(unittest.TestCase):
    def register(self, username=None, email=None, password=None, is_admin=False):
        data = json.dumps(dict(
            username=username,
            email=email,
            password=password,
            is_admin=is_admin,
        ))
        return self.app.post(f'{URL}/auth/register', data=data, mimetype='application/json')

    def login(self, username=None, email=None, password=None):
        data = json.dumps(dict(
            username=username,
            email=email,
            password=password,
        ))
        return self.app.post(f'{URL}/auth/login', data=data, mimetype='application/json')

    def setUp(self):
        self.app, self.db = create_app(testing=True)

    def tearDown(self):
        self.db.drop_tables(MODELS)
        self.db.close()

    def test_registration(self):
        username, email, password = p.username(), p.email(), p.password()
        r1 = self.register(username, email, password)
        r2 = self.register(username, email, password)
        self.assertAlmostEqual(r1.status_code, 201)
        self.assertAlmostEqual(r2.status_code, 403)
        r = self.register(p.username(), p.email(), p.password(), True)
        self.assertAlmostEqual(r.status_code, 401)
        r = self.register(p.username(), p.email(), p.password(), None)
        self.assertAlmostEqual(r.status_code, 403)
        r = self.register(p.username(), p.password())
        self.assertAlmostEqual(r.status_code, 403)
        r = self.register(True, False, False)
        self.assertAlmostEqual(r.status_code, 201)

    def test_login(self):
        username, email, password = p.username(), p.email(), p.password()
        self.register(username, email, password)
        r = self.login(username=username, password=password)
        self.assertAlmostEqual(r.status_code, 200)
        data = json.loads(r.get_data())
        self.assertIn('token', data)
        r = self.login(username=True, password=password)
        self.assertAlmostEqual(r.status_code, 403)
        r = self.login()
        self.assertAlmostEqual(r.status_code, 401)
        r = self.login(username=username, password='shit')
        self.assertAlmostEqual(r.status_code, 403)
        r = self.login(email=True, password=password)
        self.assertAlmostEqual(r.status_code, 403)
        r = self.login(email=email, password=password)
        self.assertAlmostEqual(r.status_code, 200)
        data = json.loads(r.get_data())
        self.assertAlmostEqual(data['email'], email)
        self.assertAlmostEqual(data['username'], username)
        self.assertAlmostEqual(data['is_admin'], False)


class PostUserRelatedTests(unittest.TestCase):
    link = f'{URL}/me/post'

    def post(self, url, headers=None, **data):
        data = json.dumps(data)
        r = self.app.post(url, data=data, headers=headers, mimetype='application/json')
        return r.status_code, json.loads(r.get_data())

    def setUp(self):
        self.app, self.db = create_app(testing=True)
        username, email, password = p.username(), p.email(), p.password()
        self.post(f'{URL}/auth/register', username=username, email=email, password=password)
        _, data = self.post(f'{URL}/auth/login', username=username, email=email, password=password)
        self.user = data
        self.headers = {'x-access-token': self.user['token']}
        self.code, self.first_post = self.post(self.link, self.headers,
                                               title=t.title(), text=t.text())

    def tearDown(self):
        self.db.drop_tables(MODELS)
        self.db.close()

    def test_add_post(self):
        # created
        self.assertAlmostEqual(self.code, 201)
        # usernames are equal
        self.assertAlmostEqual(self.first_post['author']['username'],
                               self.user['username'])
        code, _ = self.post(self.link, self.headers, title=t.title())
        # no post text
        self.assertAlmostEqual(code, 403)
        # no token
        code, _ = self.post(self.link, title=t.title(), text=t.text())
        self.assertAlmostEqual(code, 401)
        # boolean values as data
        code, _ = self.post(self.link, self.headers, title=True, text=False)
        self.assertAlmostEqual(code, 201)

    def test_get_post(self):
        r = self.app.get(f'{self.link}/:1', headers=self.headers)
        self.assertAlmostEqual(r.status_code, 200)
        # non-existing post id
        r = self.app.get(f'{self.link}/:15', headers=self.headers)
        self.assertAlmostEqual(r.status_code, 404)
        # invalid token
        r = self.app.get(f'{self.link}/:1', headers={'x-access-token': 'abc'})
        self.assertAlmostEqual(r.status_code, 401)

    def test_edit_post(self):
        # no data
        code, _ = self.post(f'{self.link}/:1', self.headers)
        self.assertAlmostEqual(code, 403)
        code, _ = self.post(f'{self.link}/:1', self.headers, title='New title')
        self.assertAlmostEqual(code, 200)

    def test_delete_post(self):
        r = self.app.delete(f'{self.link}/:15', headers=self.headers)
        self.assertAlmostEqual(r.status_code, 404)
        r = self.app.delete(f'{self.link}/:1', headers=self.headers)
        self.assertAlmostEqual(r.status_code, 200)
        self.assertAlmostEqual(Post.select().count(), 0)

    def test_search(self):
        self.post(self.link, self.headers, title='The_Title', text=t.text())
        self.post(self.link, self.headers, title=t.title(), text='What about The_Title')
        with self.app as c:
            c.get('/posts?query=The_Title')
            assert request.args['query'] == 'The_Title'

    def test_others_posts(self):
        for _ in range(3):
            User.from_dict({'email': p.email(), 'username': p.username(), 'password': p.password()})
        r = self.app.get(f'{URL}/me/posts/others', headers=self.headers)
        self.assertAlmostEqual(r.status_code, 404)
        users = list(User.select().where(User.id != self.user['id']))
        for _ in range(10):
            Post.from_dict({'title': p.title(), 'text': t.text(), 'author': choice(users)})
        r = self.app.get(f'{URL}/me/posts/others', headers=self.headers)
        data = json.loads(r.get_data())
        self.assertAlmostEqual(r.status_code, 200)
        self.assertAlmostEqual(len(data), 10)


if __name__ == '__main__':
    unittest.main()
