from flask import Flask
from config import Config


app = Flask(__name__)
app.config.from_object(Config)


from blueprints.api import api

app.register_blueprint(api, url_prefix='/api')
