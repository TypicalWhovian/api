from flask import Flask

from blueprints.models import create_tables
from config import Config


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    from blueprints.api import api
    app.register_blueprint(api, url_prefix='/api')
    db = create_tables(app, testing=testing)
    if testing:
        app.testing = True
        return app.test_client(), db
    return app
