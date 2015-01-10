import json
from models import Movie, Artist
from utilities import get, RetrieverError, BASE_URL_MYAPIFILMS


def retrieve_movie(movie_title):
    """
    Retrieve movie info from IMDB by movie title.
    :param movie_title: title of the film to retrieve info
    :type movie_title: string
    :return: Movie's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    url = BASE_URL_MYAPIFILMS + 'imdb?title=' + movie_title + '&format=JSON&aka=0&business=0&seasons=0&seasonYear=0&technical=0&filter=N&exactFilter=0&limit=1&lang=en-us&actors=S&biography=0&trailer=1&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0'

    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    if type(json_data) is not list:  # If it is not a list there is a problem
        raise RetrieverError(json_data["code"], json_data["message"])

    obj = Movie(id=json_data[0]["idIMDB"],
                original_title=json_data[0]["originalTitle"],
                plot=json_data[0]["plot"],
                poster=json_data[0]["urlPoster"],
                rated=json_data[0]["rated"],
                run_times=json_data[0]["runtime"][0],
                title=json_data[0]["title"],
                simple_plot=json_data[0]["simplePlot"],
                genres=json_data[0]["genres"])

    try:
        trailer_url = json_data[0]["trailer"]["videoURL"]
        obj.trailer = trailer_url
    except KeyError:
        pass

    year = json_data[0]["year"]
    if len(year) > 4:
        year = year[-4:]


    obj.year = year
    key = obj.put()
    actors_list = json_data[0]["actors"]
    directors_list = json_data[0]["directors"]
    writers_list = json_data[0]["writers"]

    retrieve_artists(obj, actors_list, directors_list, writers_list)
    return key


def retrieve_artists(obj, actors_list, directors_list, writers_list):
    """

    :param artist_name:
    :return:
    """



    for json_data in actors_list:
        act = Artist(id=json_data["actorId"],
                 name=json_data["actorName"],
                 photo=json_data["urlPhoto"])
        act.put()
        obj.add_actor(act)



    for json_data in directors_list:
        rgs = Artist(id=json_data["nameId"],
                   name=json_data["name"])
        rgs.put()
        obj.add_director(rgs)



    for json_data in writers_list:
        wrt = Artist(id=json_data["nameId"],
                 name=json_data["name"])
        wrt.put()
        obj.add_writer(wrt)




    return 'Amen'

def retrieve_artist(artist_name):
    """
    Retrieve artist info from IMDB by name of artist.
    :param name_artist: name of the artist to retrieve info
    :type name_artist: string
    :return: Artist's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    url = BASE_URL_MYAPIFILMS + 'imdb?name=' + artist_name + '&format=JSON&filmography=0&limit=1&lang=en-us&exactFilter=0&bornDied=0&starSign=0&uniqueName=0&actorActress=0&actorTrivia=0'
    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    if type(json_data) is not list:  # If it is not a list there is a problem
        raise RetrieverError(json_data["code"], json_data["message"])

    act = Artist(id=json_data["actorId"],
                 name=json_data["actorName"],
                 photo=json_data["urlPhoto"])

    key = act.put()

    return key

