import unittest

import mimesis

from api.blueprints import create_app
from api.blueprints.models import Post, User
from api.blueprints.tests.api_tests import utils

MODELS = [Post, User]
URL = '/api'

p = mimesis.Person()
t = mimesis.Text()


class AdminRegistrationTests(unittest.TestCase):
    link = f'{URL}/admin'

    def setUp(self):
        self.app, self.db = create_app(testing=True)
        username, password = p.username(), p.password()
        User.from_dict(dict(username=username, email=p.email(),
                            password=password, is_admin=True))
        self.code, self.admin = utils.post(
            self.app,
            f'{URL}/auth/login',
            username=username,
            password=password
        )
        self.headers = {'x-access-token': self.admin['token']}

    def tearDown(self):
        self.db.drop_tables(MODELS)
        self.db.close()

    def test_registration(self):
        self.assertAlmostEqual(User.select().count(), 1)

        code, data = utils.post(
            self.app,
            f'{self.link}/register',
            headers=self.headers,
            username=p.username(), email=p.email(),
            password=p.password(), is_admin=True
        )
        self.assertAlmostEqual(code, 201)

    def test_getting_users(self):
        utils.create_users(10)
        code, users = utils.get(
            self.app,
            f'{self.link}/users',
            self.headers
        )
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(len(users), 11)

        code, user = utils.get(
            self.app,
            f'{self.link}/user/5',
            self.headers
        )
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(user, User.get_by_id(5).to_dict())

        code, _ = utils.get(
            self.app,
            f'{self.link}/user/15',
            self.headers
        )
        self.assertAlmostEqual(code, 404)

        admin = User.get_by_id(self.admin['id'])
        admin.is_admin = False
        admin.save()
        code, user = utils.get(
            self.app,
            f'{self.link}/user/5',
            self.headers
        )
        self.assertAlmostEqual(code, 401)

    def test_deleting_user(self):
        utils.create_users(10)
        code, msg = utils.delete(
            self.app,
            f'{self.link}/user/3',
            self.headers
        )
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(User.select().count(), 10)

        code, msg = utils.delete(
            self.app,
            f'{self.link}/user/23',
            self.headers
        )
        self.assertAlmostEqual(code, 404)
        self.assertAlmostEqual(msg['error'], 'User does not exist.')

        utils.create_posts(50)
        seventh_user = User.get_by_id(7)
        self.assertTrue(seventh_user.posts.count() > 0)

        data = {'delete_posts': True}
        code, msg = utils.delete(
            self.app,
            f'{self.link}/user/7',
            self.headers,
            'application/json',
            data
        )
        self.assertAlmostEqual(code, 200)

        num_of_posts = Post.select().where(Post.author == seventh_user).count()
        self.assertAlmostEqual(num_of_posts, 0)

    def test_getting_users_posts(self):
        utils.create_users(10)
        utils.create_posts(50)
        code, _ = utils.get(
            self.app,
            f'{self.link}/user/40/posts',
            self.headers
        )
        self.assertAlmostEqual(code, 404)

        code, posts = utils.get(
            self.app,
            f'{self.link}/user/7/posts',
            self.headers
        )
        self.assertAlmostEqual(code, 200)
        self.assertTrue(len(posts) > 0)

        code, _ = utils.get(
            self.app,
            f'{self.link}/user/40/post/100', self.headers
        )
        self.assertAlmostEqual(code, 404)

        post_id = User.get_by_id(2).posts.first().get_id()
        code, post = utils.get(
            self.app,
            f'{self.link}/user/2/post/{post_id}',
            self.headers
        )
        self.assertAlmostEqual(code, 200)
        self.assertDictEqual(post, Post.get_by_id(post_id).to_dict())

        code, _ = utils.get(
            self.app,
            f'{self.link}/user/2/post/70',
            self.headers
        )
        self.assertAlmostEqual(code, 404)

    def test_editing_users_post(self):
        utils.create_users(3)
        utils.create_posts(50)
        post_id = User.get_by_id(2).posts.first().get_id()
        code, post = utils.post(
            self.app,
            f'{self.link}/user/2/post/{post_id}',
            self.headers,
            title=42
        )
        self.assertAlmostEqual(code, 200)
        self.assertAlmostEqual(post['title'], '42')

        code, _ = utils.post(
            self.app,
            f'{self.link}/user/2/post/404',
            self.headers,
            title='42'
        )
        self.assertAlmostEqual(code, 404)

        code, _ = utils.post(
            self.app,
            f'{self.link}/user/404/post/404',
            self.headers,
            title='42'
        )
        self.assertAlmostEqual(code, 404)

        code, _ = utils.post(
            self.app,
            f'{self.link}/user/2/post/{post_id}',
            self.headers
        )
        self.assertAlmostEqual(code, 403)

    def test_deleting_users_post(self):
        utils.create_users(3)
        utils.create_posts(50)
        post_id = User.get_by_id(2).posts.first().get_id()
        code, _ = utils.delete(
            self.app,
            f'{self.link}/user/2/post/70',
            self.headers
        )
        self.assertAlmostEqual(code, 404)

        code, post = utils.delete(
            self.app,
            f'{self.link}/user/2/post/{post_id}',
            self.headers
        )
        self.assertAlmostEqual(code, 200)
        self.assertIs(None, Post.select().where(Post.id == post_id).first())


if __name__ == '__main__':
    unittest.main()
