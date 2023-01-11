import pytest
from Access.userlist_helper import getallUserList, bulk_approve, update_user, ERROR_MESSAGE, EXCEPTION_USER_UNAUTHORIZED
from Access import models
from django.http import HttpRequest, QueryDict

class MockUserModelobj:
    def __init__(self, user= "", name=""):
        self.user = user
        self.name = name
        self.ssh_public_key = MockSshPublicKey()

    def get(self, user__username=""):
        self.user = user__username
        return MockUserModelobj(user="username")

    def update_module_credentials(self, key="", value=""):
      self.key = key
      self.value = value
      return True

class MockRequestId:
        def __init__(self):
            self.request_id = "request_id"
            self.access_tag = ""


class MockUserAccessMapping:
    def __init__(self, request_id="", user="", access="", approver_1="", approver_2="", request_reason="", access_type="", status=""):
        self.request_id = request_id
        self.user = user
        self.access = access
        self.approver_1 = approver_1
        self.approver_2 = approver_2
        self.request_reason = request_reason
        self.access_type = access_type
        self.status = status
        self.request_id = MockRequestId()

    def save(self):
      return True

class MockSshPublicKey:
  def __init__(self, key="", status=""):
        self.key = key
        self.status = status

  def save(self):
      return True

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


@pytest.mark.parametrize("testname , userMapping , expectedMessage",

    [
      ("test_bulk_approve_success", [MockUserAccessMapping(
            request_id="request_id1",
            user="user1",
            access="access1",
            approver_1="approver_1",
            approver_2="approver_2",
            request_reason="reason1",
            access_type="type1_access",
            status="status1",
        )], 'Details updated.'),
      ("test_bulk_approve_noAccess", [], 'Request access. No details found.'),
    ]
)
def test_bulk_approve(mocker, testname, userMapping, expectedMessage):
  request = mocker.MagicMock()
  request.user = "username"
  models.User.objects = MockUserModelobj()
  mocker.patch("Access.models.UserAccessMapping.objects.filter", return_value=userMapping)

  if testname == "test_bulk_approve_success":
    mappingObj = mocker.MagicMock()
    mappingObj.access.access_tag = "tagname"
    mappingObj.user = "user"
    mappingObj.approver_1.user.username = "approver"
    mappingObj.request_id = "requestid"
    mocker.patch("Access.models.UserAccessMapping.objects.get", return_value = mappingObj)
    mock_thread = mocker.MagicMock()
    mock_thread.start.return_value = True
    mocker.patch("threading.Thread", return_value = mock_thread)
  else:
    mocker.patch("threading.Thread", return_value = False)

  context = bulk_approve(request, ['type1_access, type2_access'])
  assert context["status"]["msg"]  == expectedMessage

@pytest.mark.parametrize("testname , userMapping , expectedMessage , postData, expectedError",

    [
      ("test_update_all", [MockUserAccessMapping(
            request_id="request_id1",
            user="user1",
            access="access1",
            approver_1="approver_1",
            approver_2="approver_2",
            request_reason="reason1",
            access_type="type1_access",
            status="status1",
        )],
        'Confluence Username updated.\nSlack Username updated.\nZoom Username updated.\nAWS Username updated.\nOpsgenie Username updated.\nGCP Username updated.\nGIT Username updated.\nSSH Key updated.\n',
        'confluenceusername=user1&slackusername=user1&zoomusername=user1&awsusername=user1&opsgenieusername=user1&gcpusername=user1&gitusername=user1&ssh_pub_key=ssh-rsa',
        False,
      ),
      ("test_update_ssh", [MockUserAccessMapping(
            request_id="request_id1",
            user="user1",
            access="access1",
            approver_1="approver_1",
            approver_2="approver_2",
            request_reason="reason1",
            access_type="type1_access",
            status="status1",
        )],
        'SSH Key updated.\n',
        'confluenceusername=user2&slackusername=user2&zoomusername=user2&awsusername=user2&opsgenieusername=user2&gcpusername=user2&gitusername=user2&ssh_pub_key=ssh-rsa',
        False,
      ),
      ("test_update_error", [MockUserAccessMapping()],
        'Error ocurred while updating details.',
        'confluenceusername=user2&slackusername=user2&zoomusername=user2&awsusername=user2&opsgenieusername=user2&gcpusername=user2&gitusername=user2&ssh_pub_key=ssh-rsa',
        True,
      ),
    ]
)
def test_update_user(mocker,testname,userMapping,expectedMessage,postData,expectedError):
  request = HttpRequest()
  request.user = "username"
  request.POST = QueryDict(postData)

  MockUserModelobj.has_module_credentials = {
    'gitusername': 'user2',
    'confluenceusername': 'user2',
    'awsusername': 'user2',
    'opsgenieusername': 'user2',
    'gcpusername': 'user2',
    'slackusername': 'user2',
    'zoomusername': 'user2',
    'ssh_public_key': {
      'key': 'ssh-rsa2'
    }
  }

  models.User.objects = MockUserModelobj()
  mocker.patch("Access.models.SshPublicKey.objects.create",return_value=MockSshPublicKey(key="new_key",status="new_status"))
  mocker.patch("Access.models.UserAccessMapping.objects.filter", return_value=userMapping)
  if expectedError:
    MockSshPublicKey.save = False

  context = update_user(request)
  print(context)

  if expectedError:
    assert context["error"]["error"]  == expectedMessage
  else:
    assert context["status"]["msg"]  == expectedMessage
