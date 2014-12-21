import requests


BASE_URL_FILMTV_FILM = "http://www.filmtv.it/programmi-tv/film/"


def get(url):
    """
    Get the HTML page from URL.

    :param url: URL of the page to retrieve
    :type url: string
    :return: HTML page
    :rtype: string
    """
    return requests.get(url).text

