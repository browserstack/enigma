import pytest
from Access.userlist_helper import getallUserList, ERROR_MESSAGE, EXCEPTION_USER_UNAUTHORIZED

#TESTCASE NAMES
UserIsNotAuthorized = "UserIsNotAuthorized"
UserIsAuthorized = "UserIsAuthorized"

@pytest.mark.parametrize("testname, UserHasPermission, UserHasOffboardPermission,expectedError",
                        
    [
        # user does not have permission to view the page
        (UserIsNotAuthorized, False, False,True),
        # user is authorized, and has offboard access
        (UserIsAuthorized, True, True, False),
        # user is authorized, but does not have offboard access
        (UserIsAuthorized, True, False, False)
    ])
def test_getallUserList(mocker, testname ,UserHasPermission, UserHasOffboardPermission, expectedError):
    request = mocker.MagicMock()
    userMock = mocker.MagicMock()
    if testname == UserIsNotAuthorized:
        mocker.patch("Access.helpers.check_user_permissions", return_value=UserHasPermission)
        request.user = userMock

    elif testname == UserIsAuthorized:
        
        userMock.name = "UserNickName"
        userMock.user.name = "UserNickName"
        userMock.user.first_name = "UserFirstName"
        userMock.user.last_name = "UserLastName"
        userMock.email = "UserEmail"
        userMock.user.username = "UserName1"
        userMock.gitusername = "GitUserName"
        userMock.offbaord_date = "TodaysDate"
        userMock.current_state.return_value = "Active"
        userMock.user.is_active = True
        userMock.user.has_permission.return_value = UserHasOffboardPermission
        
        request.user = userMock

        
        mocker.patch("Access.helpers.check_user_permissions", return_value=UserHasPermission)
        mocker.patch("Access.models.User.objects.all", return_value=[userMock])

    context = getallUserList(request)
    if expectedError:
        assert context["error"]["msg"]  == ERROR_MESSAGE
        assert context["error"]["error_msg"]  == EXCEPTION_USER_UNAUTHORIZED
    else:
        assert context["dataList"][0]["name"] == userMock.name
        assert context["dataList"][0]["first_name"] == userMock.user.first_name
        assert context["dataList"][0]["last_name"] == userMock.user.last_name
        assert context["dataList"][0]["email"] == userMock.email
        assert context["dataList"][0]["username"] == userMock.user.username
        assert context["dataList"][0]["git_username"] == userMock.gitusername
        assert context["dataList"][0]["offbaord_date"] == userMock.offbaord_date
        assert context["dataList"][0]["state"] == userMock.current_state()
        assert context["dataList"][0]["is_active"] == userMock.user.is_active
        if UserHasOffboardPermission:
            assert context["viewDetails"]["numColumns"] == 8
        else:
            assert context["viewDetails"]["numColumns"] == 7



