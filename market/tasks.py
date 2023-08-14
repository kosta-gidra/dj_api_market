from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from dj_api_market.celery import app

from market.models import ConfirmEmailToken, User


@app.task
def send_token_to_email_task(user_id, title,  **kwargs):
    """
    Отправляем письмо с токеном пользователю
    """
    # send an e-mail to the user
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"{title}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email]
    )
    msg.send()


@app.task
def send_simple_mail_task(user_id, title, message, **kwargs):
    """
    Отправляем письмо пользователю
    """
    # send an e-mail to the user
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"{title}",
        # message:
        f"{message}",
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()
