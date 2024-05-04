from django.conf import settings
from typing import Type
from django.db.models.signals import post_save
from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver
from django_rest_passwordreset.signals import reset_password_token_created

from .models import ConfirmEmailToken, User

new_user_registered = Signal()

new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    This function is a signal receiver for the reset_password_token_created signal.
    It sends an email to the user with the reset password token.

    Parameters:
    - sender (django_rest_passwordreset.signals.ResetPasswordTokenCreated): The sender of the signal.
    - instance (django_rest_passwordreset.models.ResetPasswordToken): The instance of the ResetPasswordToken model.
    - reset_password_token (django_rest_passwordreset.models.ResetPasswordToken): The ResetPasswordToken instance.
    - kwargs (dict): Additional keyword arguments passed to the signal receiver.
    """
    message = EmailMultiAlternatives(
        f'Password Reset Token for {reset_password_token.user}',
        reset_password_token.key,
        settings.EMAIL_HOST_USER,
        [reset_password_token.user.email]
    )
    message.send()


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    """
    This function is a signal receiver for the new_user_registered signal.
    It sends an email to the user with a confirmation email token.

    Parameters:
    - sender (Type[User]): The type of the User model.
    - instance (User): The newly created User instance.
    - created (bool): A boolean indicating whether the instance was created or updated.
    - kwargs (dict): Additional keyword arguments passed to the signal receiver.
    """
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)

    message = EmailMultiAlternatives(
        f"Password Reset Token for {instance.email}",
        token.key,
        settings.EMAIL_HOST_USER,
        [instance.email]
    )
    message.send()


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """
    This function is a signal receiver for the new_order signal.
    It sends an email to the user with an update on their order status.

    Parameters:
    - user_id (int): The ID of the user associated with the order.
    - kwargs (dict): Additional keyword arguments passed to the signal receiver.
    """
    user = User.objects.get(id=user_id)

    message = EmailMultiAlternatives(
        'Order status update',
        'The order has been collected',
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    message.send()
