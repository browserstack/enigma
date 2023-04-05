"""Get Request Access feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
import pytest
from .. import accessrequest_helper
from Access import helpers


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


@scenario(
    "features/get_request_access.feature", "get_access_request returns correct response"
)
def test_get_access_request_returns_correct_response():
    """get_access_request returns correct response."""
    pass


@scenario(
    "features/get_request_access.feature",
    "get_access_request returns correct response with extra fields",
)
def test_get_access_request_returns_correct_response_with_extra_fields():
    """get_access_request returns correct response with extra fields."""
    pass


@scenario(
    "features/get_request_access.feature",
    "get_access_request returns correct response with notice/alert",
)
def test_get_access_request_returns_correct_response_with_noticealert():
    """get_access_request returns correct response with notice/alert."""
    pass


@scenario(
    "features/get_request_access.feature",
    "get_request_access is called with invalid parameters",
)
def test_get_request_access_is_called_with_invalid_parameters():
    """get_request_access is called with invalid parameters."""
    pass


@scenario(
    "features/get_request_access.feature",
    "get_request_access is called with invalid request type",
)
def test_get_request_access_is_called_with_invalid_request_type():
    """get_request_access is called with invalid request type."""
    pass


@scenario("features/get_request_access.feature", "verify generic form key")
def test_verify_generic_form_key():
    """verify generic form key."""
    pass


@scenario(
    "features/get_request_access.feature",
    "verify response with array of access list with all elements",
)
def test_verify_response_with_array_of_access_list_with_all_elements():
    """verify response with array of access list with all elements."""
    pass


@scenario(
    "features/get_request_access.feature",
    "verify response with array of access list with empty elements",
)
def test_verify_response_with_array_of_access_list_with_empty_elements():
    """verify response with array of access list with empty elements."""
    pass


@scenario(
    "features/get_request_access.feature",
    "verify response with array of access list with two elements",
)
def test_verify_response_with_array_of_access_list_with_two_elements():
    """verify response with array of access list with two elements."""
    pass


@given("empty configured access_modules are There")
def step_impl(context, mocker):
    # Mock the get_available_access_modules function to return an empty dictionary
    get_available_access_modules = mocker.MagicMock(return_value={})
    context.get_available_access_modules = get_available_access_modules


@given("four configured access_modules are There")
def step_impl(mocker, context):
    mocked_modules = {
        "access_tag1": mocker.MagicMock(),
        "access_tag2": mocker.MagicMock(),
        "access_tag3": mocker.MagicMock(),
        "access_tag4": mocker.MagicMock(),
    }
    mocker.patch(
        "Access.helpers.get_available_access_modules", return_value=mocked_modules
    )


@given("get_request does not have accesses key")
def step_impl(mocker, context):
    """get_request does ot have accesses key."""
    context.request = mocker.MagicMock()
    context.request.GET.getlist.side_effect = KeyError("accesses")


@given("get_request has four modules")
def step_impl(context, mocker):
    context.request = mocker.MagicMock()
    context.request.GET.getlist.return_value = [
        "access_access_tag1",
        "access_access_tag2",
        "access_access_tag3",
        "access_access_tag4",
    ]


@given("get_request has two modules")
def step_impl(context, mocker):
    context.request = mocker.MagicMock()
    context.request.GET.getlist.return_value = [
        "access_access_tag1",
        "access_access_tag2",
    ]


@given("get_request has zero modules")
def step_impl(context, mocker):
    context.request = mocker.MagicMock()
    context.request.GET.getlist.return_value = []


@given("request is post request")
def step_impl(context, mocker):
    context.request = mocker.MagicMock()
    context.request.method = "POST"


@given("two with extra fields and two without extra fields")
def step_impl(context, mocker):
    context.request = mocker.MagicMock()
    context.request.GET.getlist.return_value = [
        "access_access_tag1",
        "access_access_tag2",
        "access_access_tag3",
        "access_access_tag4",
    ]

    access_tag1 = mocker.MagicMock()
    access_tag2 = mocker.MagicMock()
    access_tag3 = mocker.MagicMock()
    access_tag4 = mocker.MagicMock()
    each_module = [access_tag1, access_tag2, access_tag3, access_tag4]
    mocker.patch.object(
        each_module[0], "get_extra_fields", return_value="mocked_extra_fields1"
    )
    mocker.patch.object(
        each_module[1], "get_extra_fields", return_value="mocked_extra_fields2"
    )


@given("two with extra notice/alert and two without notice/alert")
def step_impl(context, mocker):
    context.request = mocker.MagicMock()
    context.request.GET.getlist.return_value = [
        "access_access_tag1",
        "access_access_tag2",
        "access_access_tag3",
        "access_access_tag4",
    ]

    access_tag1 = mocker.MagicMock()
    access_tag2 = mocker.MagicMock()
    access_tag3 = mocker.MagicMock()
    access_tag4 = mocker.MagicMock()
    each_module = [access_tag1, access_tag2, access_tag3, access_tag4]
    mocker.patch.object(each_module[0], "get_notice", return_value="mocked_notice1")
    mocker.patch.object(each_module[1], "get_notice", return_value="mocked_notice2")


@when("get_request_access function is called")
def step_impl(context, mocker):
    # Mock the request object to have an empty query string
    context.response = accessrequest_helper.get_request_access(context.request)


@when("get_request_access function is called for invalid request type")
def step_impl(context, mocker):
    # Mock the request object to have an empty query string
    context.request.GET.getlist.side_effect = KeyError("accesses")
    context.response = accessrequest_helper.get_request_access(context.request)


@then("Return value should be access list with two modules")
def step_impl(context):
    assert context.response["accesses"] is not None

    assert len(context.response["accesses"]) == 2

    for access in context.response["accesses"]:
        assert "formDesc" in access
        assert "accessTag" in access
        assert "accessTypes" in access
        assert "accessRequestData" in access
        assert "extraFields" in access
        assert "notice" in access
        assert "accessRequestPath" in access
    assert helpers.get_available_access_modules.call_count==1


@then("Return value should be empty access list")
def step_impl(context):
    assert context.response == {}


@then("Return value should be error json")
def step_impl(context):
    assert context.response["status"] == {
        "title": "Error Occured",
        "msg": (
            "There was an error in getting the requested access resources. Please"
            " contact Admin"
        ),
    }


@then("Return value should return all four access list with all seven present keynames")
def step_impl(context):
    assert context.response["accesses"] is not None
    assert len(context.response["accesses"]) == 4

    for access in context.response["accesses"]:
        assert "formDesc" in access
        assert "accessTag" in access
        assert "accessTypes" in access
        assert "accessRequestData" in access
        assert "extraFields" in access
        assert "notice" in access
        assert "accessRequestPath" in access
    assert helpers.get_available_access_modules.call_count==1


@then("Return value should return all four access with extra fields")
def step_impl(context):
    assert context.response["accesses"] is not None

    assert len(context.response["accesses"]) == 4

    for access in context.response["accesses"]:
        assert "extraFields" in access
    assert helpers.get_available_access_modules.call_count==1


@then("Return value should return all four access with notice/alert")
def step_impl(context):
    assert context.response["accesses"] is not None

    assert len(context.response["accesses"]) == 4

    for access in context.response["accesses"]:
        assert "notice" in access
    assert helpers.get_available_access_modules.call_count==1
