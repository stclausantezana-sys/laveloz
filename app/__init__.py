import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()


def create_app():
    app = Flask(__name__, template_folder="web/templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cambiar-en-produccion")
    from .web.rutas import bp
    app.register_blueprint(bp)
    return app
