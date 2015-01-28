from datetime import date, timedelta, datetime
from flask import jsonify, request
import logging
import re

from werkzeug.exceptions import BadRequest, MethodNotAllowed, InternalServerError
from IMDB_retriever import retrieve_movie_from_id, retrieve_artist_from_id
from google.appengine.api import memcache
from google.appengine.ext import ndb
from main import json_api
from manage_user import User
from models import Artist, Movie, TasteArtist, TasteMovie, TasteGenre
from models import User as modelUser
from movie_selector import taste_based_movie_selection
from tv_scheduling import result_movies_schedule
from utilities import RetrieverError, time_for_tomorrow, GENRES

app = json_api(__name__)
app.config['DEBUG'] = True


@app.route('/api/schedule/<tv_type>/<day>', methods=['GET'])
def schedule(tv_type, day):
    """
    Returns a JSON containing the TV programming of <tv_type> in the <day>.
    :param tv_type: type of TV from get schedule, possible value (free, sky, premium)
    :type tv_type: string
    :param day: interested day, possible value (today, tomorrow, future)
    :type day: string
    :return: schedule
        {"code": 0, "data": {"day": day, "schedule": [{"channel": channel_name, "movieUrl": url,
        "originalTitle": original_title, "time": time, "title": title}, .. ], "type": tv_type}}
    :rtype: JSON
    """
    if request.method == 'GET':
        return jsonify(code=0, data={"type": tv_type, "day": day, "schedule": result_movies_schedule(tv_type, day)})
    else:
        raise MethodNotAllowed


@app.route('/api/tastes/<user_id>/<type>', methods=['GET', 'POST'])
def tastes(user_id, type):
    """
    Endpoint that allow to list all tastes by type or add a new one.
    :param user_id: email of the user
    :type user_id: string
    :param type: string
    :type type: string
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url}],
        "type": type, "user_id": user_id}
        {"code": 0, "data": {"tastes": [{"genre": genre}],
        "type": type, "user_id": user_id}
    :rtype: JSON
    :raise MethodNotAllowed: if method is neither POST neither GET
    :raise InternalServerError: if user is not subscribed
    :raise BadRequest: if type is neither artist neither movie
    :raise InternalServerError: if there is an error from MYAPIFILMS
    """
    user = modelUser.get_by_id(user_id)  # Get user

    if user is not None:
        if request.method == 'POST':
            if type == 'artist':

                json_data = request.get_json()  # Get JSON from POST

                if json_data is None:
                    raise BadRequest

                id_imdb = json_data['idIMDB']  # Get id
                logging.info("From post: %s", id_imdb)

                artist = get_or_retrieve_by_id(id_imdb)  # Get or retrieve artist

                user.add_taste_artist(artist)  # Add artist to tastes
                return get_tastes_artists_list(user)  # Return tastes
            elif type == 'movie':
                json_data = request.get_json()  # Get JSON from POST

                if json_data is None:
                    raise BadRequest

                id_imdb = json_data['idIMDB']  # Get id
                logging.info("From post: %s", id_imdb)

                movie = get_or_retrieve_by_id(id_imdb)  # Get or retrieve movie

                user.add_taste_movie(movie)  # Add movie to tastes
                return get_tastes_movies_list(user)  # Return tastes
            elif type == 'genre':
                json_data = request.get_json()

                if json_data is None:
                    raise BadRequest

                genre = json_data['genre']
                logging.info("From post: %s", genre)

                user.add_taste_genre(genre)  # Add genre to tastes
                return get_tastes_genres_list(user)  # Return tastes
            else:
                raise BadRequest
        elif request.method == 'GET':
            if type == 'artist':
                return get_tastes_artists_list(user)  # Return artists tastes
            elif type == 'movie':
                return get_tastes_movies_list(user)  # Return movies tastes
            elif type == 'genre':
                return get_tastes_genres_list(user)  # Return genres tastes
            elif type == 'all':
                return get_tastes_list(user)  # Return all tastes
            else:
                raise BadRequest
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/tastes/<user_id>/<type>/<id>', methods=['DELETE'])
def remove_taste(user_id, type, id):
    """
    Endpoint that allow to list all tastes by type or add new one.
    :param user_id: email of the user
    :type user_id: string
    :param type: string
    :type type: string
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"idIMDB": id_IMDB, "originalTitle": original_title, "poster": poster_url}],
        "type": type, "userId": user_id}
    :rtype: JSON
    :raise MethodNotAllowed: if method is neither POST neither GET
    :raise InternalServerError: if user is not subscribed
    :raise BadRequest: if type is neither artist neither movie neither genre or a good one
    :raise InternalServerError: if there is an error from MYAPIFILMS
    """
    user = modelUser.get_by_id(user_id)  # Get user

    logging.info("From get: %s", id)

    if user is not None:
        if request.method == 'DELETE':
            if type == 'artist':
                artist = get_or_retrieve_by_id(id)

                user.remove_taste_artist(artist)  # Remove artist from tastes
                return get_tastes_artists_list(user)  # Return tastes
            elif type == 'movie':
                movie = get_or_retrieve_by_id(id)

                user.remove_taste_movie(movie)  # Remove movie from tastes
                return get_tastes_movies_list(user)  # Return tastes
            elif type == 'genre':
                if id in GENRES:
                    user.remove_taste_genre(id)  # Remove genre from tastes
                    return get_tastes_genres_list(user)  # Return tastes
                else:
                    raise BadRequest
            else:
                raise BadRequest
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/watched/<user_id>', methods=['GET', 'POST'])
def watched(user_id):
    """
    Endpoint that allow to list all watched movies or add a new one.
    :param user_id: email of the user
    :type user_id: string
    :return: list of watched movies
        {"code": 0, "data": {"movies": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url,
        "date": date}],"user_id": user_id}
    :rtype: JSON
    :raise MethodNotAllowed: if method is neither POST neither GET
    :raise InternalServerError: if user is not subscribed
    :raise BadRequest: if type is neither artist neither movie
    :raise InternalServerError: if there is an error from MYAPIFILMS
    """
    user = modelUser.get_by_id(user_id)  # Get user

    if user is not None:
        if request.method == 'POST':

            json_data = request.get_json()  # Get JSON from POST

            if json_data is None:
                raise BadRequest

            id_imdb = json_data['idIMDB']  # Get id
            logging.info("From post: %s", id_imdb)

            movie = get_or_retrieve_by_id(id_imdb)

            yesterday = date.today() - timedelta(days=1)  # Calculate yesterday

            user.add_watched_movie(movie, yesterday)
            return get_watched_movies_list(user)  # Return tastes
        elif request.method == 'GET':
            return get_watched_movies_list(user)  # Return tastes
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/watched/<user_id>/<date>', methods=['GET', 'POST'])
def watched_date(user_id, date):
    """
    Endpoint that allow to list all watched movies or add a new one.
    :param user_id: email of the user
    :type user_id: string
    :param date: date the movie been watched
    :type date: date
    :return: list of watched movies
        {"code": 0, "data": {"movies": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url,
        "date": date}],"user_id": user_id}
    :rtype: JSON
    :raise MethodNotAllowed: if method is neither POST neither GET
    :raise InternalServerError: if user is not subscribed
    :raise BadRequest: if type is neither artist neither movie
    :raise InternalServerError: if there is an error from MYAPIFILMS
    """
    user = modelUser.get_by_id(user_id)  # Get user

    if user is not None:
        if request.method == 'POST':

            json_data = request.get_json()  # Get JSON from POST

            if json_data is None:
                raise BadRequest

            id_imdb = json_data['idIMDB']  # Get id
            logging.info("From post: %s", id_imdb)

            movie = get_or_retrieve_by_id(id_imdb)

            date_object = datetime.strptime(date, '%d-%m-%Y')

            user.add_watched_movie(movie, date_object)
            return get_watched_movies_list(user)  # Return tastes
        elif request.method == 'GET':
            return get_watched_movies_list(user)  # Return tastes
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')

@app.route('/api/subscribe/', methods=['POST'])
def subscribe():
    """
    Subscribe user from App.
    :return: confirmation
        {"code": 0, "data": {"message": "User subscribed successful!", "user_id": user_id}}
    :rtype: JSON
    :raise MethodNotAllowed: if method is neither POST neither GET
    :raise InternalServerError: if user is already subscribed
    """
    if request.method == 'POST':

        json_data = request.get_json()  # Get JSON from POST

        if json_data is None:
            raise BadRequest

        user_id = json_data['userId']  # Get user_id

        user = User(email=user_id)  # Create user

        if user.is_subscribed():
            raise InternalServerError(user_id + ' is already subscribed')
        else:
            user.subscribe(name=json_data['userName'], birth_year=json_data['userBirthYear'],
                           gender=json_data['userGender'])
            return jsonify(code=0, data={"userId": user_id, "message": "User subscribed successful!"})
    else:
        raise MethodNotAllowed


@app.route('/api/unsubscribe/<user_id>', methods=['DELETE'])
def unsubscribe(user_id):
    """
    Unsubscribe user from App.
    :return:
    :raise MethodNotAllowed: if method is neither POST neither GET
    :raise InternalServerError: if user is not subscribed
    """
    if request.method == 'DELETE':

        user = User(email=user_id)  # Create user

        if user is not None:
            if not user.is_subscribed():
                raise InternalServerError(user_id + ' is not subscribed')
            else:
                user.unsubscribe()
                return jsonify(code=0, data={"userId": user_id, "message": "User unsubscribed successful!"})
        else:
            raise InternalServerError(user_id + ' is not subscribed')
    else:
        raise MethodNotAllowed


@app.route('/api/proposal/<user_id>', methods=['GET'])
def proposal(user_id):
    """
    Return the movies proposal for the user.
    :param user_id: email of the user
    :type user_id: string
    :return: list of proposal
        {"code": 0, "data": {"proposal": [{"channel": channel, "id_IMDB": id_IMDB, "original_title": original_title,
        "poster": poster, "simple_plot": simple_plot, "time": time}], "user_id": user_id}}
    :rtype: JSON
    """
    if request.method == 'GET':

        user = modelUser.get_by_id(user_id)  # Get user

        if user is not None:
            proposals = memcache.get("proposal" + user_id)  # Tries to retrieve the proposal from memcache
            if proposals is None:
                proposals = []

                movies = taste_based_movie_selection(user, result_movies_schedule("free", "today"))
                for movie in movies:
                    logging.info("Scelto: %s", (
                        str(movie[0]["originalTitle"]) if movie[0]["originalTitle"] is not None else str(
                            movie[0]["title"])))

                    movie_data_store = Movie.query(ndb.OR(Movie.original_title == movie[0]["originalTitle"],
                                                          Movie.title == movie[0][
                                                              "title"])).get()  # Find movie by title
                    proposals.append({"idIMDB": movie_data_store.key.id(),
                                      "originalTitle": movie[0]["originalTitle"] if movie[0][
                                                                                        "originalTitle"] is not None else
                                      movie[0]["title"],
                                      "poster": movie_data_store.poster,
                                      "title": movie[0]["title"] if movie[0]["title"] is not None else movie[0][
                                          "originalTitle"],
                                      "channel": movie[0]["channel"],
                                      "time": movie[0]["time"],
                                      "runTimes": movie_data_store.run_times,
                                      "simplePlot": movie_data_store.simple_plot,
                                      "italianPlot": movie_data_store.plot_it})

                    if movie_data_store is not None:
                        pass

                memcache.add("proposal" + user_id, proposals, time_for_tomorrow())  # Store proposal in memcache
                logging.info("Added in memcache %s", "proposal" + user_id)
            return jsonify(code=0, data={"userId": user.key.id(), "proposal": proposals})
        else:
            raise InternalServerError(user_id + ' is not subscribed')
    else:
        raise MethodNotAllowed


@app.route('/api/detail/<type>/<id_imdb>', methods=['GET'])
def detail(type, id_imdb):
    """
    Return all details in the datastore of an artist of a movie by id_IMDB.
    :param id_imdb:
    :type id_imdb: string
    :return: detail's object:
        {"code": 0, "data": {"detail": {"name": name, "photo": photo}, "idIMDB": id_IMDB}}
        {"code": 0, "data": {"detail": {"actors": [{"idIMDB": id_imdb, "name": name, "photo":photo}], "countries":
        [country], "directors": [{"idIMDB": id_imdb, "name": name, "photo":photo}], "genres":
        genres, "keywords": [], "original_title": original_title, "plot": plot, "poster": poster, "rated": rated,
        "run_times": run_times, "simple_plot": simple_plot, "title": title, "trailer": trailer, "writers": [id_IMDB],
        "year": year}, "id_IMDB": id_IMDB}}
    :rtype: JSON
    """
    if request.method == 'GET':
        if type == 'artist':
            artist = get_or_retrieve_by_id(id_imdb)
            return jsonify(code=0, data={"idIMDB": id_imdb, "type": "artist", "detail": artist.to_dict})
        elif type == 'movie':
            movie = get_or_retrieve_by_id(id_imdb)
            return jsonify(code=0, data={"idIMDB": id_imdb, "type": "movie", "detail": movie.to_dict})
        else:
            raise BadRequest
    else:
        raise MethodNotAllowed


def get_or_retrieve_by_id(id_imdb):
    """
    This function check if the id is a valid IMDb id and in this case get or retrieve the correct entity.
    :param id_imdb: a valid IMDb id
    :type id_imdb: string
    :return: A model instance
    :rtype Artist or Movie model
    """

    artist = re.compile("nm\d{7}$")
    movie = re.compile("tt\d{7}$")

    if artist.match(id_imdb):  # It is an artist's id
        artist = Artist.get_by_id(id_imdb)  # Find artist by id
        if artist is None:

            try:
                artist_key = retrieve_artist_from_id(id_imdb)  # Retrieve if is not in the datastore
            except RetrieverError as retriever_error:
                raise InternalServerError(retriever_error)

            artist = Artist.get_by_id(artist_key.id())  # Get artist by id

        return artist
    elif movie.match(id_imdb):  # It is a movie's id
        movie = Movie.get_by_id(id_imdb)  # Find movie by id
        if movie is None:

            try:
                movie_key = retrieve_movie_from_id(id_imdb)  # Retrieve if is not in the datastore
            except RetrieverError as retriever_error:
                raise InternalServerError(retriever_error)

            movie = Movie.get_by_id(movie_key.id())  # Get movie by id

        return movie
    else:
        raise InternalServerError(id_imdb + " is not a valid IMDb id")


def get_tastes_artists_list(user):
    """
    Get a readable taste artists list.
    :param user: user
    :type user: Models.User
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"idIMDB": id,"name": name, "photo": photo_url}],
        "type": type, "userId": user_id}
    :rtype: JSON
    """
    tastes_artists_id = user.tastes_artists  # Get all taste_artists' keys

    artists = []

    for taste_artist_id in tastes_artists_id:
        taste_artist = TasteArtist.get_by_id(taste_artist_id.id())  # Get taste

        if taste_artist.taste >= 1 and taste_artist.added:
            artist_id = taste_artist.artist.id()  # Get artist id from taste
            artist = Artist.get_by_id(artist_id)  # Get artist by id

            artists.append({"idIMDB": artist_id, "name": artist.name, "photo": artist.photo})

    return jsonify(code=0, data={"userId": user.key.id(), "type": "artist", "tastes": artists})


def get_tastes_movies_list(user):
    """
    Get a readable taste movies list.
    :param user: user
    :type user: Models.User
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"idIMDB": id,"originalTitle": original_title, "poster": poster_url}],
        "type": type, "userId": user_id}
    :rtype: JSON
    """
    tastes_movies_id = user.tastes_movies

    movies = []

    for taste_movie_id in tastes_movies_id:
        taste_movie = TasteMovie.get_by_id(taste_movie_id.id())  # Get taste
        movie_id = taste_movie.movie.id()  # Get movie id from taste
        movie = Movie.get_by_id(movie_id)  # Get movie by id

        movies.append({"idIMDB": movie_id, "originalTitle": movie.original_title, "poster": movie.poster})

    return jsonify(code=0, data={"userId": user.key.id(), "type": "movie", "tastes": movies})


def get_tastes_genres_list(user):
    """
    Get a readable taste movies list.
    :param user: user
    :type user: Models.User
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"idIMDB": id,"originalTitle": original_title, "poster": poster_url}],
        "type": type, "userId": user_id}
    :rtype: JSON
    """
    tastes_genres_id = user.tastes_genres

    genres = []

    for taste_genre_id in tastes_genres_id:
        taste_genre = TasteGenre.get_by_id(taste_genre_id.id())  # Get taste

        # TODO: not use object, use a simple list
        if taste_genre.taste >= 1 and taste_genre.added:
            genres.append({"genre": taste_genre.genre})

    return jsonify(code=0, data={"userId": user.key.id(), "type": "genre", "tastes": genres})


def get_tastes_list(user):
    """
    Get a readable taste artists list.
    :param user: user
    :type user: Models.User
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"idIMDB": id,"originalTitle": original_title, "poster": poster_url}],
        "type": type, "userId": user_id}
    :rtype: JSON
    """
    tastes_artists_id = user.tastes_artists  # Get all taste_artists' keys

    artists = []

    for taste_artist_id in tastes_artists_id:
        taste_artist = TasteArtist.get_by_id(taste_artist_id.id())  # Get taste

        if taste_artist.taste >= 1 and taste_artist.added:
            artist_id = taste_artist.artist.id()  # Get artist id from taste
            artist = Artist.get_by_id(artist_id)  # Get artist by id

            artists.append({"idIMDB": artist_id, "name": artist.name, "photo": artist.photo})

    tastes_movies_id = user.tastes_movies

    movies = []

    for taste_movie_id in tastes_movies_id:
        taste_movie = TasteMovie.get_by_id(taste_movie_id.id())  # Get taste
        movie_id = taste_movie.movie.id()  # Get movie id from taste
        movie = Movie.get_by_id(movie_id)  # Get movie by id

        movies.append({"idIMDB": movie_id,
                       "originalTitle": movie.original_title,
                       "title": movie.title,
                       "poster": movie.poster})

    return jsonify(code=0,
                   data={"userId": user.key.id(), "type": "all", "tastes": {"artists": artists, "movies": movies}})


def get_watched_movies_list(user):
    """
    Get a readable watched movie list.
    :param user: user
    :type user: Models.User
    :return: list of watched movies
        {"code": 0, "data": {"movies": [{"idIMDB": id,"originalTitle": original_title, "poster": poster_url,
        "date": date}],"userId": user_id}
    :rtype: JSON
    """
    watched_movies_id = user.watched_movies  # Get all taste_artists' keys

    movies = []

    for i in range(0, len(watched_movies_id)):
        watched_movie_id = watched_movies_id[i].id()
        watched_movie = Movie.get_by_id(watched_movie_id)  # Get movie

        date_watched_movie = user.date_watched[i]  # Get date

        taste_movie = TasteMovie.get_by_id(watched_movie_id + user.key.id())  # Get taste

        movies.append({"idIMDB": watched_movie.key.id(),
                       "originalTitle": watched_movie.original_title,
                       "title": watched_movie.title,
                       "poster": watched_movie.poster,
                       "date": date_watched_movie.strftime('%d-%m-%Y'),
                       "tasted": 1 if taste_movie is not None else 0})

    return jsonify(code=0, data={"userId": user.key.id(), "watched": movies})
