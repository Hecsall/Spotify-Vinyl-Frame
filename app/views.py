
import os
from flask import (
    Blueprint, render_template, request, session, Response
)
import spotipy
from random import randint


bp = Blueprint('views', __name__, url_prefix='/')


FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_SCOPES = ["user-read-recently-played", "user-read-currently-playing"]
BASE_URL = os.getenv("BASE_URL")
REDIRECT_URI = "{}/".format(BASE_URL)
CACHE_TOKEN_INFO = {}


# Spotipy custom Cache Handler
# It just saves the token_info in an unused variable since
# not saving it would trigger a Spotipy error
class UselessCacheHandler(spotipy.cache_handler.CacheHandler):
    def get_cached_token(self):
        """
        Get and return a token_info dictionary object.
        """
        return session.get("unused_token_info")

    def save_token_to_cache(self, token_info):
        """
        Save a token_info dictionary object to the cache and return None.
        """
        session["unused_token_info"] = token_info
        return None


cache_handler = UselessCacheHandler()

auth_manager = spotipy.oauth2.SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SPOTIFY_SCOPES,
    cache_handler=cache_handler,
    show_dialog=False,
)


def get_user_id(auth_manager, code):
    print(code)
    # Get Access Token
    token_info = auth_manager.get_access_token(request.args.get("code"), as_dict=True)
    access_token = token_info["access_token"]
    # Get User Info
    spotify_api = spotipy.Spotify(auth=access_token)
    user_id = spotify_api.me()["id"]
    # Save to session
    session["token_info"] = token_info
    session["token_info"]["uid"] = user_id
    return user_id


# Retrieve Access Token from Session
def get_access_token():
    token_info = session.get("token_info")

    if auth_manager.is_token_expired(token_info):
        updated_token_info = auth_manager.validate_token(token_info)
        access_token = updated_token_info["access_token"]
    else:
        access_token = token_info["access_token"]

    return access_token


# Given a user ID, return the currently playing track
def get_song_info(access_token):
    spotify = spotipy.Spotify(auth=access_token)
    track = spotify.current_user_playing_track()
    if track is not None and track["item"] is not None:
        return track, True
    else:
        # Get a random recently played track from the last 10
        tracks = spotify.current_user_recently_played(limit=10)
        track = {}
        track["item"] = tracks["items"][randint(0, 9)]["track"]
        return track, False


@bp.route('/')
def index():
    if request.args.get("code"):
        user_id = get_user_id(
            auth_manager=auth_manager, code=request.args.get("code")
        )

    rendered_data = {"title": "Home"}

    session_token_info = session.get("token_info")
    if not auth_manager.validate_token(session_token_info):
        auth_url = auth_manager.get_authorize_url()
        rendered_data["auth_url"] = auth_url
        rendered_data["is_authenticated"] = False
    else:
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        rendered_data["spotify"] = spotify
        rendered_data["is_authenticated"] = True

        access_token = get_access_token()
        if not access_token:
            return Response("User not authorized", status=403)
        song, is_now_playing = get_song_info(session_token_info['access_token'])

        rendered_data["song"] = song
        rendered_data["is_now_playing"] = is_now_playing

    return render_template("index.html", **rendered_data)