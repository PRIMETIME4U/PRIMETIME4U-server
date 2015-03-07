# coding=utf-8
import requests
import logging
from datetime import timedelta, datetime
from flask import Flask, jsonify
from werkzeug.exceptions import InternalServerError, default_exceptions
from google.appengine.api import urlfetch


TV_CHANNELS = {"Rai 1": 1, "Rai 2": 2, "Rai3": 3, "Rete 4": 4, "Canale 5": 5,  "Italia 1": 6, "La7": 7, "MTV": 8,
               "Deejay TV": 9, "Rai 4": 21, "Iris": 22, "Rai 5": 23, "Rai Movie": 24, "Rai Premium": 25, "Cielo": 26,
               "Class TV": 27, "TV 2000": 28, "La7D": 29, "La5": 30, "Real Time": 31, "QVC": 32, "ABC": 33,
               "Mediaset Extra": 34, "Mediaset Italia 2": 35, "RTL 102.5 TV": 36, "Giallo": 38, "Top Crime": 39,
               "Boing": 40, "K2": 41, "Rai Gulp": 42, "Rai YOYO": 43, "Frisbee": 44, "DMAX": 52, "Premium Cinema": 311,
               "Premium Emotion": 312, "Premium Energy": 313, "Premium Cinema Comedy": 314,
               "Studio Universal": 315, "Premium Cinema HD": 320, "Joi": 321, "Mya": 322, "Premium Action": 323,
               "Premium Crime": 324, "Premium Extra 1": 326, "Premium Extra 2": 327}


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

def channel_number(channel_name):
    """
    return the channel_number of the channel_name
    :param channel_name: channel to retrieve number
    :type channel_name: string
    :return: channel number
    :rtype: string
    """
    try:
        val = str(TV_CHANNELS[channel_name])
    except KeyError:
        val = "NotFound"

    return val


if __name__ == "__main__":
    print time_for_tomorrow()