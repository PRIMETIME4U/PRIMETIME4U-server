from google.appengine.api import mail


def confirm_subscription(user):
    """
    Send email for subscription.
    :param user: user to send email
    :type user: models.User
    :return: None
    """
    message = mail.EmailMessage(sender="PRIMETIME4U Support <support@hale-kite-786.appspotmail.com>",
                                subject="PT4U: Subscription confirmed")

    message.to = "{} <{}>".format(user.name, user.key.id())
    message.body = """
    Dear {},

    You are subscribed to PRIMETIME4U and now you only have to wait the daily mail with our movie proposal.
    Enjoy our service and leave us a feedback!


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
                                subject="PT4U: Unsubscription confirmed")
    message.to = "{} <{}>".format(user.name, user.key.id())
    message.body = """
    Dear {},

    Thank you for using our service. You will not receive movie proposals anymore.
    Let us know why you have decided to leave our service. Your feedback is important for us.

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
                                subject="PT4U: Your daily movie proposal")

    message.to = "{} <{}>".format(user.name, user.key.id())

    message.body = """
    Dear {},

    Today we propose to you:

    Title: {};
    Original Title: {};
    Channel: {};
    Time: {}

    The PRIMETIME4U Team
    """.format(user.name,
               movie["title"],
               movie["originalTitle"] if movie["originalTitle"] is not None else movie["title"],
               movie["channel"],
               movie["time"])

    message.send()


def send_feedback(sender):
    """
    Thank the user.
    :param sender: the sender to thank
    :type sender: String
    :return: None
    """
    message = mail.EmailMessage(sender="PRIMETIME4U Support <support@hale-kite-786.appspotmail.com>",
                                subject="PT4U: Thanks for your feedback")

    message.to = "{}".format(sender)
    message.body = """
    Dear {},

    Thanks for your feedback, it will be helpful in order to improve your PT4U experience!

    The PRIMETIME4U Team
    """.format(sender)

    message.send()


def forward_mail(mail_message):
    """
    Forward mail received to admins.
    :param mail_message: the mail message
    :type mail_message: InboundEmailMessage
    :return: None
    """
    content_type, encoded = mail_message.bodies(content_type='text/plain').next()
    body = encoded.decode()
    mail.send_mail(sender="support@hale-kite-786.appspotmail.com",
                   to="Claudio Pastorini <pastorini.claudio@gmail.com>, "
                      "Dorel Coman <dorelcomanj@gmail.com>, "
                      "Giovanni Colonna <gc240790@gmail.com>, "
                      "Marius Ionita <ionita.maryus@gmail.com>",
                   subject=mail_message.subject,
                   body=body,
                   reply_to=mail_message.sender)
