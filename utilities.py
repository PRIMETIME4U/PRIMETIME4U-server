import requests

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
    return requests.get(url).text


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