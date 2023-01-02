from Access.views_helper import generateUserMappings, executeGroupAccess, getAccessHistory
from Access.views import showAccessHistory
from Access.models import User
from Access import models, helpers
import pytest
from Access import views_helper
from bootprocess import general
import logging

from django.contrib.auth import get_user_model
from django.test import RequestFactory

class MockAuthUser:
    def __init__(self, username="", user=""):
        self.user = user
        self.username = username


class MockRequest:
    def __init__(self, username=""):
        self.user = MockAuthUser(username)


def test_generateUserMappings(mocker):
    class MemberShipObj:
        def __init__(self, membership_id="", reason=""):
            self.membership_id = membership_id
            self.reason = reason

    class AuthUser:
        def __init__(self, username):
            self.username = username
            self.user = username

    class User:
        def __init__(self, user=""):
            self.user = AuthUser(username="")

    class MockAccess:
        def __init__(self):
            self.access_tag = ""

    class MockGroupAccessMapping:
        def __init__(self, access="", approver_1="", approver_2="", request_reason=""):
            self.access = access
            self.approver_1 = approver_1
            self.approver_2 = approver_2
            self.request_reason = request_reason
            self.access = MockAccess()

    class MockUserAccessMapping:
        def __init__(
            self,
            request_id="",
            user="",
            access="",
            approver_1="",
            approver_2="",
            request_reason="",
            access_type="",
            status="",
        ):
            self.request_id = request_id
            self.user = user
            self.access = access
            self.approver_1 = approver_1
            self.approver_2 = approver_2
            self.request_reason = request_reason
            self.access_type = access_type
            self.status = status

        def __len__(self):
            return 1

    def values_list(*args, **kwargs):
        return [""]

    mock_objects = mocker.MagicMock(name="objects")
    mock_objects.values_list = values_list
    mocker.patch(
        "Access.models.GroupAccessMapping.objects.filter",
        return_value=[MockGroupAccessMapping()],
    )
    groupAccessMappingSpy = mocker.spy(models.GroupAccessMapping.objects, "filter")

    mocker.patch(
        "Access.models.UserAccessMapping.objects.filter",
        return_value=mock_objects,
        side_effect=mocker.patch(
            "Access.models.UserAccessMapping.objects.filter", return_value=mock_objects
        ),
    )
    userAccessMappingFilterSpy = mocker.spy(models.UserAccessMapping.objects, "filter")

    mocker.patch(
        "Access.models.UserAccessMapping.objects.create",
        return_value=MockUserAccessMapping(
            request_id="request_id1",
            user="user1",
            access="access2",
            approver_1="approver_1",
            approver_2="approver_2",
            request_reason="reason123",
            access_type="access_type",
            status="status1",
        ),
    )
    userAccessMappingCreateSpy = mocker.spy(models.UserAccessMapping.objects, "create")

    usermappingList = generateUserMappings(
        User(user="username1"),
        MemberShipObj(),
        MemberShipObj(membership_id="1", reason="reason"),
    )

    assert usermappingList[0].request_id == "request_id1"
    assert groupAccessMappingSpy.call_count == 1
    assert userAccessMappingFilterSpy.call_count == 2
    assert userAccessMappingCreateSpy.call_count == 1


@pytest.mark.parametrize(
    "testName, userstate, requestid, expectedStatus, expected_decline_reason",
    [
        (
            "User is Active",
            "active",
            "other",
            "Declined",
            "Auto decline for 'Other Access'. Please replace this with correct access.",
        ),
        ("User is Active", "inactive", "", "Declined", "User is not active"),
    ],
)
def test_executeGroupAccess(
    mocker, testName, userstate, requestid, expectedStatus, expected_decline_reason
):
    userMock = mocker.MagicMock()
    userMock.username = "username"
    userMock.current_state.return_value = userstate

    mappingObj = mocker.MagicMock()
    mappingObj.access.access_tag = "tagname"
    mappingObj.user = userMock
    mappingObj.approver_1.user = userMock
    mappingObj.request_id = requestid
    executeGroupAccess([mappingObj])
    assert mappingObj.status == expectedStatus
    assert mappingObj.decline_reason == expected_decline_reason


@pytest.mark.parametrize(
    """testName, userstate, requestid,user_state,
    approvalResponse ,expectedStatus, emailSesCallCount,""",
    [
        (
            "User is Active, request is not other, user.state not 1",
            "active",
            "reqid",
            "2",
            None,
            "Declined",
            0,
        ),
        (
            "User is Active, request is not other, user.state is 1, Approval Returns true",
            "active",
            "reqid",
            "1",
            True,
            "Approved",
            0,
        ),
        (
            "User is Active, request is not other, user.state is 1, Approval Fails",
            "active",
            "reqid",
            "1",
            [False, "Failure Message"],
            "GrantFailed",
            1,
        ),
    ],
)
def test_executeGroupAccess_run_access_grant(
    mocker,
    testName,
    userstate,
    approvalResponse,
    requestid,
    user_state,
    expectedStatus,
    emailSesCallCount,
):
    views_helper.logger = logging.getLogger(__name__)
    mockAccessModule = mocker.MagicMock()
    mockAccessModule.tag.return_value = "tagname"
    mockAccessModule.approve.return_value = approvalResponse
    mockAccessModule.access_mark_revoke_permission.return_value = "destination"

    userMock = mocker.MagicMock()
    userMock.username = "username"
    userMock.current_state.return_value = userstate
    userMock.state = user_state

    mappingObj = mocker.MagicMock()
    mappingObj.access.access_tag = "tagname"
    mappingObj.user = userMock
    mappingObj.approver_1.user = userMock
    mappingObj.request_id = requestid
    mappingObj.status = ""
    mappingObj.decline_reason = ""

    mocker.patch("bootprocess.general.emailSES", return_value="")
    emailSES_Spy = mocker.spy(general, "emailSES")

    views_helper.all_access_modules = [mockAccessModule]

    executeGroupAccess([mappingObj])
    assert mappingObj.status == expectedStatus
    assert emailSES_Spy.call_count == emailSesCallCount

@pytest.mark.django_db
def test_show_access_history(mocker):

    # save user with email='test@test.com' to the database 
    djangoUser = get_user_model()
    # Create a test user
    test_auth_user = djangoUser.objects.create(
        username='testuser', email='test@test.com', password='testpass'
    )
    test_auth_user.save()

    # Set up test data
    user = User()
    user.user_id = '1'
    user.gitusername = '123'
    user.name = 'testuser'
    user.password = 'testpass'
    user.email = 'test@test.com'
    user.state = 1
    user.save()

    # mark the user as authenticated to bypass the login_required decorator
    user.is_authenticated = True

    # use RequestFactory to create a request object
    factory = RequestFactory()
    request = factory.get('/access/showAccessHistory')
    request.user = user
    response = showAccessHistory(request)

    # Assert that the response is successful
    assert response.status_code == 200

    # assert 'access_history' in response.content.decode('utf-8')
    assert 'Request History' in response.content.decode('utf-8')


@pytest.mark.django_db
def test_get_access_history(mocker):

    # save user with email='test@test.com' to the database 
    djangoUser = get_user_model()
    # Create a test user
    test_auth_user = djangoUser.objects.create(
        username='testuser', email='test@test.com', password='testpass'
    )
    test_auth_user.save()

    # Set up test data
    user = User()
    user.user_id = '1'
    user.gitusername = '123'
    user.name = 'testuser'
    user.password = 'testpass'
    user.email = 'test@test.com'
    user.state = 1
    user.save()

    # create a user
    userMock = mocker.MagicMock()
    userMock.username = "approver1"

    mappingObj = mocker.MagicMock()
    mappingObj.access.access_tag = "tagname"
    mappingObj.user = user
    mappingObj.approver_1.user = userMock
    mappingObj.approver_2.user = userMock
    mappingObj.request_id = "requestid"
    mappingObj.request_reason = "Test request"
    mappingObj.status = "Approved"
    mappingObj.decline_reason = ""

    # create another user
    userMock2 = mocker.MagicMock()
    userMock2.username = "approver2"

    mappingObj2 = mocker.MagicMock()
    mappingObj2.access.access_tag = "tagname"
    mappingObj2.user = user
    mappingObj2.approver_1.user = userMock2
    mappingObj2.approver_2.user = userMock2
    mappingObj2.request_id = "requestid 2"

    # mock query db for user whose email = "test@exmaple.com"
    mocker.patch(
        "Access.models.UserAccessMapping.objects.filter",
        return_value=[mappingObj, mappingObj2],
    )
    userAccessMappingFilterSpy = mocker.spy(models.UserAccessMapping.objects, "filter")

    # mock so that access_details = helper.getAccessRequestDetails(data) line in getAccessHistory() returns a dict with key 'accessType' and value 'accessTypeValue' 
    mocker.patch(
        "Access.helpers.getAccessRequestDetails",
        return_value={
            "accessType": "accessTypeValue",
            "accessCategory": "accessCategoryValue",
            "accessMeta": "accessMetaValue",
        },
    )

    # import helpers module and spy on getAccessRequestDetails() function
    getAccessRequestDetailsSpy = mocker.spy(helpers, "getAccessRequestDetails")

    request = mocker.MagicMock()
    request.user = user
    context = getAccessHistory(request)

    assert len(context['dataList']) == 2

    assert userAccessMappingFilterSpy.call_count == 1
    assert getAccessRequestDetailsSpy.call_count == 2

    assert context['dataList'][0]['id'] == "requestid"
    assert context['dataList'][0]['type'] == "accessTypeValue"
    assert context['dataList'][0]['access'] == 'accessCategoryValue details: "accessMetaValue"'
    assert context['dataList'][0]['status'] == "Approved"
    assert context['dataList'][0]['reason'] == "Test request"
    assert context['dataList'][0]['decline_reason'] == ""
    assert context['dataList'][0]['approver'] == "1: "+userMock.username+"\n2: "+userMock.username

    assert context['dataList'][1]['id'] == "requestid 2"
    assert context['dataList'][1]['type'] == "accessTypeValue"
    assert context['dataList'][1]['access'] == 'accessCategoryValue details: "accessMetaValue"'
    assert context['dataList'][1]['approver'] == "1: "+userMock2.username+"\n2: "+userMock2.username
