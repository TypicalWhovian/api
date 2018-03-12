from flask import Flask
from config import Config
from blueprints.models import create_tables


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    create_tables(app)
    from blueprints.api import api
    app.register_blueprint(api, url_prefix='/api')

    return app
