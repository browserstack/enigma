"""features/process_individual_request.feature feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


import pytest
from .. import accessrequest_helper
import Access
from Access import helpers
from Access.models import User
from Access.models import UserAccessMapping
from django.db.models.query import QuerySet
from datetime import datetime, timedelta


@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.email = "test@test.com"
    user.user.username = "test-user"
    return user


@pytest.fixture
def context(mocker):
    context = mocker.MagicMock()
    return context


@pytest.fixture
def new_request(mocker):
    req = mocker.MagicMock()
    return req


@scenario(
    "./features/process_individual_request.feature",
    "Multiple pending requests for a club",
)
def test_multiple_pending_requests_for_a_club():
    """Multiple pending requests for a club."""
    pass


@scenario(
    "./features/process_individual_request.feature",
    "Multiple pending requests for multiple clubs",
)
def test_multiple_pending_requests_for_multiple_clubs():
    """Multiple pending requests for multiple clubs."""
    pass


@scenario("./features/process_individual_request.feature", "No pending requests")
def test_no_pending_requests():
    """No pending requests."""
    pass


@scenario(
    "./features/process_individual_request.feature", "Single pending request for a club"
)
def test_single_pending_request_for_a_club():
    """Single pending request for a club."""
    pass


@given('access_tag is "access-tag-1"')
def step_impl(context):
    """access_tag is "access-tag-1"."""
    context.access_tag = "access-tag-1"


@given('club id is "123"')
def step_impl(context):
    """club id is "123"."""
    context.club_id = "123"


@given("individual_pending_requests contains a single pending request for a club")
def step_impl(context, mocker):
    """individual_pending_requests contains a single pending request for a club."""
    context.individual_pending_requests = [
        {
            "requestId": "123_request_1",
            "club_id": "123",
            "userEmail": "user@example.com",
            "accessReason": "test_reason",
            "access_desc": "test_access_desc",
            "access_tag": "access-tag-1",
            "requested_on": datetime.now().isoformat(),
            "accessCategory": "test_access_category",
            "accessMeta": "test_access_meta",
        }
    ]


@given("individual_pending_requests contains multiple pending requests for a club")
def step_impl(context):
    """individual_pending_requests contains multiple pending requests for a club."""
    context.individual_pending_requests = [
        {
            "requestId": "123_1",
            "userEmail": "user1@example.com",
            "accessReason": "reason 1",
            "access_desc": "desc 1",
            "access_tag": "tag 1",
            "requested_on": datetime(2023, 5, 1, 10, 0, 0),
            "accessCategory": "category 1",
            "accessMeta": "meta 1",
        },
        {
            "requestId": "123_2",
            "userEmail": "user2@example.com",
            "accessReason": "reason 2",
            "access_desc": "desc 2",
            "access_tag": "tag 2",
            "requested_on": datetime(2023, 5, 1, 11, 0, 0),
            "accessCategory": "category 2",
            "accessMeta": "meta 2",
        },
    ]


@given(
    "individual_pending_requests contains multiple pending requests for multiple clubs"
)
def step_impl(context):
    """individual_pending_requests contains multiple pending requests for multiple clubs."""
    context.individual_pending_requests = [
        {
            "requestId": "123_request1",
            "club_id": "123",
            "userEmail": "user1@example.com",
            "accessReason": "reason1",
            "access_desc": "desc1",
            "access_tag": "access-tag-1",
            "requested_on": "2023-04-29T00:00:00Z",
            "accessCategory": "cat1",
            "accessMeta": "meta1",
        },
        {
            "requestId": "123_request2",
            "club_id": "123",
            "userEmail": "user2@example.com",
            "accessReason": "reason2",
            "access_desc": "desc2",
            "access_tag": "access-tag-1",
            "requested_on": "2023-04-28T00:00:00Z",
            "accessCategory": "cat2",
            "accessMeta": "meta2",
        },
        {
            "requestId": "456_request1",
            "club_id": "456",
            "userEmail": "user3@example.com",
            "accessReason": "reason3",
            "access_desc": "desc3",
            "access_tag": "access-tag-1",
            "requested_on": "2023-04-27T00:00:00Z",
            "accessCategory": "cat3",
            "accessMeta": "meta3",
        },
    ]


@given("individual_pending_requests is empty")
def step_impl(context):
    """individual_pending_requests is empty."""
    context.individual_pending_requests = []
    context.access_tag = "access-tag-1"


@when("process_individual_requests is called")
def step_impl(context, mocker):
    """process_individual_requests is called."""
    context.individual_requests = []
    access_tag = context.access_tag
    mocker.patch("Access.helpers.sla_breached", return_value=True)
    accessrequest_helper.process_individual_requests(
        context.individual_pending_requests, context.individual_requests, access_tag
    )


@then(
    "each entry should have club_id, userEmail, accessReason, accessType, requested_on, sla_breached, accessData"
)
def step_impl(context):
    """each entry should have club_id, userEmail, accessReason, accessType, requested_on, sla_breached, accessData."""
    for request in context.individual_requests:
        for club_request in request["requests"]:
            assert club_request["club_id"]
            assert club_request["userEmail"]
            assert club_request["accessReason"]
            assert club_request["accessType"]
            assert club_request["requested_on"]
            assert club_request["sla_breached"]


@then(
    'individual_requests should contain a single entry with module_tag "access-tag-1"'
)
def step_impl(context):
    """individual_requests should contain a single entry with module_tag "access-tag-1"."""
    assert len(context.individual_requests) == 1
    assert context.individual_requests[0]["module_tag"] == "access-tag-1"


@then(
    'individual_requests should contain one entry for each club with module_tag "access-tag-1"'
)
def step_impl(context):
    """individual_requests should contain one entry for each club with module_tag "access-tag-1"."""
    assert len(context.individual_requests[0]["requests"]) == 2
    club_ids = set(["123", "456"])
    for request in context.individual_requests:
        assert request["module_tag"] == "access-tag-1"
        assert request["requests"]
        club_id = request["requests"][0]["club_id"]
        assert club_id in club_ids
        club_ids.remove(club_id)


@then("individual_requests should remain unchanged")
def step_impl(context):
    """individual_requests should remain unchanged."""
    assert len(context.individual_requests) == 0


@then(
    "the accessData for each entry should contain all the pending requests for the corresponding club."
)
def step_impl(context):
    """the accessData for each entry should contain all the pending requests for the corresponding club.."""
    for request in context.individual_requests:
        for club_request in request["requests"]:
            club_id = club_request["club_id"]
            access_data = club_request["accessData"]
            for pending_request in context.individual_pending_requests:
                if pending_request["club_id"] == club_id:
                    assert len(pending_request) == 9

            assert len(context.individual_pending_requests) == 3


@then("the accessData should contain all the pending requests for the club")
def step_impl(context):
    """the accessData should contain all the pending requests for the club."""
    assert len(context.individual_requests[0]["requests"][0]["accessData"]) == 2
    assert (
        context.individual_requests[0]["requests"][0]["accessData"][0]["requestId"]
        == "123_1"
    )
    assert (
        context.individual_requests[0]["requests"][0]["accessData"][1]["requestId"]
        == "123_2"
    )


@then('the entry should have club_id "123"')
def step_impl(context):
    """the entry should have club_id "123"."""
    assert context.individual_requests[0]["requests"][0]["club_id"] == "123"


@then(
    "the entry should have userEmail, accessReason, accessType, requested_on, sla_breached, accessData"
)
def step_impl(context):
    """the entry should have userEmail, accessReason, accessType, requested_on, sla_breached, accessData."""
    request = context.individual_requests[0]["requests"][0]
    assert "userEmail" in request
    assert "accessReason" in request
    assert "accessType" in request
    assert "requested_on" in request
    assert "sla_breached" in request
    assert "accessData" in request
    assert len(request["accessData"]) == 1
    assert request["accessData"][0]["accessCategory"] == "test_access_category"
    assert request["accessData"][0]["accessMeta"] == "test_access_meta"
    assert request["accessData"][0]["requestId"] == "123_request_1"
