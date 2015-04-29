import logging
import random
from google.appengine.ext import ndb
from models import TasteMovie, TasteArtist, TasteGenre, User, Movie

from tv_scheduling import result_movies_schedule
from utilities import NUMBER_SUGGESTIONS


def random_movie_selection(schedule_movies):
    """
    Select random movie from TV schedule passed.
    :param schedule_movies: movies schedule
    :type schedule_movies: list of dict
    :return: movie selected randomly
    :rtype: JSON object
    """
    return random.choice(schedule_movies)


def taste_based_movie_selection(user, schedule_movies):
    """

    :param user:
    :param schedule_movies:
    :return:
    """
    tastes_artists_id = user.tastes_artists  # Get all taste_artists' keys
    tastes_movies_id = user.tastes_movies
    tastes_genres_id = user.tastes_genres

    artists_id = []
    artists_value = []
    for taste_artist_id in tastes_artists_id:
        taste_artist = TasteArtist.get_by_id(taste_artist_id.id())  # Get taste
        if taste_artist is not None:
            artist_id = taste_artist.artist.id()  # Get movie id from taste
            artists_id.append(artist_id)
            artists_value.append(taste_artist.taste)
        else:
            logging.error("Inconsistence with taste_artist")

    movies_id = []
    movies_value = []
    for taste_movie_id in tastes_movies_id:
        taste_movie = TasteMovie.get_by_id(taste_movie_id.id())  # Get taste
        if taste_movie is not None:
            movie_id = taste_movie.movie.id()  # Get movie id from taste
            movies_id.append(movie_id)
            movies_value.append(taste_movie.taste)
        else:
            logging.error("Inconsistence with taste_movie")

    genres = []
    genres_value = []
    for taste_genre_id in tastes_genres_id:
        taste_genre = TasteGenre.get_by_id(taste_genre_id.id())
        if taste_genre is not None:
            genres.append(taste_genre.genre)
            genres_value.append(taste_genre.taste)
        else:
            logging.error("Inconsistence with taste_genre")

    data = []
    random_choice = True

    repeatChoice = user.repeat_choice

    for movie in schedule_movies:
        points = 0.0
        movie_data_store = Movie.query(ndb.OR(Movie.original_title == movie["originalTitle"],
                                              Movie.title == movie["title"])).get()

        if movie_data_store is not None:
            if repeatChoice is not True and movie_data_store.key in user.watched_movies:
                logging.info("Movie already watched: " + movie_data_store.key.id())
                continue

            for actor in movie_data_store.actors:
                if actor.get().key.id() in artists_id:
                    logging.info("Trovato %s", str(actor.get().key.id()))
                    points += artists_value[artists_id.index(actor.get().key.id())]
                    random_choice = False

            for director in movie_data_store.directors:
                if director.get().key.id() in artists_id:
                    logging.info("Trovato %s", str(director.get().key.id()))
                    points += artists_value[artists_id.index(director.get().key.id())]
                    random_choice = False

            for writer in movie_data_store.writers:
                if writer.get().key.id() in artists_id:
                    logging.info("Trovato %s", str(writer.get().key.id()))
                    points += artists_value[artists_id.index(writer.get().key.id())]
                    random_choice = False

            for genre in movie_data_store.genres:
                if genre in genres:
                    logging.info("Trovato %s", genre)
                    points += genres_value[genres.index(genre)]
                    random_choice = False

            logging.info("Titolo: %s - Punteggio: %6.2f", movie_data_store.original_title, points)

            data.append((movie, points))
        else:
            logging.error("Non presente nel datastore: %s", (str(movie["originalTitle"]) if movie["originalTitle"] is not None else str(movie["title"])))

    if random_choice:
        random.shuffle(data)
    else:
        data.sort(key=lambda tup: tup[1], reverse=True)

    return data

if __name__ == "__main__":
    print taste_based_movie_selection(User.get_by_id("test@example.com"), result_movies_schedule("free", "today"))