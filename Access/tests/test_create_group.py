from pytest_bdd import scenario, given, when, then
from django.http import QueryDict
from Access.group_helper import create_group, NEW_GROUP_CREATE_ERROR_GROUP_EXISTS, NEW_GROUP_CREATE_SUCCESS_MESSAGE
import pytest
import Access
from Access import notifications

@pytest.fixture
def new_request(mocker):
    req = mocker.MagicMock()
    req.user.user = mocker.MagicMock(spec=Access.models.User)
    req.user.email = "test_user@test.com"
    return req

@scenario('./features/create_group.feature', 'Create a new Group with duplicate name')
def test_create_group_error():
    pass

@scenario('./features/create_group.feature', 'Create a new Group Success')
def test_create_group_success():
    pass


@given("A group name", target_fixture="new_group_name")
def group_name():
    return "testGroupName"

@given("It already exists")
def group_already_exists(mocker):
     mocker.patch("Access.models.GroupV2.group_exists", return_value=[mocker.MagicMock()])


@given("It does not exists in DB")
def group_does_not_exists(mocker):
     mocker.patch("Access.models.GroupV2.group_exists", return_value=[])


@given("The group can be saved", target_fixture="mock_group")
def group_is_saved(mocker):
    mock_group = mocker.MagicMock(spec=Access.models.GroupV2)
    mocker.patch("Access.models.GroupV2.create", return_value = mock_group)
    return mock_group

@given("Requester can be added to the group by default")
def add_user_to_group(mock_group, new_group_name):
    mock_group.add_member.return_value = True
    mock_group.name = new_group_name

@given("Notification can be sent")
def send_notification(mocker):
    mocker.patch("Access.notifications.send_new_group_create_notification", return_value = "")

@when("I pass request", target_fixture="context_output")
def add_group(new_request, new_group_name):
    new_request.POST = QueryDict("newGroupName=" + new_group_name + "&requiresAccessApprove=true&newGroupReason=['test reason']")
    return create_group(new_request)

@then("I should get an error message")
def check_error(context_output, new_group_name):
    context = {}
    context["error"] = {
        "error_msg": NEW_GROUP_CREATE_ERROR_GROUP_EXISTS["error_msg"],
        "msg": NEW_GROUP_CREATE_ERROR_GROUP_EXISTS["msg"].format(group_name= new_group_name),
    }
    assert context_output == context
    assert Access.models.GroupV2.group_exists.call_count==1

@then("I should a get a success message")
def check_success(context_output, new_group_name, mock_group):
    context = {}
    context["status"] = {
        "title": NEW_GROUP_CREATE_SUCCESS_MESSAGE["title"],
        "msg": NEW_GROUP_CREATE_SUCCESS_MESSAGE["msg"].format(group_name = new_group_name),
    }
    assert context_output == context
    assert Access.models.GroupV2.group_exists.call_count==1
    assert Access.models.GroupV2.create.call_count==1
    assert mock_group.add_member.call_count == 1
    assert notifications.send_new_group_create_notification.call_count == 1