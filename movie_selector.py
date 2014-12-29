import random

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


if __name__ == "__main__":
    print random_movie_selection(result_movies_schedule("free", "today"))