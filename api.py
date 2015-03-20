from datetime import datetime
from flask import jsonify, request
import logging
import re

from werkzeug.exceptions import BadRequest, MethodNotAllowed, InternalServerError
from IMDB_retriever import retrieve_movie_from_id, retrieve_artist_from_id, retrieve_suggest_list, \
    retrieve_search_result_list
from google.appengine.ext import ndb
from main import json_api
from manage_user import User
from models import Artist, Movie, TasteArtist, TasteMovie, TasteGenre
from models import User as modelUser
from movie_selector import taste_based_movie_selection
from tv_scheduling import result_movies_schedule, result_movies_schedule_list
from utilities import RetrieverError, GENRES, clear_url, channel_number

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
    Endpoint that allow to list all tastes by type (first page) or add a new one.
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

                id_imdb = json_data['data']  # Get id
                logging.info("From post: %s", id_imdb)

                artist = get_or_retrieve_by_id(id_imdb)  # Get or retrieve artist

                user.add_taste_artist(artist)  # Add artist to tastes
                artists_page = generate_artists(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "artist", "tastes": artists_page["artists"],
                                 "next_page": artists_page["next_page"]})  # Return artists tastes
            elif type == 'movie':
                json_data = request.get_json()  # Get JSON from POST

                if json_data is None:
                    raise BadRequest

                id_imdb = json_data['data']  # Get id
                logging.info("From post: %s", id_imdb)

                movie = get_or_retrieve_by_id(id_imdb)  # Get or retrieve movie
                user.add_taste_movie(movie)  # Add movie to tastes
                movies_page = generate_movies(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "movie", "tastes": movies_page["movies"],
                                 "next_page": movies_page["next_page"]})
            elif type == 'genre':
                json_data = request.get_json()

                if json_data is None:
                    raise BadRequest

                genre = json_data['data']
                logging.info("From post: %s", genre)

                user.add_taste_genre(genre)  # Add genre to tastes
                genres_page = generate_genres(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "genre", "tastes": genres_page["genres"],
                                 "next_page": genres_page["next_page"]}) # Return genres tastes
            else:
                raise BadRequest

        elif request.method == 'GET':
            if type == 'artist':
                artists_page = generate_artists(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "artist", "tastes": artists_page["artists"],
                                 "next_page": artists_page["next_page"]})  # Return artists tastes

            elif type == 'movie':
                movies_page = generate_movies(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "movie", "tastes": movies_page["movies"],
                                 "next_page": movies_page["next_page"]})

            elif type == 'genre':
                genres_page = generate_genres(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "genre", "tastes": genres_page["genres"],
                                 "next_page": genres_page["next_page"]}) # Return genres tastes
            elif type == 'all':
                artists_page = generate_artists(user)
                movie_page = generate_movies(user)
                genres_page = generate_genres(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "all",
                                             "tastes": {"artists": artists_page["artists"],
                                            "next_page_artists": artists_page["next_page"],
                                            "movies": movie_page["movies"], "next_page_movies": movie_page["next_page"],
                                            "genres": genres_page["genres"],
                                            "next_page_genres": genres_page["next_page"]}})
            else:
                raise BadRequest
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/tastes/<user_id>/<type>/<page>', methods=['GET'])
def tastes_page(user_id, type, page):
    """
    Endpoint that allow to list all tastes by type (by page) or add a new one.
    :param user_id: email of the user
    :type user_id: string
    :param type: string
    :type type: string
    :param page: number of page
    :type page:
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
        if request.method == 'GET':
            if type == 'artist':
                artists_page = generate_artists(user, int(page))

                return jsonify(code=0, data={"userId": user.key.id(), "type": "artist", "tastes": artists_page["artists"],
                                 "next_page": artists_page["next_page"]})  # Returns artists tastes

            elif type == 'movie':
                movies_page = generate_movies(user, int(page))

                return jsonify(code=0, data={"userId": user.key.id(), "type": "movie", "tastes": movies_page["movies"],
                                 "next_page": movies_page["next_page"]})  # Returns movies tastes

            elif type == 'genre':
                genres_page = generate_genres(user, int(page))

                return jsonify(code=0, data={"userId": user.key.id(), "type": "genre", "tastes": genres_page["genres"],
                                 "next_page": genres_page["next_page"]})  # Returns genres tastes
            else:
                raise BadRequest
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/untaste/<user_id>', methods=['POST'])
def untaste(user_id):
    # TODO: rewrite description
    """
    Endpoint that allow to list all tastes by type (first page) or add a new one.
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

            json_data = request.get_json()  # Get JSON from POST

            if json_data is None:
                raise BadRequest

            id_imdb = json_data['data']  # Get id
            logging.info("From post: %s, untaste", id_imdb)

            movie = get_or_retrieve_by_id(id_imdb)  # Get or retrieve movie
            user.add_taste_movie(movie, -1)  # Add movie to tastes

            return jsonify(data="OK")

        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/tastes/<user_id>/<type>/<data>', methods=['DELETE'])
def remove_taste(user_id, type, data):
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

    logging.info("From get: %s", data)

    if user is not None:
        if request.method == 'DELETE':
            if type == 'artist':
                artist = get_or_retrieve_by_id(data)

                user.remove_taste_artist(artist)  # Remove artist from tastes
                artists_page = generate_artists(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "artist", "tastes": artists_page["artists"],
                                 "next_page": artists_page["next_page"]})  # Return artists tastes
            elif type == 'movie':
                movie = get_or_retrieve_by_id(data)
                user.remove_taste_movie(movie)  # Remove movie from tastes
                movies_page = generate_movies(user)

                return jsonify(code=0, data={"userId": user.key.id(), "type": "movie", "tastes": movies_page["movies"],
                                 "next_page": movies_page["next_page"]})
            elif type == 'genre':
                if data in GENRES:
                    user.remove_taste_genre(data)  # Remove genre from tastes
                    genres_page = generate_genres(user)

                    return jsonify(code=0, data={"userId": user.key.id(), "type": "movie", "tastes": genres_page["genres"],
                                 "next_page": genres_page["next_page"]})  # Return genres tastes
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
    Endpoint that allow to list all watched movies (first page) or add a new one.
    :param user_id: email of the user
    :type user_id: string
    :return: list of watched movies
        {"code": 0, "data": {"movies": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url,
        "date": date}],"user_id": user_id, "prevPage": prevPage, "nextPage": nextPage}
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
            date = json_data['date']  # Get date
            logging.info("From post: %s %s", id_imdb, date)

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


@app.route('/api/watched/<user_id>/<page>', methods=['GET'])
def watched_page(user_id, page):
    """
    Endpoint that allow to list all watched movies listed by pages, the FIRST PAGE is 0. It uses pagination.
    :param user_id: email of the user
    :type user_id: string
    :param page: page to send
    :type page: integer
    :return: list of watched movies by page
        {"code": 0, "data": {"movies": [{"id_IMDB": id,"original_title": original_title, "poster": poster_url,
        "date": date}],"user_id": user_id, "prevPage": prevPage, "nextPage": nextPage}
    :rtype: JSON
    :raise MethodNotAllowed: if method is not GET
    :raise InternalServerError: if user is not subscribed
    :raise BadRequest: if type is neither artist neither movie
    :raise InternalServerError: if there is an error from MYAPIFILMS
    """
    user = modelUser.get_by_id(user_id)  # Get user

    if user is not None:
        if request.method == 'GET':
            return get_watched_movies_list(user, int(page))  # Return tastes
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
            proposals = user.proposal
            if proposals is None:
                proposals = []

                tv_type_list = user.tv_type
                movies = taste_based_movie_selection(user, result_movies_schedule_list(tv_type_list))

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
                                      "channelNumber": channel_number(movie[0]["channel"]),
                                      "time": movie[0]["time"],
                                      "runTimes": movie_data_store.run_times,
                                      "simplePlot": movie_data_store.simple_plot,
                                      "italianPlot": movie_data_store.plot_it})

                    if movie_data_store is not None:
                        pass

                user.proposal = proposals
                user.put()
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


@app.route('/api/suggest/<user_id>/<query>')
def suggest(user_id, query):
    if request.method == 'GET':

        user = modelUser.get_by_id(user_id)  # Get user
        if user is not None:
            suggestions = retrieve_suggest_list(user, query)
            return jsonify(code=0, data=suggestions)
        else:
            raise InternalServerError(user_id + ' is not subscribed')
    else:
        raise MethodNotAllowed


@app.route('/api/search/<user_id>/<query>')
def search(user_id, query):
    if request.method == 'GET':

        user = modelUser.get_by_id(user_id)  # Get user
        if user is not None:
            results = retrieve_search_result_list(user, query)
            return jsonify(code=0, data=results)
        else:
            raise InternalServerError(user_id + ' is not subscribed')
    else:
        raise MethodNotAllowed


@app.route('/api/manual/<offset>')
def manual(offset):
    movies = Movie.query()
    for movie in movies.fetch(500, offset=int(offset)):
        movie.poster = clear_url(movie.poster)
        movie.put()
    artists = Artist.query()
    for artist in artists.fetch(500, offset=int(offset)):
        artist.photo = clear_url(artist.photo)
        artist.put()
    return 'OK'

# TODO: Finish the setting considering al the possible elements to be insert in the GET and in the POST
@app.route('/api/settings/<user_id>', methods=['GET', 'POST'])
def settings(user_id):
    """
    This function helps to retrieve and modify the settings of the application.
    :param user_id: the email of the user
    :type user_id: string
    :return: JSON in case of the GET, and null in case of POST and there's no error

    The POST request has to be done { "tvType": [ "free", "premium",...],
    """
    
    user = modelUser.get_by_id(user_id)
    if user is not None:
        if request.method == 'GET':

            return jsonify(code=0, userId=user.key.id(), tv_type=user.tv_type, repeatChoice=user.repeat_choice,
                           enableNotification=user.enable_notification, timeNotification=user.time_notification)

        elif request.method == 'POST':
            json_data = request.get_json()  # Get JSON from POST
            logging.info("changing settings")
            if json_data is None:
                raise BadRequest

            tv_type_list = json_data['tvType']   # Reading tv type and modifying the list
            if not user.modify_tv_type(tv_type_list):
                logging.info("bad tv type")
                raise BadRequest

            repeat_choice = json_data['repeatChoice']
            if not user.modify_repeat_choice(repeat_choice):
                logging.info("bad repeatChoice")
                raise BadRequest

            enable_notification = json_data['enableNotification']
            if not user.modify_notification(enable_notification):
                logging.info("bad enableNotification")
                raise BadRequest

            time_notification = json_data['timeNotification']
            if not user.modify_time_notification(time_notification):
                logging.info("bad timeNotification")
                raise BadRequest

            return 'OK'

        else:
            logging.info("method")
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


def get_or_retrieve_by_id(id_imdb):
    """
    This function check if the id is a valid IMDb id and in this case get or retrieve the correct entity.
    :param id_imdb: a valid IMDb id
    :type id_imdb: string
    :return: A model instance
    :rtype Artist or Movie model
    """

    artist = re.compile('nm\d{7}$')
    movie = re.compile('tt\d{7}$')

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

# TODO: argument next functions

def generate_artists(user, page=0):

    tastes_artists_id = user.tastes_artists  # Get all taste_artists' keys
    artists = []

    count = 0
    for i in range(page, len(tastes_artists_id)):
        taste_artist_id = tastes_artists_id[i]
        taste_artist = TasteArtist.get_by_id(taste_artist_id.id())  # Get taste

        if taste_artist.taste >= 1 and taste_artist.added:
            count = count +1
            if count == 6:
                next_page_artists = '/api/tastes/' + user.key.id() + '/artist/' + str(i + 1)

            if count == 7:
                break

            artist_id = taste_artist.artist.id()  # Get artist id from taste
            artist = Artist.get_by_id(artist_id)  # Get artist by id

            artists.append({"idIMDB": artist_id,
                            "name": artist.name.encode('utf-8') if artist.name is not None else None,
                            "tasted": 1,
                            "photo": artist.photo})

    if count <= 6:
        next_page_artists = None

    return {"artists": artists, "next_page": next_page_artists}


def generate_movies(user, page=0):

    tastes_movies_id = user.tastes_movies
    movies = []

    count = 0
    for i in range(page, len(tastes_movies_id)):
        taste_movie_id = tastes_movies_id[i]
        taste_movie = TasteMovie.get_by_id(taste_movie_id.id())  # Get taste
        count = count + 1

        if count == 4:
            next_page_movies = '/api/tastes/' + user.key.id() + '/movie/' + str(i + 1)

        if count == 5:
                break

        movie_id = taste_movie.movie.id()  # Get movie id from taste
        movie = Movie.get_by_id(movie_id)  # Get movie by id

        movies.append({"idIMDB": movie_id,
                       "originalTitle": movie.original_title.encode('utf-8') if movie.original_title is not None else movie.title.encode('utf-8'),
                       "title": movie.title.encode('utf-8') if movie.title is not None else movie.original_title.encode('utf-8'),
                       "tasted": 1,
                       "poster": movie.poster})

    if count <= 4:
        next_page_movies = None

    return {"movies": movies, "next_page": next_page_movies}


def generate_genres(user, page=0):

    tastes_genres_id = user.tastes_genres
    genres = []

    count = 0
    for i in range(page, len(tastes_genres_id)):
        taste_genre_id = tastes_genres_id[i]
        taste_genre = TasteGenre.get_by_id(taste_genre_id.id())  # Get taste

        # TODO: not use object, use a simple list
        if taste_genre.taste >= 1.0 and taste_genre.added:
            count = count + 1
            if count == 4:
                next_page_genres = '/api/tastes/' + user.key.id() + '/genre/' + str(i + 1)
            if count == 5:
                break

            genres.append({"name": taste_genre.genre,
                           "tasted": 1})
    if count <= 4:
        next_page_genres = None

    return {"genres": genres, "next_page": next_page_genres}


def get_watched_movies_list(user, page=0):
    """
    Get a readable watched movie list.
    :param user: user
    :type user: Models.User
    :return: list of watched movies
        {"code": 0, "data": {"movies": [{"idIMDB": id,"originalTitle": original_title, "poster": poster_url,
        "date": date}],"userId": user_id, "prevPage": prevPage, "nextPage": nextPage}
    :rtype: JSON
    """
    watched_movies_id = user.watched_movies  # Get all taste_artists' keys

    movies = []

    if (page + 1)*10 > len(watched_movies_id):  # Finding max element in page
        last_elem = len(watched_movies_id)
    else:
        last_elem = (page + 1)*10

    if (page + 1)*10 < len(watched_movies_id):  # Preparing url for next page
        next_page = str(page + 1)
        next_page_url = '/api/watched/' + user.key.id() + '/' + next_page
    else:
        next_page_url = None

    if page > 0:  # Preparing url for prev page
        prev_page = str(page - 1)
        prev_page_url = '/api/watched/' + user.key.id() + '/' + prev_page
    else:
        prev_page_url = None

    for i in range(page * 10, last_elem):  # Preparing JSON with list of movies watched for current page
        watched_movie_id = watched_movies_id[i].id()
        watched_movie = Movie.get_by_id(watched_movie_id)  # Get movie

        date_watched_movie = user.date_watched[i]  # Get date

        taste_movie = TasteMovie.get_by_id(watched_movie_id + user.key.id())  # Get taste

        movies.append({"idIMDB": watched_movie.key.id(),
                       "originalTitle": watched_movie.original_title.encode('utf-8') if watched_movie.original_title is not None else watched_movie.title.encode('utf-8'),
                       "title": watched_movie.title.encode('utf-8') if watched_movie.title is not None else watched_movie.original_title.encode('utf-8'),
                       "poster": watched_movie.poster,
                       "date": date_watched_movie.strftime('%d-%m-%Y'),
                       "tasted": 1 if taste_movie is not None else 0})

    return jsonify(code=0, data={"userId": user.key.id(), "watched": movies,
                                 "nextPage": next_page_url, "previousPage": prev_page_url})


