from google.appengine.api import memcache
from utilities import *
import lxml.html
from werkzeug.exceptions import BadRequest


def get_movies_schedule(html_page):
    """
    Parse HTML page and retrieve information about movies schedule as title, original title, channel and time of
    transmission.
    :param html_page: HTML page to parse
    :type html_page: string
    :return: list JSON object of movie scraped
        {"title": title, "originalTitle": original_title, "channel": channel, "time": time}
    :rtype: list of dict
    """
    movies_list = []

    tree = lxml.html.fromstring(html_page)

    movies_node = tree.xpath('//article[@class="item item-scheda item-scheda-film cf option-view-list"]')  # Get movies
    for movie_node in movies_node:
        title = movie_node.xpath('.//a[contains(@href, "http://www.filmtv.it/film/")]/text()')[0].strip().encode(
            'utf-8')  # Get title
        original_title = movie_node.xpath('.//p[@class="titolo-originale"]/text()')  # Get original title
        if len(original_title) == 0:
            original_title = None
        else:
            original_title = original_title[0].strip().encode('utf-8')
        channel = movie_node.xpath('.//h3[@class="media tv"]/text()')[0].strip().encode('utf-8')  # Get channel
        time = movie_node.xpath('.//time[@class="data"]/text()')[0][2:].strip()  # Get time

        movies_list.append({"title": title, "originalTitle": original_title, "channel": channel, "time": time})
        print movies_list
    return movies_list


def result_movies_schedule(tv_type, day):
    """
    Get TV movies schedule from www.filmtv.it. You could ask the schedule of today, tomorrow and the day after tomorrow
    of the free TV, SKY TV and Mediaset Premium TV.
    :param tv_type: type of TV from get schedule, possible value (free, sky, premium)
    :type tv_type: string
    :param day: interested day, possible value (today, tomorrow, future)
    :type day: string
    :return: list JSON object of movie info scraped
        {"title": title, "originalTitle": original_title, "channel": channel, "time": time}
    :rtype: list of dict
    """
    if day.upper() == "TODAY":  # Translate day for get call
        day = "oggi"
    elif day.upper() == "TOMORROW":
        day = "domani"
    elif day.upper() == "FUTURE":
        day = "dopodomani"
    else:
        raise BadRequest

    if tv_type.upper() == "FREE":  # Translate tv_type for get call
        tv_type = "free"
        schedule = memcache.get(tv_type + day)  # Tries to retrieve the schedule in memcache
        if schedule is not None:  # Control if it was retrieved
            return schedule
        else:
            html_page = get(BASE_URL_FILMTV_FILM + day + "/stasera/")
            schedule = get_movies_schedule(html_page)
            memcache.add("free" + day, schedule, 3600)  # Store the schedule in memcache for int seconds
            return schedule

    elif tv_type.upper() == "SKY":
        tv_type = "sky"
        schedule = memcache.get(tv_type + day)  # Tries to retrieve the schedule in memcache
        if schedule is not None:  # Control if it was retrieved
            return
        else:
            html_page = get(BASE_URL_FILMTV_FILM + day + "/stasera/" + tv_type)
            schedule = get_movies_schedule(html_page)
            memcache.add(tv_type + day, schedule, 3600)  # Store the schedule in memcache for int seconds
            return schedule

    elif tv_type.upper() == "PREMIUM":
        tv_type = "premium"
        schedule = memcache.get(tv_type + day)  # Tries to retrieve the schedule in memcache
        if schedule is not None:
            return schedule
        else:
            html_page = get(BASE_URL_FILMTV_FILM + day + "/stasera/" + tv_type)
            schedule = get_movies_schedule(html_page)
            memcache.add(tv_type + day, schedule, 3600)  # Store the schedule in memcache for int seconds
            return schedule
    else:
        raise BadRequest


if __name__ == "__main__":
    print result_movies_schedule("free", "today")