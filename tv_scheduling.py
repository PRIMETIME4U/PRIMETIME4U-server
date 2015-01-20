from google.appengine.api import memcache
from utilities import *
import lxml.html
from werkzeug.exceptions import BadRequest, InternalServerError


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
        movie_url = movie_node.xpath('.//a[contains(@href, "http://www.filmtv.it/film/")]/@href')[0]
        original_title = movie_node.xpath('.//p[@class="titolo-originale"]/text()')  # Get original title
        movie_year = movie_node.xpath('.//ul[@class="info cf"]/li/time/text()')[0]
        #print title
        print movie_year
        if len(original_title) == 0:
            original_title = None
        else:
            original_title = original_title[0].strip().encode('utf-8')
        channel = movie_node.xpath('.//h3[@class="media tv"]/text()')[0].strip().encode('utf-8')  # Get channel
        time = movie_node.xpath('.//time[@class="data"]/text()')[0][2:].strip()  # Get time

        movies_list.append({"title": title, "originalTitle": original_title, "channel": channel, "time": time,
                            "movieUrl": movie_url, "year": movie_year})
        #print movies_list
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
    else:
        if tv_type == TV_TYPE[0]:
            url = BASE_URL_FILMTV_FILM + day + "/stasera/"
        elif tv_type == TV_TYPE[1] or tv_type == TV_TYPE[2]:
            url = BASE_URL_FILMTV_FILM + day + "/stasera/" + tv_type
        else:
            raise BadRequest

        html_page = get(url)
        schedule = get_movies_schedule(html_page)

        if schedule is not None:
            memcache.add(tv_type + day, schedule, time_for_tomorrow())  # Store the schedule in memcache
            return schedule
        else:
            raise InternalServerError("Errore sono None")


if __name__ == "__main__":
    print result_movies_schedule("free", "today")