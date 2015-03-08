import logging
from google.appengine.api import memcache
import lxml.html
from werkzeug.exceptions import BadRequest, InternalServerError
from utilities import TV_TYPE, BASE_URL_FILMTV_FILM, time_for_tomorrow, get


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
        movie_url = movie_node.xpath('.//a[contains(@href, "http://www.filmtv.it/film/")]/@href')[0]  # Get FilmTV url
        original_title = movie_node.xpath('.//p[@class="titolo-originale"]/text()')  # Get original title
        year = movie_node.xpath('.//ul[@class="info cf"]/li/time/text()')[0]  # Get year
        if len(original_title) == 0:
            original_title = None
        else:
            original_title = original_title[0].strip().encode('utf-8')
        channel = movie_node.xpath('.//h3[@class="media tv"]/text()')[0].strip().encode('utf-8')  # Get channel
        time = movie_node.xpath('.//time[@class="data"]/text()')[0][2:].strip()  # Get time

        if channel != "Rsi La1" and channel != "Rsi La2":  # Remove the swiss channels
            value = {"title": title, "originalTitle": original_title, "channel": channel, "time": time,
                            "movieUrl": movie_url, "year": year}
            movies_list.append(value) if value not in movies_list else logging.info("Movie already in schedule")
            # Control of doubles in schedule

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

    tv_type = tv_type.lower()

    schedule = memcache.get(tv_type + day)  # Tries to retrieve the schedule from memcache
    if schedule is not None:  # Control if it was retrieved
        return schedule
    else:  # Else retrieve it
        if tv_type == TV_TYPE[0]:
            url = BASE_URL_FILMTV_FILM + day + "/stasera/"
        elif tv_type == TV_TYPE[1] or tv_type == TV_TYPE[2]:
            url = BASE_URL_FILMTV_FILM + day + "/stasera/" + tv_type
        else:
            raise BadRequest

        html_page = get(url)  # Get HTML page
        schedule = get_movies_schedule(html_page)  # Retrieve schedule

        if schedule is not None:
            memcache.add(tv_type + day, schedule, time_for_tomorrow())  # Store the schedule in memcache
            return schedule
        else:
            raise InternalServerError('TV scheduling not retrieved')


def result_movies_schedule_list(tv_type_list):
    """
    This combine all the movies in schedule for the different tv types present in the list

    :param tv_type_list: list of tv types
    :return: return the JSON with all the schedule for current list
    """
    schedule_list = []

    if tv_type_list == []:
        logging.info("no tv type set")
        tv_type_list = ["free"]

    for i in tv_type_list:
        schedule_list = schedule_list + result_movies_schedule(i, "today")

    return schedule_list

if __name__ == "__main__":
    print result_movies_schedule("free", "today")