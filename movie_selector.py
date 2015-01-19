import random
from google.appengine.ext import ndb
from models import TasteMovie, TasteArtist, TasteGenre, User, Movie

from tv_scheduling import result_movies_schedule


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
    tastes_artists_id = user.tastes_artists  # Get all taste_artists' keys
    tastes_movies_id = user.tastes_movies
    tastes_genres_id = user.tastes_genres

    artists_id = []
    artists_value = []
    for taste_artist_id in tastes_artists_id:
        taste_artist = TasteArtist.get_by_id(taste_artist_id.id())  # Get taste
        artist_id = taste_artist.id_IMDB.id()  # Get movie id from taste
        artists_id.append(artist_id)
        artists_value.append(taste_artist.taste)

    movies_id = []
    movies_value = []
    for taste_movie_id in tastes_movies_id:
        taste_movie = TasteMovie.get_by_id(taste_movie_id.id())  # Get taste
        movie_id = taste_movie.id_IMDB.id()  # Get movie id from taste
        movies_id.append(movie_id)
        movies_value.append(taste_movie.taste)

    genres = []
    genres_value = []
    for taste_genre_id in tastes_genres_id:
        taste_genre = TasteGenre.get_by_id(taste_genre_id.id())
        genres.append(taste_genre.genre)
        print (taste_genre.genre, taste_genre.taste)
        genres_value.append(taste_genre.taste)

    for movie in schedule_movies:
        points = 0
        movie_data_store = Movie.query(ndb.OR(Movie.original_title == movie["originalTitle"],
                                              Movie.title == movie["title"])).get()
        if movie_data_store is not None:
            print movie_data_store.key.id()
            for actor in movie_data_store.actors:
                if actor.get().key.id() in artists_id:
                    print "Trovato " + str(actor.get().key.id())
                    points += artists_value[artists_id.index(actor.get().key.id())]
            for genre in movie_data_store.genres:
                if genre in genres:
                    print "Trovato " + genre
                    points += genres_value[genres.index(genre)]
            print movie_data_store.key.id(), str(points)
        else:
            print "non ce l'ho ", str(movie["originalTitle"])

    return random.choice(schedule_movies)

if __name__ == "__main__":
    print taste_based_movie_selection(User.get_by_id("test@example.com"), result_movies_schedule("free", "today"))