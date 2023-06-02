"""Validate Approver Permission feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
from Access.accessrequest_helper import validate_approver_permissions
import pytest


@pytest.fixture
def context(mocker):
    context = mocker.MagicMock()
    return context


@pytest.fixture
def access_mapping(mocker):
    access_mapping = mocker.MagicMock()
    access_mapping.access.access_lable = "test-lable"
    return access_mapping


@pytest.fixture
def request_1(mocker):
    request_1 = mocker.MagicMock()
    return request_1


@pytest.fixture
def access_type(mocker):
    access_type = mocker.MagicMock()
    return access_type


@scenario(
    "features/validate_approver_permissions.feature",
    "User who made the request does not have any approver access & access_mapping is not in pending state & module does not need secondary approval",
)
def test_user_who_made_the_request_does_not_have_any_approver_access__access_mapping_is_not_in_pending_state__module_does_not_need_secondary_approval():
    """User who made the request does not have any approver access & access_mapping is not in pending state & module does not need secondary approval."""
    pass


@scenario(
    "features/validate_approver_permissions.feature",
    "User who made the request has primary approver access & access_mapping is not in pending state & module does not need secondary approval",
)
def test_user_who_made_the_request_has_primary_approver_access__access_mapping_is_not_in_pending_state__module_does_not_need_secondary_approval():
    """User who made the request has primary approver access & access_mapping is not in pending state & module does not need secondary approval."""
    pass


@scenario(
    "features/validate_approver_permissions.feature",
    "User who made the request has primary approver access & access_mapping is not in pending state & module supports secondary approval",
)
def test_user_who_made_the_request_has_primary_approver_access__access_mapping_is_not_in_pending_state__module_supports_secondary_approval():
    """User who made the request has primary approver access & access_mapping is not in pending state & module supports secondary approval."""
    pass


@scenario(
    "features/validate_approver_permissions.feature",
    "User who made the request has secondary approver access & access_mapping is not in pending state & module supports secondary approval",
)
def test_user_who_made_the_request_has_secondary_approver_access__access_mapping_is_not_in_pending_state__module_supports_secondary_approval():
    """User who made the request has secondary approver access & access_mapping is not in pending state & module supports secondary approval."""
    pass


@scenario(
    "features/validate_approver_permissions.feature",
    "When the user who made the request has primary approver access & access_mapping is in pending state & module does needs secondary approval",
)
def test_when_the_user_who_made_the_request_has_primary_approver_access__access_mapping_is_in_pending_state__module_does_needs_secondary_approval():
    """When the user who made the request has primary approver access & access_mapping is in pending state & module does needs secondary approval."""
    pass


@scenario(
    "features/validate_approver_permissions.feature",
    "When the user who made the request has primary approver access & access_mapping is in pending state & module does not need secondary approval",
)
def test_when_the_user_who_made_the_request_has_primary_approver_access__access_mapping_is_in_pending_state__module_does_not_need_secondary_approval():
    """When the user who made the request has primary approver access & access_mapping is in pending state & module does not need secondary approval."""
    pass


@scenario(
    "features/validate_approver_permissions.feature",
    "When the user who made the request has secondary approver access & access_mapping is in primary pending state & module does needs secondary approval",
)
def test_when_the_user_who_made_the_request_has_secondary_approver_access__access_mapping_is_in_primary_pending_state__module_does_needs_secondary_approval():
    """When the user who made the request has secondary approver access & access_mapping is in primary pending state & module does needs secondary approval."""
    pass


@scenario(
    "features/validate_approver_permissions.feature",
    "_get_approver_permissions raises an Exception, the function should return error message as json",
)
def test__get_approver_permissions_raises_an_exception_the_function_should_return_error_message_as_json():
    """_get_approver_permissions raises an Exception, the function should return error message as json."""
    pass


@given("Modules does not need secondary approval")
def step_impl(access_mapping):
    """Modules does not need secondary approval."""
    access_mapping.is_secondary_pending.return_value = True


@given("Modules supports secondary approval")
def step_impl(access_mapping):
    """Modules supports secondary approval."""
    access_mapping.is_secondary_pending.return_value = True


@given("User who made request has primary approver access")
def step_impl(context, mocker, access_mapping, request_1):
    """User who made request has primary approver access."""
    mock_permissions = {"approver_permissions": {"1": "ACCESS_APPROVE", "2": ""}}
    mocker.patch(
        "Access.accessrequest_helper._get_approver_permissions",
        return_value=mock_permissions,
    )
    request_1.user.user.has_permission.return_value = True


@given("User who made request has primary approver access with false response")
def step_impl(context, mocker, access_mapping, request_1):
    """User who made request has primary approver access."""
    mock_permissions = {"approver_permissions": {"1": "ACCESS_APPROVE", "2": ""}}
    mocker.patch(
        "Access.accessrequest_helper._get_approver_permissions",
        return_value=mock_permissions,
    )
    request_1.user.user.has_permission.return_value = False


@given("User who made request has secondary approver access")
def step_impl(mocker, context, access_mapping, request_1):
    mock_permissions = {"approver_permissions": {"1": "", "2": "ACCESS_APPROVE"}}
    mocker.patch(
        "Access.accessrequest_helper._get_approver_permissions",
        return_value=mock_permissions,
    )
    request_1.user.user.has_permission.return_value = True


@given("User who made request has only secondary approver access with false response")
def step_impl(mocker, context, access_mapping, request_1):
    mock_permissions = {"approver_permissions": {"1": "", "2": "ACCESS_APPROVE"}}
    mocker.patch(
        "Access.accessrequest_helper._get_approver_permissions",
        return_value=mock_permissions,
    )
    request_1.user.user.has_permission.return_value = False


@given("User who made request not have any approver access")
def step_impl(mocker, request_1):
    mock_permissions = {"approver_permissions": {"1": "", "2": ""}}
    mocker.patch(
        "Access.accessrequest_helper._get_approver_permissions",
        return_value=mock_permissions,
    )
    request_1.user.user.has_permission.return_value = False


@given("_get_approver_permissions raises an exception when called")
def step_impl(mocker):
    """_get_approver_permissions raises an exception when called."""
    mock_response = {"error": "Error in request not found OR Invalid request type"}
    mocker.patch(
        "Access.accessrequest_helper.process_error_response", return_value=mock_response
    )
    mock_exception = Exception("Error in request not found OR Invalid request type")
    mocker.patch(
        "Access.accessrequest_helper._get_approver_permissions",
        side_effect=mock_exception,
    )


@given("access_mapping is in pending state")
def step_impl(access_mapping, mocker):
    """access_mapping is in pending state."""
    print("here in pending true")
    access_mapping.is_pending.return_value = True


@given("access_mapping is not in pending state")
def step_impl(access_mapping, mocker):
    """access_mapping is not in pending state."""
    access_mapping.is_pending.return_value = False


@when("validate_approver_permissions function is called", target_fixture="response")
def step_impl(mocker, access_mapping, context, access_type, request_1):
    """validate_approver_permissions function is called."""
    return validate_approver_permissions(access_mapping, access_type, request_1)


@then("Return value should be empty json")
def step_impl(response):
    """Return value should be empty json."""
    assert response == {}


@then("Return value should be error json")
def step_impl(response):
    """Return value should be error json."""
    assert response == {"error": "Error in request not found OR Invalid request type"}


@then("Return value should be permission denied json")
def step_impl(response):
    """Return value should be permission denied json."""
    assert response == {"error": "Permission Denied!"}
