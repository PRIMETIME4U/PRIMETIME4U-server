import json
import logging
import lxml
from google.appengine.api import memcache
from models import Movie, Artist, TasteMovie, TasteArtist, TasteGenre
from utilities import get, RetrieverError, BASE_URL_MYAPIFILMS, GENRES, clear_url


def retrieve_movie_from_title(movie_original_title, movie_director, movie_cast, movie_title=None, movie_url=None,
                              movie_year=None, movie_genre=None):
    """
    Retrieve movie info from IMDB by movie title.
    :param movie_title: title of the film to retrieve info
    :type movie_title: string
    :param movie_original_title: original title of the film to retrieve info
    :type movie_original_title: string
    :param movie_director: director of the film to retrieve info
    :type movie_director: string
    :param movie_genre: genre of the film to retrieve info
    :type movie_genre: string
    :return: Movie's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    logging.info('Retrieving %s', movie_original_title)

    url = BASE_URL_MYAPIFILMS + 'imdb?title=' + movie_original_title + '&format=JSON&aka=0&business=0&seasons=0&seasonYear=' + movie_year + '&technical=0&filter=M&exactFilter=0&limit=1&lang=en-us&actors=S&biography=0&trailer=1&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0&token=307cccfe-d20b-4b69-b976-d6a024538864'
    logging.info('Url My API Films: %s', url)

    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    if type(json_data) is not list:  # If it is not a list there is a problem
        logging.info('Movie not found in IMDB.')
        for x in range(26, len(movie_url)):
            if movie_url[x] == "/":
                end = x
                break

        movie_id = movie_url[26: end]
        movie = Movie(id=movie_id,
                      year=movie_year,
                      original_title=movie_original_title,
                      title=movie_title,
                      genres=[movie_genre])

        actors_string = movie_cast
        directors_list = movie_director
        writers_list = []
        #print actors_string

        actors_list = []
        begin = 0
        count = 0
        for i in actors_string:
            count += 1
            if i == "," or count == len(actors_string) - 1:
                actors_list.append(actors_string[begin:count - 1])
                begin = count + 1
                search_artist_from_name(actors_list[len(actors_list) - 1], movie)

        for director_name in directors_list:
            search_artist_from_name(actors_list[len(actors_list) - 1], movie, director_name)

        html_page_plot = get(movie_url).encode('utf-8')
        tree = lxml.html.fromstring(html_page_plot)
        try:
            movie.plot_it = tree.xpath('//article[@class="scheda-desc"]/p/text()')[0]
        except IndexError:
            logging.error('Impossible to retrieve info from FilmTV')
            pass
        movie.put()
    else:
        directors_list = json_data[0]['directors']
        #print movie_director
        #prova = directors_list[0]['name'].encode('utf-8')
        #print prova
        if (movie_director in directors_list[0]['name'].encode('utf-8')) or (directors_list[0]['name'].encode('utf-8') in movie_director):
            movie = Movie(id=json_data[0]['idIMDB'],
                          plot=json_data[0]['plot'],
                          poster=clear_url(json_data[0]['urlPoster']),
                          rated=json_data[0]['rated'],
                          simple_plot=json_data[0]['simplePlot'],
                          genres=json_data[0]['genres'])
            try:
                trailer_url = json_data[0]['trailer']['videoURL']
                movie.trailer = trailer_url
            except KeyError:
                movie.trailer = None

            movie.title = movie_title
            movie.original_title = movie_original_title

            run_times = json_data[0]['runtime']
            if len(run_times) == 0:
                movie.run_times = None
            else:
                movie.run_times = run_times[0]

            year = json_data[0]['year']
            if len(year) > 4:
                year = year[-4:]
            movie.year = year

            actors_list = json_data[0]['actors']
            writers_list = json_data[0]['writers']

            retrieve_artists(movie, actors_list, directors_list, writers_list)

            logging.info('Url FilmTV: %s', movie_url)

            html_page_plot = get(movie_url).encode('utf-8')
            tree = lxml.html.fromstring(html_page_plot)
            try:
                movie.plot_it = tree.xpath('//article[@class="scheda-desc"]/p/text()')[0]

            except IndexError:
                logging.error('Impossible to retrieve info from FilmTV')
                pass
            movie.put()
        else:
            logging.info("FilmTV movie is not the same with retrieved movie in IMDB!")
            for x in range(26, len(movie_url)):
                if movie_url[x] == "/":
                    end = x
                    break

            movie_id = movie_url[26: end]
            #print movie_id
            movie = Movie(id=movie_id,
                          genres=[movie_genre],
                          year=movie_year,
                          original_title=movie_original_title,
                          title=movie_title)

            actors_string = movie_cast
            directors_list = movie_director
            writers_list = []
            #print actors_string

            actors_list = []
            begin = 0
            count = 0
            if actors_string is not None:
                for i in actors_string:
                    count += 1
                    if i == "," or count == len(actors_string) - 1:
                        actors_list.append(actors_string[begin:count - 1])
                        begin = count + 1
                        search_artist_from_name(actors_list[len(actors_list) - 1], movie)
            if directors_list is not None:
                for director_name in directors_list:
                    search_artist_from_name(actors_list[len(actors_list) - 1], movie, director_name)

            html_page_plot = get(movie_url).encode('utf-8')
            tree = lxml.html.fromstring(html_page_plot)
            try:
                movie.plot_it = tree.xpath('//article[@class="scheda-desc"]/p/text()')[0]
            except IndexError:
                logging.error('Impossible to retrieve info from FilmTV')
                pass

    key = movie.put()
    logging.info('Retrieved %s', movie_original_title)

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
    logging.info('Retrieving %s', movie_id)

    url = BASE_URL_MYAPIFILMS + 'imdb?idIMDB=' + movie_id + '&format=JSON&aka=1&business=0&seasons=0&seasonYear=0&technical=0&filter=N&exactFilter=0&limit=1&lang=en-us&actors=S&biography=0&trailer=1&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0&token=307cccfe-d20b-4b69-b976-d6a024538864'

    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    movie = Movie(id=json_data['idIMDB'],
                  plot=json_data['plot'],
                  poster=clear_url(json_data['urlPoster']) if ('urlPoster' in json_data and json_data['urlPoster'] != "") else None,
                  rated=json_data['rated'],
                  simple_plot=json_data['simplePlot'],
                  genres=json_data['genres'])

    try:
        trailer_url = json_data['trailer']['videoURL']
        movie.trailer = trailer_url
    except KeyError:
        movie.trailer = None

    movie.original_title = json_data['title']

    akas = json_data['akas']
    for aka in akas:
        if aka['country'] == 'Italy':
            movie.title = aka['title']

    run_times = json_data['runtime']
    if len(run_times) == 0:
        movie.run_times = None
    else:
        movie.run_times = run_times[0]

    year = json_data['year']
    if len(year) > 4:
        year = year[-4:]

    movie.year = year
    key = movie.put()
    actors_list = json_data['actors']
    directors_list = json_data['directors']
    writers_list = json_data['writers']

    retrieve_artists(movie, actors_list, directors_list, writers_list)

    logging.info('Retrieved %s', movie_id)
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
        actor = Artist(id=json_data['actorId'],
                       name=json_data['actorName'],
                       photo=clear_url(json_data['urlPhoto']))
        actor.put()
        movie.add_actor(actor)

    for json_data in directors_list:
        director = Artist(id=json_data['nameId'],
                          name=json_data['name'])
        director.put()
        movie.add_director(director)

    for json_data in writers_list:
        writer = Artist(id=json_data['nameId'],
                        name=json_data['name'])
        writer.put()
        movie.add_writer(writer)


def search_artist_from_name(artist_name, movie=None, director_name=None):
    """
    Retrieve artist info from IMDB by name of artist.
    :param artist_name: name of the actor to retrieve info
    :type artist_name: string
    :return: Actor's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """

    url = BASE_URL_MYAPIFILMS + 'imdb?name=' + artist_name + '&format=JSON&filmography=0&limit=1&lang=en-us&exactFilter=0&bornDied=0&starSign=0&uniqueName=0&actorActress=0&actorTrivia=0&token=307cccfe-d20b-4b69-b976-d6a024538864'
    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)
    if type(json_data) is not list:  # If it is not a list there is a problem
        raise RetrieverError(json_data['code'], json_data['message'])

    try:
        photo = clear_url(json_data[0]['urlPhoto'])
    except Exception:
        logging.info("Photo not found")
        photo = "None"

    artist = Artist(id=json_data[0]['idIMDB'],
                    name=json_data[0]['name'],
                    photo=photo)

    if movie is not None:
        if director_name is not None:
            movie.add_director(artist)
        else:
            movie.add_actor(artist)

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
    logging.info('Retrieving %s', artist_id)

    url = BASE_URL_MYAPIFILMS + 'imdb?idName=' + artist_id + '&format=JSON&filmography=0&lang=en-us&bornDied=0&starSign=0&uniqueName=0&actorActress=0&actorTrivia=0&actorPhotos=N&actorVideos=N&salary=0&spouses=0&tradeMark=0&personalQuotes=0&token=307cccfe-d20b-4b69-b976-d6a024538864'
    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    artist = Artist(id=json_data["idIMDB"],
                    name=json_data["name"],
                    photo=clear_url(json_data["urlPhoto"]) if ('urlPhoto' in json_data and json_data['urlPhoto'] != "") else None)

    return artist.put()


def retrieve_suggest_list(user, query):

    json_page = memcache.get(query.lower())
    if json_page is None:
        url = 'http://sg.media-imdb.com/suggests/' + query[0] + '/' + query + '.json'
        json_page = get(url).encode('utf-8')
        memcache.add(query, json_page)

    value = 'imdb$' + query

    movies = []
    artists = []
    genres = []

    try:
        json_data = json.loads(json_page[len(value)+1:-1])

        data = json_data['d']

        for elem in data:
            if not elem['id'].startswith('http://'):
                if 'q' in elem:
                    if elem['q'] == "feature":
                        try:
                            idIMDB = elem['id']
                            taste_movie = TasteMovie.get_by_id(idIMDB + user.key.id())  # Get taste
                            movies.append({"originalTitle": elem['l'].encode('utf-8') if elem['l'] is not None else None,
                                           "title": None,
                                           "idIMDB": idIMDB,
                                           "poster": clear_url(elem['i'][0]) if 'i' in elem else 'null',
                                           "year": str(elem['y']),
                                           "tasted": 1 if (taste_movie is not None and taste_movie.added) else 0})
                        except KeyError as err:
                            logging.error("Error in the JSON: %s", err)
                else:
                    try:
                        idIMDB = elem['id']
                        taste_artist = TasteArtist.get_by_id(idIMDB + user.key.id())
                        artists.append({"name": elem['l'].encode('utf-8') if elem['l'] is not None else None,
                                        "idIMDB": elem['id'],
                                        "photo": clear_url(elem['i'][0]) if 'i' in elem else 'null',
                                        "tasted": 1 if (taste_artist is not None and taste_artist.added) else 0})
                    except KeyError as err:
                        logging.error("Error in the JSON: %s", err)
            else:
                logging.info("Error the element is a link: %s", elem['id'])
    except ValueError:
        pass

    [genres.append({"name": genre, "tasted": 1 if (TasteGenre.get_by_id(genre + user.key.id()) is not None and (TasteGenre.get_by_id(genre + user.key.id())).added) else 0}) for genre in GENRES if genre.lower().startswith(query.lower())]

    return {"query": query, "movies": movies, "artists": artists, "genres": genres}


def retrieve_search_result_list(user, query):

    movies_page = memcache.get("movies" + query.lower())
    if movies_page is None:
        movies_page = get(BASE_URL_MYAPIFILMS + 'imdb?title=' + query + '&format=JSON&aka=0&business=0&seasons=0&seasonYear=0&technical=0&filter=M&exactFilter=0&limit=5&lang=it-it&actors=N&biography=0&trailer=0&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0&moviePhotos=N&movieVideos=N&token=307cccfe-d20b-4b69-b976-d6a024538864').encode('utf-8')
        memcache.add("movies" + query.lower(), movies_page)

    artists_page = memcache.get("artists" + query.lower())
    if artists_page is None:
        artists_page = get(BASE_URL_MYAPIFILMS + 'imdb?name=' + query + '&format=JSON&filmography=0&limit=5&lang=it-it&exactFilter=0&bornDied=0&starSign=0&uniqueName=0&actorActress=0&actorTrivia=0&actorPhotos=N&actorVideos=N&salary=0&spouses=0&tradeMark=0&personalQuotes=0&token=307cccfe-d20b-4b69-b976-d6a024538864').encode('utf-8')
        memcache.add("artists" + query, artists_page)

    movies = []
    artists = []
    genres = []

    try:
        json_data = json.loads(movies_page)
        print json_data
        if type(json_data) is list:  # If it is not a list there is a problem

            for elem in json_data:
                idIMDB = elem['idIMDB']
                taste_movie = TasteMovie.get_by_id(idIMDB + user.key.id())  # Get taste
                movies.append({"title": elem['title'].encode('utf-8') if elem['title'] != "" else elem['originalTitle'].encode('utf-8'),
                               "originalTitle": elem['originalTitle'].encode('utf-8') if elem['originalTitle'] != "" else elem['title'].encode('utf-8'),
                               "idIMDB": idIMDB,
                               "poster": clear_url(elem['urlPoster']) if ('urlPoster' in elem and elem['urlPoster'] != "") else None,
                               "year": str(elem['year']),
                               "tasted": 1 if (taste_movie is not None and taste_movie.added) else 0})
    except ValueError:
        pass

    try:
        json_data = json.loads(artists_page)
        print json_data
        if type(json_data) is list:  # If it is not a list there is a problem

            for elem in json_data:
                idIMDB = elem['idIMDB']
                taste_artist = TasteArtist.get_by_id(idIMDB + user.key.id())
                artists.append({"name": elem['name'].encode('utf-8') if elem['name'] != "" else None,
                                "idIMDB": idIMDB,
                                "photo": clear_url(elem['urlPhoto']) if ('urlPhoto' in elem and elem['urlPhoto'] != "") else None,
                                "tasted": 1 if (taste_artist is not None and taste_artist.added) else 0})
    except ValueError:
        pass

    [genres.append({"name": genre, "tasted": 1 if (TasteGenre.get_by_id(genre + user.key.id()) is not None and (TasteGenre.get_by_id(genre + user.key.id())).added) else 0}) for genre in GENRES if genre.lower().startswith(query)]

    return {"query": query, "movies": movies, "artists": artists, "genres": genres}

'''
# TODO: next to be finished
def retrieve_movie_title_from_id(movie_id, language):
    """
    Retrieve movie info from IMDB by movie id.
    :param movie_id: original title of the film to retrieve info
    :type movie_id: string
    :return: Movie's key
    :rtype: ndb.Key
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    logging.info('Retrieving %s', movie_id)

    url = BASE_URL_MYAPIFILMS + 'imdb?idIMDB=' + movie_id + '&format=JSON&aka=1&business=0&seasons=0&seasonYear=0&technical=0&filter=N&exactFilter=0&limit=1&lang=en-us&actors=S&biography=0&trailer=0&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0'

    json_page = get(url).encode('utf-8')
    json_data = json.loads(json_page)

    movie = Movie(id=json_data['idIMDB'],
                  plot=json_data['plot'],
                  poster=clear_url(json_data['urlPoster']) if ('urlPoster' in json_data and json_data['urlPoster'] != "") else None,
                  rated=json_data['rated'],
                  simple_plot=json_data['simplePlot'],
                  genres=json_data['genres'])

    movie.original_title = json_data['title']

    akas = json_data['akas']
    for aka in akas:
        if aka['country'] == 'Italy':
            movie.title = aka['title']

    return key
'''
