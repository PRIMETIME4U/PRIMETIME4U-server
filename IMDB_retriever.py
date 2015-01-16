import json
import lxml
from models import Movie, Artist
from utilities import get, RetrieverError, BASE_URL_MYAPIFILMS


def retrieve_movie_from_title(movie_title, movie_original_title, movie_url):
    """
    Retrieve movie info from IMDB by movie title.
    :param movie_title: title of the film to retrieve info
    :type movie_title: string
    :param movie_original_title: original title of the film to retrieve info
    :type movie_original_title: string
    :return: Movie's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    url = BASE_URL_MYAPIFILMS + 'imdb?title=' + movie_title + '&format=JSON&aka=1&business=0&seasons=0&seasonYear=0&technical=0&filter=N&exactFilter=0&limit=1&lang=en-us&actors=S&biography=0&trailer=1&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0'

    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    if type(json_data) is not list:  # If it is not a list there is a problem
        raise RetrieverError(json_data["code"], json_data["message"])


    movie = Movie(id=json_data[0]["idIMDB"],
                  plot=json_data[0]["plot"],
                  poster=json_data[0]["urlPoster"],
                  rated=json_data[0]["rated"],
                  simple_plot=json_data[0]["simplePlot"],
                  genres=json_data[0]["genres"])

    #html_page_plot = get(movie_url).encode('utf-8')
    #tree = lxml.html.fromstring(html_page_plot)
    #plot_it = tree.xpath('//article[@class="scheda-desc"]/p/text()')
    #movie.plot_it = str(plot_it)   # Save movie italian plot

    try:
        trailer_url = json_data[0]["trailer"]["videoURL"]
        movie.trailer = trailer_url
    except KeyError:
        movie.trailer = None

    movie.title = movie_title
    movie.original_title = movie_original_title

    run_times = json_data[0]["runtime"]
    if len(run_times) == 0:
        movie.run_times = None
    else:
        movie.run_times = run_times[0]

    year = json_data[0]["year"]
    if len(year) > 4:
        year = year[-4:]

    movie.year = year
    key = movie.put()
    actors_list = json_data[0]["actors"]
    directors_list = json_data[0]["directors"]
    writers_list = json_data[0]["writers"]

    retrieve_artists(movie, actors_list, directors_list, writers_list)
    return key


def retrieve_movie_from_id(movie_id):
    """
    Retrieve movie info from IMDB by movie id.
    :param movie_id: original title of the film to retrieve info
    :type movie_id: string
    :return: Movie's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    url = BASE_URL_MYAPIFILMS + 'imdb?idIMDB=' + movie_id + '&format=JSON&aka=1&business=0&seasons=0&seasonYear=0&technical=0&filter=N&exactFilter=0&limit=1&lang=en-us&actors=S&biography=0&trailer=1&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0'

    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    movie = Movie(id=json_data["idIMDB"],
                  plot=json_data["plot"],
                  poster=json_data["urlPoster"],
                  rated=json_data["rated"],
                  simple_plot=json_data["simplePlot"],
                  genres=json_data["genres"])

    try:
        trailer_url = json_data["trailer"]["videoURL"]
        movie.trailer = trailer_url
    except KeyError:
        movie.trailer = None

    movie.original_title = json_data["title"]

    akas = json_data["akas"]
    for aka in akas:
        if aka["country"] == "Italy":
            movie.title = aka["title"]

    run_times = json_data["runtime"]
    if len(run_times) == 0:
        movie.run_times = None
    else:
        movie.run_times = run_times[0]

    year = json_data["year"]
    if len(year) > 4:
        year = year[-4:]

    movie.year = year
    key = movie.put()
    actors_list = json_data["actors"]
    directors_list = json_data["directors"]
    writers_list = json_data["writers"]

    retrieve_artists(movie, actors_list, directors_list, writers_list)
    return key


def retrieve_artists(movie, actors_list, directors_list, writers_list):
    """
    Retrieve all artist in a movie from actors, directors and writers lists.
    :param movie: Movie object in order to add actors, directors and writers
    :type movie: Movie
    :param actors_list: list of actors
    :type actors_list: list of dict
    :param directors_list: list of directors
    :type directors_list: list of dict
    :param writers_list: list of writers
    :type writers_list: list of dict
    """
    for json_data in actors_list:
        actor = Artist(id=json_data["actorId"],
                       name=json_data["actorName"],
                       photo=json_data["urlPhoto"])
        actor.put()
        movie.add_actor(actor)

    for json_data in directors_list:
        director = Artist(id=json_data["nameId"],
                          name=json_data["name"])
        director.put()
        movie.add_director(director)

    for json_data in writers_list:
        writer = Artist(id=json_data["nameId"],
                        name=json_data["name"])
        writer.put()
        movie.add_writer(writer)


def retrieve_artist_from_name(artist_name):
    """
    Retrieve artist info from IMDB by name of artist.
    :param artist_name: name of the artist to retrieve info
    :type artist_name: string
    :return: Artist's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    url = BASE_URL_MYAPIFILMS + 'imdb?name=' + artist_name + '&format=JSON&filmography=0&limit=1&lang=en-us&exactFilter=0&bornDied=0&starSign=0&uniqueName=0&actorActress=0&actorTrivia=0'
    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    if type(json_data) is not list:  # If it is not a list there is a problem
        raise RetrieverError(json_data["code"], json_data["message"])

    print json_data[0]

    artist = Artist(id=json_data[0]["idIMDB"],
                    name=json_data[0]["name"],
                    photo=json_data[0]["urlPhoto"])

    return artist.put()


def retrieve_artist_from_id(artist_id):
    """
    Retrieve artist info from IMDB by id of artist.
    :param artist_id: id of the artist to retrieve info
    :type artist_id: string
    :return: Artist's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    url = BASE_URL_MYAPIFILMS + 'imdb?idName=' + artist_id + '&format=JSON&filmography=0&lang=en-us&bornDied=0&starSign=0&uniqueName=0&actorActress=0&actorTrivia=0&actorPhotos=N&actorVideos=N&salary=0&spouses=0&tradeMark=0&personalQuotes=0'
    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    artist = Artist(id=json_data["idIMDB"],
                    name=json_data["name"],
                    photo=json_data["urlPhoto"])

    return artist.put()