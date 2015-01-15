from datetime import date, timedelta
from flask import jsonify, request

from werkzeug.exceptions import BadRequest, MethodNotAllowed, InternalServerError
from IMDB_retriever import retrieve_movie_from_title, retrieve_artist_from_name, retrieve_movie_from_id, \
    retrieve_artist_from_id
from google.appengine.api import memcache
from main import json_api
from manage_user import User
from models import Artist, Movie, TasteArtist, TasteMovie
from models import User as modelUser
from movie_selector import random_movie_selection
from tv_scheduling import result_movies_schedule
from utilities import RetrieverError, NUMBER_SUGGESTIONS, time_for_tomorrow

app = json_api(__name__)
app.config['DEBUG'] = True


@app.route('/api/schedule/<tv_type>/<day>')
def schedule(tv_type, day):
    """
    Returns a JSON containing the TV programming of <tv_type> in the <day>.
    :param tv_type: type of TV from get schedule, possible value (free, sky, premium)
    :type tv_type: string
    :param day: interested day, possible value (today, tomorrow, future)
    :type day: string
    :return: schedule
        {"code": 0, "data": { "day": day, "schedule": [{"channel": channel_name, "originalTitle": original_title,
        "time": time, "title": title}, .. ], "type": tv_type}}
    :rtype: JSON
    """
    return jsonify(code=0, data={"type": tv_type, "day": day, "schedule": result_movies_schedule(tv_type, day)})


@app.route('/api/tastes/<user_id>/<type>', methods=['GET', 'POST'])
def add_tastes(user_id, type):
    """
    Endpoint that allow to list all tastes by type or add new one.
    :param user_id: email of the user
    :type user_id: string
    :param type: string
    :type type: string
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url}],
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
                artist_name = request.form['artist_name']  # Get artist_name from POST

                artist = Artist.query(Artist.name == artist_name).get()  # Find artist by name
                if artist is None:
                    try:
                        artist_key = retrieve_artist_from_name(artist_name)  # Retrieve if is not in the datastore
                    except RetrieverError as retriever_error:
                        raise InternalServerError(retriever_error)
                    artist = Artist.get_by_id(artist_key.id())

                user.add_taste_artist(artist)  # Add artist to tastes
                return get_tastes_artists_list(user)  # Return tastes
            elif type == 'movie':
                movie_original_title = request.form['movie_title']  # Get movie_title from POST

                movie = Movie.query(Movie.original_title == movie_original_title).get()  # Find movie by original title
                if movie is None:
                    try:
                        movie_key = retrieve_movie_from_title(
                            movie_original_title)  # Retrieve if is not in the datastore
                    except RetrieverError as retriever_error:
                        raise InternalServerError(retriever_error)
                    movie = Movie.get_by_id(movie_key.id())

                user.add_taste_movie(movie)  # Add movie to tastes
                return get_tastes_movies_list(user)  # Return tastes
            else:
                raise BadRequest
        elif request.method == 'GET':
            if type == 'artist':
                return get_tastes_artists_list(user)  # Return tastes
            elif type == 'movie':
                return get_tastes_movies_list(user)  # Return tastes
            else:
                raise BadRequest
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/tastes/<user_id>/<type>/<id_imdb>', methods=['DELETE'])
def remove_taste(user_id, type, id_imdb):
    """
    Endpoint that allow to list all tastes by type or add new one.
    :param user_id: email of the user
    :type user_id: string
    :param type: string
    :type type: string
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url}],
        "type": type, "user_id": user_id}
    :rtype: JSON
    :raise MethodNotAllowed: if method is neither POST neither GET
    :raise InternalServerError: if user is not subscribed
    :raise BadRequest: if type is neither artist neither movie
    :raise InternalServerError: if there is an error from MYAPIFILMS
    """
    user = modelUser.get_by_id(user_id)  # Get user

    if user is not None:
        if request.method == 'DELETE':
            if type == 'artist':
                artist = Artist.get_by_id(id_imdb)

                user.remove_taste_artist(artist)  # Remove artist to tastes
                return get_tastes_artists_list(user)  # Return tastes
            elif type == 'movie':
                movie = Movie.get_by_id(id_imdb)

                user.remove_taste_movie(movie)  # Remove movie to tastes
                return get_tastes_movies_list(user)  # Return tastes
            else:
                raise BadRequest
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/watched/<user_id>', methods=['GET', 'POST'])
def watched(user_id):
    """
    Endpoint that allow to list all watched movies.
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
            movie_original_title = request.form['movie_title']  # Get movie_title from POST

            movie = Movie.query(Movie.original_title == movie_original_title).get()  # Find movie by original title
            if movie is None:
                try:
                    movie_key = retrieve_movie_from_title(
                        movie_original_title)  # Retrieve if is not in the datastore
                except RetrieverError as retriever_error:
                    raise InternalServerError(retriever_error)
                movie = Movie.get_by_id(movie_key.id())

            yesterday = date.today() - timedelta(days=1)

            user.add_watched_movie(movie, yesterday)
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
        user_id = json_data['user_id']  # Get user_id

        user = User(email=user_id)  # Create user

        if user.is_subscribed():
            raise InternalServerError(user_id + ' is already subscribed')
        else:
            user.subscribe(name=json_data['user_name'], birth_year=json_data['user_birth_year'],
                           gender=json_data['user_gender'])
            return jsonify(code=0, data={"user_id": user_id, "message": "User subscribed successful!"})
    else:
        raise MethodNotAllowed


@app.route('/api/unsubscribe/', methods=['POST'])
def unsubscribe():
    """
    Unsubscribe user from App.
    :return:
    :raise MethodNotAllowed: if method is neither POST neither GET
    :raise InternalServerError: if user is not subscribed
    """
    if request.method == 'POST':
        user_id = request.form['user_id']  # Get user_id from POST

        user = User(email=user_id)  # Create user

        if not user.is_subscribed():
            raise InternalServerError(user_id + ' is not subscribed')
        else:
            user.unsubscribe()
            return jsonify(code=0, data={"user_id": user_id, "message": "User unsubscribed successful!"})
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

                for i in range(0, NUMBER_SUGGESTIONS):
                    movie = random_movie_selection(result_movies_schedule("free", "today"))

                    movie_data_store = Movie.query(
                        Movie.original_title == movie["originalTitle"]).get()  # Find movie by original title

                    if movie_data_store is not None:
                        proposals.append({"id_IMDB": movie_data_store.key.id(),
                                          "original_title": movie["originalTitle"] if movie["originalTitle"] is not None
                                          else movie["title"], "poster": movie_data_store.poster,
                                          "channel": movie["channel"],
                                          "time": movie["time"],
                                          "simple_plot": movie_data_store.simple_plot})

                if len(proposals) == 0:
                    raise InternalServerError("Programmazione di oggi ancora non disponibile")

                memcache.add("proposal" + user_id, proposals, time_for_tomorrow())  # Store proposal in memcache
            return jsonify(code=0, data={"user_id": user.key.id(), "proposal": proposals})
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
        {"code": 0, "data": {"detail": {"name": name, "photo": photo}, "id_IMDB": id_IMDB}}
        {"code": 0, "data": {"detail": {"actors": [id_IMDB], "countries": [country], "directors": [id_IMDB], "genres":
        [genre], "keywords": [], "original_title": original_title, "plot": plot, "poster": poster, "rated": rated,
        "run_times": run_times, "simple_plot": simple_plot, "title": title, "trailer": trailer, "writers": [id_IMDB],
        "year": year}, "id_IMDB": id_IMDB}}
    :rtype: JSON
    """
    if request.method == 'GET':
        if type == 'artist':
            artist = Artist.get_by_id(id_imdb)  # Get movie

            if artist is None:
                try:
                    artist_key = retrieve_artist_from_id(id_imdb)  # Retrieve if is not in the datastore
                except RetrieverError as retriever_error:
                    raise InternalServerError(retriever_error)

                artist = Artist.get_by_id(artist_key.id())
            return jsonify(code=0, data={"id_IMDB": id_imdb, "type": "artist", "detail": artist.to_dict})
        elif type == 'movie':
            movie = Movie.get_by_id(id_imdb)  # Get movie

            if movie is None:
                try:
                    artist_key = retrieve_movie_from_id(id_imdb)  # Retrieve if is not in the datastore
                except RetrieverError as retriever_error:
                    raise InternalServerError(retriever_error)

                movie = Movie.get_by_id(artist_key.id())
            return jsonify(code=0, data={"id_IMDB": id_imdb, "type": "movie", "detail": movie.to_dict})
        else:
            raise BadRequest
    else:
        raise MethodNotAllowed


def get_tastes_artists_list(user):
    """
    Get a readable taste artists list.
    :param user: user
    :type user: Models.User
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url}],
        "type": type, "user_id": user_id}
    :rtype: JSON
    """
    tastes_artists_id = user.tastes_artists  # Get all taste_artists' keys

    artists = []

    for taste_artist_id in tastes_artists_id:
        taste_artist = TasteArtist.get_by_id(taste_artist_id.id())  # Get taste
        artist_id = taste_artist.id_IMDB.id()  # Get artist id from taste
        artist = Artist.get_by_id(artist_id)  # Get artist by id

        artists.append({"id_IMDB": artist_id, "name": artist.name, "photo": artist.photo})

    return jsonify(code=0, data={"user_id": user.key.id(), "type": "artist", "tastes": artists})


def get_tastes_movies_list(user):
    """
    Get a readable taste movies list.
    :param user: user
    :type user: Models.User
    :return: list of tastes
        {"code": 0, "data": {"tastes": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url}],
        "type": type, "user_id": user_id}
    :rtype: JSON
    """
    tastes_movies_id = user.tastes_movies

    movies = []

    for taste_movie_id in tastes_movies_id:
        taste_movie = TasteMovie.get_by_id(taste_movie_id.id())  # Get taste
        movie_id = taste_movie.id_IMDB.id()  # Get movie id from taste
        movie = Movie.get_by_id(movie_id)  # Get movie by id

        movies.append({"id_IMDB": movie_id, "original_title": movie.original_title, "poster": movie.poster})

    return jsonify(code=0, data={"user_id": user.key.id(), "type": "movie", "tastes": movies})


def get_watched_movies_list(user):
    """
    Get a readable watched movie list.
    :param user: user
    :type user: Models.User
    :return: list of watched movies
        {"code": 0, "data": {"movies": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url,
        "date": date}],"user_id": user_id}
    :rtype: JSON
    """
    watched_movies_id = user.watched_movies  # Get all taste_artists' keys

    movies = []

    for i in range(0, len(watched_movies_id)):
        watched_movie = Movie.get_by_id(watched_movies_id[i].id())  # Get movie

        date_watched_movie = user.date_watched[i]  # Get date

        movies.append({"id_IMDB": watched_movie.key.id(), "original_title": watched_movie.original_title,
                       "poster": watched_movie.poster, "date": date_watched_movie.strftime('%d %B %Y')})

    return jsonify(code=0, data={"user_id": user.key.id(), "watched": movies})
