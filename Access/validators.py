import re
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from Access.models import StoredPassword

class NumberValidator(object):
    def validate(self, password, user=None):
        if not re.findall('\d', password):
            raise ValidationError(
                _("The password must contain at least 1 digit, 0-9."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 digit, 0-9."
        )


class UppercaseValidator(object):
    def validate(self, password, user=None):
        if not re.findall('[A-Z]', password):
            raise ValidationError(
                _("The password must contain at least 1 uppercase letter, A-Z."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 uppercase letter, A-Z."
        )


class SymbolValidator(object):
    def validate(self, password, user=None):
        if not re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', password):
            raise ValidationError(
                _("The password must contain at least 1 special character: " +
                  "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 special character: " +
            "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"
        )


class RepeatedValidator(object):
    def validate(self, password, user=None):
        if user is None:
            return None

        user_list = StoredPassword.objects.filter(user=user).order_by('-id')[:3:-1]
        password_list = []
        for user in user_list:
            password_list.append(user.password)

        for encoded in password_list:
            saved_password = check_password(password, encoded, setter=None, preferred='pbkdf2_sha256')
            if saved_password:
                raise ValidationError(
                    _("The password cannot be the same as last 3 used passwords."),
                    code='password_no_symbol',
                )

    def password_changed(self, password, user=None):
        if user is None:
            return None

        hashed_password = make_password(password, salt=None, hasher='pbkdf2_sha256')
        saved_password = StoredPassword.objects.filter(user=user, password=hashed_password).first()
        if saved_password is None:
            saved_password = StoredPassword()
            saved_password.user = user
            saved_password.password = hashed_password
            saved_password.save()

    def get_help_text(self):
        return _(
            "Your password cannot be the same as last 3 used passwords."
        )
