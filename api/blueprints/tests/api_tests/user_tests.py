import unittest

import mimesis
from flask import request

from api.blueprints import create_app
from api.blueprints.models import Post, User
from api.blueprints.tests.api_tests import utils

MODELS = [Post, User]
URL = '/api'

p = mimesis.Person()
t = mimesis.Text()


class RegistrationTests(unittest.TestCase):
    def register(self, username=None, email=None, password=None, is_admin=False):
        data = dict(
            username=username,
            email=email,
            password=password,
            is_admin=is_admin,
        )
        return utils.post(self.app, f'{URL}/auth/register', **data)

    def login(self, username=None, email=None, password=None):
        data = dict(username=username, email=email, password=password)
        return utils.post(self.app, f'{URL}/auth/login', **data)

    def setUp(self):
        self.app, self.db = create_app(testing=True)

    def tearDown(self):
        self.db.drop_tables(MODELS)
        self.db.close()

    def test_registration(self):
        username, email, password = p.username(), p.email(), p.password()
        code1, _ = self.register(username, email, password)
        code2, _ = self.register(username, email, password)
        self.assertAlmostEqual(code1, 201)
        self.assertAlmostEqual(code2, 403)
        code, _ = self.register(p.username(), p.email(), p.password(), True)
        self.assertAlmostEqual(code, 401)
        code, _ = self.register(p.username(), p.email(), p.password(), None)
        self.assertAlmostEqual(code, 403)
        code, _ = self.register(p.username(), p.password())
        self.assertAlmostEqual(code, 403)
        code, _ = self.register(True, False, False)
        self.assertAlmostEqual(code, 201)

    def test_login(self):
        username, email, password = p.username(), p.email(), p.password()
        self.register(username, email, password)
        code, data = self.login(username=username, password=password)
        self.assertAlmostEqual(code, 200)
        self.assertIn('token', data)
        code, _ = self.login(username=True, password=password)
        self.assertAlmostEqual(code, 403)
        code, _ = self.login()
        self.assertAlmostEqual(code, 401)
        code, _ = self.login(username=username, password='shit')
        self.assertAlmostEqual(code, 403)
        code, _ = self.login(email=True, password=password)
        self.assertAlmostEqual(code, 403)
        code, data = self.login(email=email, password=password)
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(data['email'], email)
        self.assertAlmostEqual(data['username'], username)
        self.assertAlmostEqual(data['is_admin'], False)


class PostUserRelatedTests(unittest.TestCase):
    link = f'{URL}/me/post'

    def setUp(self):
        self.app, self.db = create_app(testing=True)
        username, email, password = p.username(), p.email(), p.password()
        utils.post(self.app, f'{URL}/auth/register',
                   username=username, email=email, password=password)
        _, data = utils.post(self.app, f'{URL}/auth/login',
                             username=username, email=email, password=password)
        self.user = data
        self.headers = {'x-access-token': self.user['token']}
        self.code, self.first_post = utils.post(self.app, self.link, self.headers,
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
        code, _ = utils.post(self.app, self.link, self.headers, title=t.title())
        # no post text
        self.assertAlmostEqual(code, 403)
        # no token
        code, _ = utils.post(self.app, self.link, title=t.title(), text=t.text())
        self.assertAlmostEqual(code, 401)
        # boolean values as data
        code, _ = utils.post(self.app, self.link, self.headers,
                             title=True, text=False)
        self.assertAlmostEqual(code, 201)

    def test_get_post(self):
        code, _ = utils.get(self.app, f'{self.link}/:1', self.headers)
        self.assertAlmostEqual(code, 200)
        # non-existing post id
        code, _ = utils.get(self.app, f'{self.link}/:15', self.headers)
        self.assertAlmostEqual(code, 404)
        # invalid token
        code, _ = utils.get(self.app, f'{self.link}/:1', {'x-access-token': 'abc'})
        self.assertAlmostEqual(code, 401)

    def test_edit_post(self):
        # no data
        code, _ = utils.post(self.app, f'{self.link}/:1', self.headers)
        self.assertAlmostEqual(code, 403)
        code, _ = utils.post(self.app, f'{self.link}/:1', self.headers,
                             title='New title')
        self.assertAlmostEqual(code, 200)

    def test_delete_post(self):
        code, _ = utils.delete(self.app, f'{self.link}/:15', self.headers)
        self.assertAlmostEqual(code, 404)
        code, _ = utils.delete(self.app, f'{self.link}/:1', self.headers)
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(Post.select().count(), 0)

    def test_search(self):
        utils.post(self.app, self.link, self.headers,
                   title='The_Title', text=t.text())
        utils.post(self.app, self.link, self.headers,
                   title=t.title(), text='What about The_Title')
        with self.app as c:
            c.get('/posts?query=The_Title')
            assert request.args['query'] == 'The_Title'

    def test_others_posts(self):
        utils.create_users(3)
        code, _ = utils.get(self.app, f'{URL}/me/posts/others', self.headers)
        self.assertAlmostEqual(code, 404)
        users = list(User.select().where(User.id != self.user['id']))
        utils.create_posts(10, users)
        code, data = utils.get(self.app, f'{URL}/me/posts/others', self.headers)
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(len(data), 10)


if __name__ == '__main__':
    unittest.main()
