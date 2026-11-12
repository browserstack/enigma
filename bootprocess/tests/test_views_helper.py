""" tests for bootprocess.views_helper (real database, no model mocking) """
import pytest
from django.contrib.auth.models import User as AuthUser
from Access import models
from bootprocess import views_helper
from EnigmaAutomation.settings import DEFAULT_ACCESS_GROUP


class _Request:
    """ minimal request carrying the auth user """
    def __init__(self, auth_user):
        self.user = auth_user


@pytest.fixture(name="env")
def fixture_env(monkeypatch):
    """ default group with an owner, a new joiner, and a stubbed access grant """
    owner_auth = AuthUser.objects.create(username="owner")
    owner = models.User.objects.get_or_create(user=owner_auth, defaults={"name": "owner"})[0]
    group = models.GroupV2.objects.create(
        group_id="g1", name=DEFAULT_ACCESS_GROUP, description="d",
        requester=owner, status="Approved", approver=owner)
    models.MembershipV2.objects.create(
        membership_id="m-owner", user=owner, group=group, is_owner=True,
        requested_by=owner, status="Approved")
    joiner_auth = AuthUser.objects.create(username="joiner")
    joiner = models.User.objects.get_or_create(user=joiner_auth, defaults={"name": "joiner"})[0]

    granted = []
    monkeypatch.setattr(views_helper, "generate_user_mappings", lambda *_: ["m"])
    monkeypatch.setattr(views_helper, "execute_group_access", granted.append)
    return {"auth": joiner_auth, "user": joiner, "group": group, "granted": granted}


def _count(env):
    return models.MembershipV2.objects.filter(
        user=env["user"], group=env["group"]).count()


@pytest.mark.django_db
def test_new_user_is_added_to_default_group_once(env):
    """ first dashboard load adds the membership and grants access """
    context = views_helper.get_dashboard_data(_Request(env["auth"]))
    assert _count(env) == 1
    assert len(env["granted"]) == 1
    assert context["groupCount"] == 1


@pytest.mark.django_db
def test_repeated_dashboard_loads_do_not_duplicate_membership(env):
    """ F-041: a second load must not create a second membership or grant """
    views_helper.get_dashboard_data(_Request(env["auth"]))
    views_helper.get_dashboard_data(_Request(env["auth"]))
    assert _count(env) == 1
    assert len(env["granted"]) == 1


@pytest.mark.django_db
def test_membership_check_is_not_string_based(env):
    """ a lookalike group name must not count as being in the default group """
    other = models.GroupV2.objects.create(
        group_id="g2", name=DEFAULT_ACCESS_GROUP + "-extra", description="d",
        requester=env["user"], status="Approved", approver=env["user"])
    models.MembershipV2.objects.create(
        membership_id="m-other", user=env["user"], group=other,
        requested_by=env["user"], status="Approved")
    views_helper.get_dashboard_data(_Request(env["auth"]))
    assert _count(env) == 1
