""" file contains general methods for bootprocess """
import logging
from django.core import mail
from django.core.mail import BadHeaderError
from enigma_automation.settings import EMAIL_BACKEND, DEFAULT_FROM_EMAIL
logger = logging.getLogger(__name__)


def email_via_smtp(destination, subject, body):
    """ method to send email to destination with given subject and body """
    if destination and subject and body:
        with mail.get_connection(backend=EMAIL_BACKEND) as connection:
            try:
                email = mail.EmailMessage(subject=subject, body=body,
                                          from_email=DEFAULT_FROM_EMAIL, to=destination,
                                          connection=connection)
                email.content_subtype = "html"
                response = email.send(fail_silently=False)
                if response != 1:
                    raise Exception('Message not delivered. Contact Admin for more details.')
            except BadHeaderError as exc:
                raise Exception("Invalid header found.") from exc
    else:
        raise Exception('Make sure all fields are entered and valid.')

    logger.info("Email Sent!!")
    return True
