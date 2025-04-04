import os
from flask import Flask
from dotenv import load_dotenv

from spotipy.oauth2 import SpotifyOAuth

from . import views

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    load_dotenv()
    
    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY")
    )

    app.register_blueprint(views.bp)

    return app
