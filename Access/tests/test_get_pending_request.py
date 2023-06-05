"""features/get_pending_request.feature feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
import Access
import pytest
from Access import accessrequest_helper


@pytest.fixture(autouse=True)
def setup_test_config():
    accessrequest_helper.DECLINE_REASONS = {
        "declineReasons": {
            "reason1": "Not in adherence with Access Management Policy",
            "reason2": "Access can be granted to L3 or above only",
            "reason3": "Duplicate request",
        }
    }


@pytest.fixture
def new_request(mocker):
    req = mocker.MagicMock()
    req.user.user = mocker.MagicMock(spec=Access.models.User)
    req.user.email = "test_user@test.com"
    return req


@pytest.fixture
def context(mocker):
    context = mocker.MagicMock()
    return context


@scenario("./features/get_pending_request.feature", "Error Handling")
def test_error_handling():
    """Error Handling for get-pending-request."""
    pass


@scenario("./features/get_pending_request.feature", "Retrieving All Pending Requests")
def test_retrieving_all_pending_requests():
    """Retrieving All Pending Requests."""
    pass


@given("an error occurs while retrieving the requests")
def step_impl(context, mocker):
    """an error occurs while retrieving the requests."""
    mock_response = {"error": "Error in request not found OR Invalid request type"}
    mocker.patch(
        "Access.accessrequest_helper.process_error_response", return_value=mock_response
    )
    mock_exception = Exception("Error in request not found OR Invalid request type")
    mocker.patch(
        "Access.models.GroupV2.get_pending_creation",
        side_effect=mock_exception,
    )


@given("request to view all pending requests")
def step_impl(context, mocker):
    """request to view all pending requests."""
    mocker.patch(
        "Access.models.GroupV2.get_pending_memberships", return_value=mocker.MagicMock
    )
    mocker.patch("Access.models.GroupV2.get_pending_creation", return_value=[])
    mocker.patch(
        "Access.accessrequest_helper.get_pending_accesses_from_modules",
        return_value=("test-user-1", "test-ser-2"),
    )


@given("request to view pending requests")
def step_impl(context, mocker):
    """request to view pending requests."""
    mocker.patch(
        "Access.models.GroupV2.get_pending_memberships", return_value=mocker.MagicMock
    )
    mocker.patch("Access.models.GroupV2.get_pending_creation", return_value=[])
    mocker.patch(
        "Access.accessrequest_helper.get_pending_accesses_from_modules",
        return_value=("test-user-1", "test-ser-2"),
    )


@when("the `get_pending_requests` method is called")
def step_impl(context, new_request):
    """the `get_pending_requests` method is called."""
    context.request = new_request
    context.result = accessrequest_helper.get_pending_requests(context.request)


@then("all pending access requests from modules")
def step_impl(context):
    """all pending access requests from modules."""
    assert "genericRequests" in context.result
    assert "groupGenericRequests" in context.result
    assert Access.models.GroupV2.get_pending_memberships.call_count == 1
    assert Access.models.GroupV2.get_pending_creation.call_count == 1


@then("return an error response")
def step_impl(context):
    """return an error response."""
    assert context.result is not None
    assert Access.models.GroupV2.get_pending_memberships.call_count == 1
    assert Access.models.GroupV2.get_pending_creation.call_count == 1


@then("return the retrieved requests in the context variable")
def step_impl(context):
    """return the retrieved requests in the context variable."""
    assert context.result is not None


@then("the method should handle the error")
def step_impl(context):
    """the method should handle the error."""
    assert context.result == {
        "error": "Error in request not found OR Invalid request type"
    }


@then("the method should retrieve all pending membership and group creation requests")
def step_impl(context):
    """the method should retrieve all pending membership and group creation requests."""
    assert "membershipPending" in context.result
    assert "newGroupPending" in context.result
