import json
from models import Movie, Artist
from utilities import get


def retrieve_movie(movie_title):
    """

    :param movie_title:
    :return:
    :rtype:
    """
    url = 'http://www.myapifilms.com/imdb?title=' + movie_title + '&format=JSON&aka=0&business=0&seasons=0&seasonYear=0&technical=0&filter=N&exactFilter=0&limit=1&lang=en-us&actors=N&biography=0&trailer=1&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0'

    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)[0]

    obj = Movie(id=json_data["idIMDB"],
                original_title=json_data["originalTitle"],
                plot=json_data["plot"],
                poster=json_data["urlPoster"],
                rated=json_data["rated"],
                run_times=json_data["runtime"][0],
                title=json_data["title"],
                simple_plot=json_data["simplePlot"])

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