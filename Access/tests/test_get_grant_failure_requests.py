"""test get_grant_fail_requests feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)

import pytest
from .. import accessrequest_helper
from Access import helpers
import Access
from Access.models import User
from Access.models import UserAccessMapping
from django.db.models.query import QuerySet

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

@scenario('./features/get_grant_failed_requests.feature', 'Handling errors')
def test_handling_errors():
    """Handling errors."""
    pass


@scenario('./features/get_grant_failed_requests.feature', 'Retrieving all grant failure requests')
def test_retrieving_all_grant_failure_requests():
    """Retrieving all grant failure requests."""
    pass


@given('an error occurs while executing the method')
def step_impl(mocker,context):
    """an error occurs while executing the method."""
    mock_response = {"error": "Error in request not found OR Invalid request type"}

    context.mock_user_access_mapping = mocker.MagicMock(spec=UserAccessMapping)
    context.mock_user = mocker.MagicMock(spec=User)
    orderByPatch = mocker.MagicMock()

    mock_response = {"error": "Error in request not found OR Invalid request type"}
    mocker.patch(
        "Access.accessrequest_helper.process_error_response", return_value=mock_response
    )
    mock_exception = Exception("Error in request not found OR Invalid request type")
    orderByPatch.order_by.return_value = mocker.MagicMock()
    mocker.patch(
            "Access.models.UserAccessMapping.objects.filter", side_effect=mock_exception,
        )


@given('there are grant failure requests in the database')
@pytest.mark.django_db
def step_impl(mocker,context):
    """there are grant failure requests in the database."""
    context.mock_user_access_mapping = mocker.MagicMock(spec=UserAccessMapping)
    context.mock_user = mocker.MagicMock(spec=User)
    orderByPatch = mocker.MagicMock()
    orderByPatch.order_by.return_value = mocker.MagicMock()
    mocker.patch(
            "Access.models.UserAccessMapping.objects.filter", return_value=orderByPatch
        )
    queryset_mock = mocker.MagicMock()
    context.request.GET.get.return_value = False
    mocker.patch("Access.models.User.objects.get",return_value=mocker.MagicMock())
    queryset_mock.filter.order_by.return_value="request_1"
    

@when('the get_grant_failed_requests method is called')
def step_impl(mocker,new_request,context):
    """the get_grant_failed_requests method is called."""
    context.request = mocker.MagicMock()
    context.result = accessrequest_helper.get_grant_failed_requests(context.request)

@then('it should return a context containing all grant failure requests sorted by requested_on date in descending order')
def step_impl(mocker,context):
    """it should return a context containing all grant failure requests sorted by requested_on date in descending order."""
    assert context.result['failures'] is not None

@then('it should return an error response with details of the error.')
def step_impl(mocker,context):
    """it should return an error response with details of the error.."""
    assert context.result == {
        "error": "Error in request not found OR Invalid request type"
    }









# from behave import given, when, then
# from myapp.utils import get_grant_failed_requests

# @given('an error occurs while executing the method')
# def step_given_error_occurs(context):
#     # Implement the necessary setup or mock the error condition
#     # For example, raise an exception to simulate an error
#     context.error = Exception("An error occurred")

# @when('the get_grant_failed_requests method is called')
# def step_when_get_grant_failed_requests_called(context):
#     # Call the get_grant_failed_requests method
#     request = context.request
#     try:
#         context.result = get_grant_failed_requests(request)
#     except Exception as e:
#         context.error = e

# @then('it should return an error response with details of the error')
# def step_then_check_error_response(context):
#     # Check if an error occurred and validate the error response
#     assert context.error is not None
#     # You can further customize this step to validate the error response details,
#     # such as specific error message or status code, based on your application's error handling logic
#     # For example, assert context.error.message == "An error occurred"
#     pass
