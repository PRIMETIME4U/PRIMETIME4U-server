import json
from models import Movie, Artist
from utilities import get, RetrieverError, BASE_URL_MYAPIFILMS


def retrieve_movie(movie_title):
    """

    :param movie_title:
    :return:
    :rtype:
    """
    url = BASE_URL_MYAPIFILMS + 'imdb?title=' + movie_title + '&format=JSON&aka=0&business=0&seasons=0&seasonYear=0&technical=0&filter=N&exactFilter=0&limit=1&lang=en-us&actors=N&biography=0&trailer=1&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0'

    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    if type(json_data) is not list:
        raise RetrieverError(json_data["code"], json_data["message"])

    obj = Movie(id=json_data[0]["idIMDB"],
                original_title=json_data[0]["originalTitle"],
                plot=json_data[0]["plot"],
                poster=json_data[0]["urlPoster"],
                rated=json_data[0]["rated"],
                run_times=json_data[0]["runtime"][0],
                title=json_data[0]["title"],
                simple_plot=json_data[0]["simplePlot"])

    return obj.put()


# def retrieve_artist(artist_name):
#     """
#
#     :param artist_name:
#     :return:
#     """
#     url =
#
#     json_page = get(url).encode('utf-8')
#     json_data = json.loads(json_page)[0]
#
#     obj = Artist(id=json_data["idIMDB"],
#
#     obj.put()