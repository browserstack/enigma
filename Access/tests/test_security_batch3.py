""" regression tests: F-033 mark_revoked status, F-034 password history, F-036 CID """
import re
from types import SimpleNamespace
from unittest import mock
import pytest
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth.hashers import make_password
from django.test import RequestFactory
from Access import views
from Access.models import StoredPassword
from Access.validators import RepeatedValidator
from EnigmaAutomation import settings


def _ops_request(query):
    request = RequestFactory().get("/access/markRevoked", query)
    perm = SimpleNamespace(label="ALLOW_USER_OFFBOARD")
    request.user = mock.MagicMock()
    request.user.is_authenticated = True
    request.user.user.permissions = [perm]
    return request


def test_mark_revoked_success_returns_200():
    """ F-033: success must not be reported as 403 """
    mapping = mock.MagicMock(request_id="r1")
    with mock.patch.object(
            views.UserAccessMapping, "get_unrevoked_accesses_by_request_id",
            return_value=[mapping]):
        response = views.mark_revoked(_ops_request({"requestId": "r1"}))
    assert response.status_code == 200
    mapping.revoke.assert_called_once()


def test_mark_revoked_failure_returns_500():
    """ an exception during revoke is an error status, not 200 """
    with mock.patch.object(
            views.UserAccessMapping, "get_unrevoked_accesses_by_request_id",
            side_effect=RuntimeError("boom")):
        response = views.mark_revoked(_ops_request({"requestId": "r1"}))
    assert response.status_code == 500


def test_mark_revoked_module_without_username_is_400():
    """ missing username on a module revoke is a client error """
    response = views.mark_revoked(_ops_request({"requestId": "module-ssh"}))
    assert response.status_code == 400


@pytest.fixture(name="auth_user")
def fixture_auth_user(db):
    """ django auth user """
    del db
    return AuthUser.objects.create(username="pwuser")


def _store(user, *passwords):
    for pw in passwords:
        StoredPassword.objects.create(
            user=user, password=make_password(pw, hasher="pbkdf2_sha256"))


@pytest.mark.parametrize("history", [1, 3, 4])
def test_recent_password_is_rejected_even_with_short_history(auth_user, history):
    """ F-034: [:3:-1] skipped the check when <=4 passwords were stored """
    _store(auth_user, *[f"Old-pass-{i}!" for i in range(history)])
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        RepeatedValidator().validate(f"Old-pass-{history - 1}!", auth_user)


def test_new_password_is_accepted(auth_user):
    """ a password not in the history passes """
    _store(auth_user, "Old-pass-0!")
    assert RepeatedValidator().validate("Brand-new-1!", auth_user) is None


def test_password_older_than_three_is_allowed(auth_user):
    """ only the last 3 are blocked """
    _store(auth_user, "p-a-1!", "p-b-2!", "p-c-3!", "p-d-4!")
    assert RepeatedValidator().validate("p-a-1!", auth_user) is None


def test_password_changed_does_not_store_duplicates(auth_user):
    """ the same password saved twice must produce one row """
    validator = RepeatedValidator()
    validator.password_changed("Same-pass-1!", auth_user)
    validator.password_changed("Same-pass-1!", auth_user)
    assert StoredPassword.objects.filter(user=auth_user).count() == 1


def test_cid_generator_is_unpredictable_and_unique():
    """ F-036: CID comes from uuid4 (os.urandom), not random.random() """
    ids = {settings.CID_GENERATOR() for _ in range(200)}
    assert len(ids) == 200
    assert all(re.fullmatch(r"[0-9a-f]{32}", i) for i in ids)
