from google.appengine.api import mail


def confirm_subscription(user):
    """
    Send email for subscription.
    :param user: user to send email
    :type user: models.User
    :return: None
    """
    message = mail.EmailMessage(sender="PRIMETIME4U Support <support@hale-kite-786.appspotmail.com>",
                                subject="Your now subscribed")

    message.to = "{} <{}>".format(user.name, user.key.id())
    message.body = """
    Dear {}:

    You are now subscribed to our movie suggest. You only have to
    wait the daily mail for our movie suggest.

    Please let us know if you have any questions and give us
    some feedback if you want.

    The PRIMETIME4U Team
    """.format(user.name)

    message.send()


def confirm_unsubscription(user):
    """
    Send email for unsubscription.
    :param user: user to send email
    :type user: models.User
    :return: None
    """
    message = mail.EmailMessage(sender="PRIMETIME4U Support <support@hale-kite-786.appspotmail.com>",
                                subject="Your now unsubscribed")
    print user
    message.to = "{} <{}>".format(user.name, user.key.id())
    message.body = """
    Dear {}:

    You are now unsubscribed to our movie suggest.

    Please let us know why you decided it, your feedback is
    important for us.

    The PRIMETIME4U Team
    """.format(user.name)

    message.send()


def send_suggestion(user, movie):
    """
    Send email form movie suggestion.
    :param user: user to send email
    :type user: models.User
    :param movie: movie to suggest
    :type movie: JSON object
    :return: None
    """
    message = mail.EmailMessage(sender="PRIMETIME4U Suggestion <support@hale-kite-786.appspotmail.com>",
                                subject="Your daily movie suggest")

    message.to = "{} <{}>".format(user.name, user.key.id())
    message.body = """
    Dear {}:

    Today we suggest you:

    Title: {};
    Original Title: {};
    Channel: {};
    Time: {}

    The PRIMETIME4U Team
    """.format(user.name, movie["title"], movie["originalTitle"], movie["channel"], movie["time"])

    message.send()