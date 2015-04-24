import logging
import random
from google.appengine.ext import ndb
from models import TasteMovie, TasteArtist, TasteGenre, User, Movie

from tv_scheduling import result_movies_schedule
from utilities import NUMBER_SUGGESTIONS
from time import time

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
    times = time()

    artists_id = user.artists_id
    genres_id = user.genres_id

    tiempo = time()
    data = []
    random_choice = True

    for movie in schedule_movies:
        points = 0.0
        movie_data_store = Movie.query(ndb.OR(Movie.original_title == movie["originalTitle"],
                                              Movie.title == movie["title"])).get()
        if movie_data_store is not None:
            for actor in movie_data_store.actors:
                if actor.get().key.id() in artists_id:
                    logging.info("Trovato %s", str(actor.get().key.id()))
                    points += user.get_value_artist(actor.get().key.id())
                    random_choice = False

            for director in movie_data_store.directors:
                if director.get().key.id() in artists_id:
                    logging.info("Trovato %s", str(director.get().key.id()))
                    points += user.get_value_artist(actor.get().key.id())
                    random_choice = False

            for writer in movie_data_store.writers:
                if writer.get().key.id() in artists_id:
                    logging.info("Trovato %s", str(writer.get().key.id()))
                    points += user.get_value_artist(actor.get().key.id())
                    random_choice = False

            for genre in movie_data_store.genres:
                if genre in genres_id:
                    logging.info("Trovato %s", genre)
                    points += user.get_value_genre(genre)
                    random_choice = False

            logging.info("Titolo: %s - Punteggio: %6.2f", movie_data_store.original_title, points)

            data.append((movie, points))
        else:
            logging.error("Non presente nel datastore: %s", (str(movie["originalTitle"]) if movie["originalTitle"] is not None else str(movie["title"])))

    logging.info("time for algorithm" + str(time()-tiempo))

    if random_choice:
        random.shuffle(data)
    else:
        data.sort(key=lambda tup: tup[1], reverse=True)

    logging.info("total TIME: " + str(time() - times))
    return data

if __name__ == "__main__":
    print taste_based_movie_selection(User.get_by_id("test@example.com"), result_movies_schedule("free", "today"))