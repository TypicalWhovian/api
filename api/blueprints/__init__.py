from flask import Flask

from api.blueprints.models import create_tables
from api.config import Config


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    from api.blueprints.api import api
    app.register_blueprint(api, url_prefix='/api')
    db = create_tables(app, testing=testing)
    if testing:
        app.testing = True
        return app.test_client(), db
    return app
