import re
from django.contrib.auth.hashers import make_password
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
        # In case there is no user this validator is not applicable, so we return success
        print("validating repeat with pbkdf2_sha256")
        if user is None:
            return None
        hashed_password = make_password(password, salt=None, hasher='pbkdf2_sha256')
        saved_password = StoredPassword.objects.filter(user=user, password=hashed_password).first()
        if saved_password is not None:
            raise ValidationError(
                _("The password cannot be the same as previously used passwords."),
                code='password_no_symbol',
            )

    def password_changed(self, password, user=None):
        # In case there is no user this is not applicable
        if user is None:
            return None

        print("saving old password")
        hashed_password = make_password(password, salt=None, hasher='pbkdf2_sha256')
        saved_password = StoredPassword.objects.filter(user=user, password=hashed_password).first()
        if saved_password is None:
            saved_password = StoredPassword()
            saved_password.user = user
            saved_password.password = hashed_password
            saved_password.save()

    def get_help_text(self):
        return _(
            "Your password cannot be the same as previously used passwords."
        )
