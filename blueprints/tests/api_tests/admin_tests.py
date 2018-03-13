import json
import unittest
from random import choice

import mimesis

from blueprints import create_app
from blueprints.models import Post, User

app = create_app(testing=True)

MODELS = [Post, User]
URL = '/api'

p = mimesis.Person()
t = mimesis.Text()


class AdminRegistrationTests(unittest.TestCase):
    link = f'{URL}/admin'

    def post(self, url, headers=None, **data):
        data = json.dumps(data)
        r = self.app.post(url, data=data, headers=headers, mimetype='application/json')
        return r.status_code, json.loads(r.get_data())

    def get(self, url, headers):
        r = self.app.get(url, headers=headers)
        return r.status_code, json.loads(r.get_data())

    def delete(self, url, headers, mimetype=None, data=None):
        if data is not None:
            data = json.dumps(data)
        r = self.app.delete(url, headers=headers, mimetype=mimetype, data=data)
        return r.status_code, json.loads(r.get_data())

    def create_users(self, quantity):
        for _ in range(quantity):
            User.from_dict({
                'username': p.username(),
                'email': p.email(),
                'password': p.password(),
            })

    def create_posts(self, quantity):
        users = list(User.select())
        for _ in range(quantity):
            Post.from_dict({
                'title': t.title(),
                'text': t.text(),
                'author': choice(users),
            })

    def setUp(self):
        self.app, self.db = create_app(testing=True)
        username, password = p.username(), p.password()
        User.from_dict(dict(username=username, email=p.email(),
                            password=password, is_admin=True))
        self.code, self.admin = self.post(f'{URL}/auth/login', username=username, password=password)
        self.headers = {'x-access-token': self.admin['token']}

    def tearDown(self):
        self.db.drop_tables(MODELS)
        self.db.close()

    def test_registration(self):
        self.assertAlmostEqual(User.select().count(), 1)
        code, data = self.post(f'{self.link}/register', headers=self.headers,
                               username=p.username(), email=p.email(),
                               password=p.password(), is_admin=True)
        self.assertAlmostEqual(code, 201)

    def test_getting_users(self):
        self.create_users(10)
        code, users = self.get(f'{self.link}/users', self.headers)
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(len(users), 11)
        code, user = self.get(f'{self.link}/user/5', self.headers)
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(user, User.get_by_id(5).to_dict())
        code, _ = self.get(f'{self.link}/user/15', self.headers)
        self.assertAlmostEqual(code, 404)
        admin = User.get_by_id(self.admin['id'])
        admin.is_admin = False
        admin.save()
        code, user = self.get(f'{self.link}/user/5', self.headers)
        self.assertAlmostEqual(code, 401)

    def test_deleting_user(self):
        self.create_users(10)
        code, msg = self.delete(f'{self.link}/user/3', self.headers)
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(User.select().count(), 10)
        code, msg = self.delete(f'{self.link}/user/23', self.headers)
        self.assertAlmostEqual(code, 404)
        self.assertAlmostEqual(msg['error'], 'User does not exist.')
        self.create_posts(50)
        seventh_user = User.get_by_id(7)
        self.assertTrue(seventh_user.posts.count() > 0)
        data = {'delete_posts': True}
        code, msg = self.delete(f'{self.link}/user/7', self.headers, 'application/json', data)
        self.assertAlmostEqual(code, 200)
        num_of_posts = Post.select().where(Post.author == seventh_user).count()
        self.assertAlmostEqual(num_of_posts, 0)

    def test_getting_users_posts(self):
        self.create_users(10)
        self.create_posts(50)
        code, _ = self.get(f'{self.link}/user/40/posts', self.headers)
        self.assertAlmostEqual(code, 404)
        code, posts = self.get(f'{self.link}/user/7/posts', self.headers)
        self.assertAlmostEqual(code, 200)
        self.assertTrue(len(posts) > 0)
        code, _ = self.get(f'{self.link}/user/40/post/100', self.headers)
        self.assertAlmostEqual(code, 404)
        post_id = User.get_by_id(2).posts.first().get_id()
        code, post = self.get(f'{self.link}/user/2/post/{post_id}', self.headers)
        self.assertAlmostEqual(code, 200)
        self.assertDictEqual(post, Post.get_by_id(post_id).to_dict())
        code, _ = self.get(f'{self.link}/user/2/post/70', self.headers)
        self.assertAlmostEqual(code, 404)

    def test_editing_users_post(self):
        self.create_users(3)
        self.create_posts(50)
        post_id = User.get_by_id(2).posts.first().get_id()
        code, post = self.post(f'{self.link}/user/2/post/{post_id}',
                               self.headers, title=42)
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(post['title'], '42')
        code, _ = self.post(f'{self.link}/user/2/post/404',
                            self.headers, title='42')
        self.assertAlmostEqual(code, 404)
        code, _ = self.post(f'{self.link}/user/404/post/404',
                            self.headers, title='42')
        self.assertAlmostEqual(code, 404)
        code, _ = self.post(f'{self.link}/user/2/post/{post_id}', self.headers)
        self.assertAlmostEqual(code, 403)

    def test_deleting_users_post(self):
        self.create_users(3)
        self.create_posts(50)
        post_id = User.get_by_id(2).posts.first().get_id()
        code, _ = self.delete(f'{self.link}/user/2/post/70', self.headers)
        self.assertAlmostEqual(code, 404)
        code, post = self.delete(f'{self.link}/user/2/post/{post_id}', self.headers)
        self.assertAlmostEqual(code, 200)
        self.assertIs(None, Post.select().where(Post.id == post_id).first())


if __name__ == '__main__':
    unittest.main()
