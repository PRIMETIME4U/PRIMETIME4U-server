import requests
from datetime import timedelta, datetime
from werkzeug.exceptions import InternalServerError

BASE_URL_FILMTV_FILM = "http://www.filmtv.it/programmi-tv/film/"
BASE_URL_MYAPIFILMS = "http://www.myapifilms.com/"
TV_TYPE = ['free', 'sky', 'premium']
NUMBER_SUGGESTIONS = 3


def get(url):
    """
    Get the HTML page from URL.
    :param url: URL of the page to retrieve
    :type url: string
    :return: HTML page
    :rtype: string
    """
    try:
        return requests.get(url).text
    except Exception as exception:
        raise InternalServerError(exception)


def time_for_tomorrow():
    """
    This function return the millis for tomorrow from now.
    :return: millis for tomorrow from now
    :rtype: integer
    """
    now = datetime.now()
    tomorrow = datetime.replace(now + timedelta(days=1), hour=0, minute=0, second=0)
    delta = tomorrow - now
    return ((delta.days * 24 * 60 * 60 + delta.seconds) * 1000 + delta.microseconds / 1000.0) / 1000


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