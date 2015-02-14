import requests
import logging
from datetime import timedelta, datetime
from flask import Flask, jsonify
from werkzeug.exceptions import InternalServerError, default_exceptions
from google.appengine.api import urlfetch

BASE_URL_FILMTV_FILM = "http://www.filmtv.it/programmi-tv/film/"
BASE_URL_MYAPIFILMS = "http://www.myapifilms.com/"

TV_TYPE = ['free', 'sky', 'premium']

GENRES = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
          'Fantasy', 'Film-Noir', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Sport',
          'Thriller', 'War', 'Western']
# TODO: translate it
# GENRES_ITA = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
#               'Fantasy', 'Film-Noir', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Sport',
#               'Thriller', 'War', 'Western']

NUMBER_SUGGESTIONS = 3

GENRE_WEIGHT = 0.15
ACTOR_WEIGHT = 0.2
DIRECTOR_WEIGHT = 0.12
WRITER_WEIGHT = 0.1


def json_api(import_name, **kwargs):
    """
    Creates a JSON-oriented Flask app.

    All error responses that you don't specifically
    manage yourself will have applications/json content
    type, and will contain JSON like this (just an example)

    {
        "code": 1,
        "errorMessage": "The requested URL was not found on the server.  If you entered the URL manually please [...] ",
        "errorType": "404: Not Found"
    }

    More here: http://flask.pocoo.org/snippets/83/ (ad-hoc by pincopallino93)
    """

    def make_json_error(ex):
        response = jsonify(errorMessage=str(ex.description) if hasattr(ex, 'description') else str(ex), code=1,
                           errorType=str(ex))
        response.status_code = 200  # (ex.code if isinstance(ex, HTTPException) else 500)

        return response

    app = Flask(import_name, **kwargs)

    for code in default_exceptions:
        app.error_handler_spec[None][code] = make_json_error

    return app


def get(url):
    """
    Get the HTML page from URL.
    :param url: URL of the page to retrieve
    :type url: string
    :return: HTML page
    :rtype: string
    """
    urlfetch.set_default_fetch_deadline(60)
    try:
        response = requests.get(url)
    except Exception as exception:
        raise InternalServerError(exception)

    return response.text


def time_for_tomorrow():
    """
    This function return the seconds for tomorrow from now.
    :return: millis for tomorrow from now
    :rtype: integer
    """
    now = datetime.now()
    tomorrow = datetime.replace(now + timedelta(days=1), hour=0, minute=0, second=0)
    delta = tomorrow - now
    seconds = ((delta.days * 24 * 60 * 60 + delta.seconds) * 1000 + delta.microseconds / 1000.0) / 1000
    logging.info("Seconds for tomorrow: " + str(seconds))
    return seconds


def clear_url(url):
    """
    Return a clear IMDb url photo.
    :param url: url to clear
    :return: url cleared
    """
    if url is "":
        return None
    elif url is not None:
        end = url.index("._") if "._" in url else len(url)
        return url[:end]


class RetrieverError(Exception):
    """
    Exception for error in retrieving data from http://www.myapifilms.com/.
    """

    def __init__(self, code, message):
        """
        Constructor of Exception.
        :param code: error code
        :type code: int
        :param message: error message
        :type message: string
        :return: None
        """
        self.code = code
        self.message = message

    def __str__(self):
        return str(self.code) + ": " + self.message


if __name__ == "__main__":
    print time_for_tomorrow()