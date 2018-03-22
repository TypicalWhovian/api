from pathlib import Path

import yaml
from flask import Flask

from api.blueprints.models import create_tables


def get_config(testing):
    file = Path('config.yml')
    path = file
    if testing:
        path = '../..' / file
    with open(path) as config:
        c = yaml.load(config.read())
    return c


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_mapping(get_config(testing))
    from api.blueprints.api import api
    app.register_blueprint(api, url_prefix='/api')
    db = create_tables(app, testing=testing)
    if testing:
        app.testing = True
        return app.test_client(), db
    return app
