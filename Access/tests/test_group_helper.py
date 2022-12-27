import pytest
from django.http import QueryDict
from Access import models
from Access import group_helper
from unittest.mock import ANY

testGroupName = "testgroupname"
#TESTCASE NAMES
GroupAlreadyExists = "GroupExists"
GroupDoesNotExists_DoesNotNeedsApproval_1 = "GroupDoesNotExists Does not Need Approval"
GroupDoesNotExists_DoesNotNeedsApproval_2 = "GroupDoesNotExists Does not Need Approval with SelectedUserList"
GroupDoesNotExists_NeedsApproval_3 = "GroupDoesNotExists NeedsApproval with SelectedUserList"


@pytest.mark.parametrize("testname,postData,expectedContext, membershipCreationCallCount, needsAccessApprove",
    [
        (
            GroupAlreadyExists,
            "newGroupName=['" + testGroupName + "']",
            "{'error': {'error_msg': 'Invalid Group Name', 'msg': \"A group with name ['" + testGroupName + "'] already exists. Please choose a new name.\"}}",
            0, False
        ),
        (
            GroupDoesNotExists_DoesNotNeedsApproval_1,
            "newGroupName=['" + testGroupName + "']&requiresAccessApprove=false&newGroupReason=['test reason']",
            "{'status': {'title': 'New Group Request submitted', 'msg': \"A request for New Group with name ['" + testGroupName+ "'] has been submitted for approval. You will be notified for any changes in request status.\"}}",
            1, False
        ),
        (
            GroupDoesNotExists_DoesNotNeedsApproval_2,
            "newGroupName=['" + testGroupName + "']&requiresAccessApprove=false&newGroupReason=['test reason']&selectedUserList=user1@user1.com",
            "{'status': {'title': 'New Group Request submitted', 'msg': \"A request for New Group with name ['" + testGroupName+ "'] has been submitted for approval. You will be notified for any changes in request status.\"}}",
            2, False
        ),    
        (
            GroupDoesNotExists_NeedsApproval_3,
            "newGroupName=['" + testGroupName + "']&requiresAccessApprove=true&newGroupReason=['test reason']&selectedUserList=user1@user1.com",
            "{'status': {'title': 'New Group Request submitted', 'msg': \"A request for New Group with name ['" + testGroupName+ "'] has been submitted for approval. You will be notified for any changes in request status.\"}}",
            2, True
        ),            
    ]
)
def test_createGroup(mocker, testname, postData,expectedContext, membershipCreationCallCount, needsAccessApprove):
    request = mocker.MagicMock()
    request.POST = QueryDict(postData)
    
    if testname==GroupAlreadyExists:
        statusFilterPatch = mocker.MagicMock()
        statusFilterPatch.filter.return_value = ['testGroupName']
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=statusFilterPatch)
    
    elif testname==GroupDoesNotExists_DoesNotNeedsApproval_1:
        def mockGenerateNewGroupCreationEmailBody(request, group_id, newGroupName, initialMembers, newGroupReason, needsAccessApprove):
            return ""
        statusFilterPatch = mocker.MagicMock()
        statusFilterPatch.filter.return_value = []
        mockUser = mocker.MagicMock()
        mockUser.user.username = "username"
        request.user.email = "user@user.com"
        request.user.user = mockUser
        mockGroup = mocker.MagicMock()
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=statusFilterPatch)
        mocker.patch("Access.models.GroupV2.objects.create", return_value=mockGroup)
        mocker.patch("Access.models.MembershipV2.objects.create", return_value=True)
        mocker.patch("Access.email_helper.generateEmail", return_value="email body")
        mocker.patch("bootprocess.general.emailSES", return_value="")
        group_helper.generateNewGroupCreationEmailBody  = mockGenerateNewGroupCreationEmailBody

    elif testname==GroupDoesNotExists_DoesNotNeedsApproval_2:
        def mockGenerateNewGroupCreationEmailBody(request, group_id, newGroupName, initialMembers, newGroupReason, needsAccessApprove):
            return ""
        statusFilterPatch = mocker.MagicMock()
        statusFilterPatch.filter.return_value = []
        mockAuthUser = mocker.MagicMock()
        mockAuthUser.user.username = "username"
        request.user.email = "user@user.com"
        request.user.user = mockAuthUser
        mockGroup = mocker.MagicMock()

        mockAccUser = mocker.MagicMock()
        mockAccUser.user.username = "UserName"

        mocker.patch("Access.models.GroupV2.objects.filter", return_value=statusFilterPatch)
        mocker.patch("Access.models.GroupV2.objects.create", return_value=mockGroup)
        mocker.patch("Access.models.MembershipV2.objects.create", return_value=None)
        mocker.patch("Access.models.User.objects.filter", return_value=[mockAccUser])
        mocker.patch("Access.email_helper.generateEmail", return_value="email body")
        mocker.patch("bootprocess.general.emailSES", return_value="")
        group_helper.generateNewGroupCreationEmailBody  = mockGenerateNewGroupCreationEmailBody

    elif testname==GroupDoesNotExists_NeedsApproval_3:
        def mockGenerateNewGroupCreationEmailBody(request, group_id, newGroupName, initialMembers, newGroupReason, needsAccessApprove):
            return ""
        statusFilterPatch = mocker.MagicMock()
        statusFilterPatch.filter.return_value = []
        mockAuthUser = mocker.MagicMock()
        mockAuthUser.user.username = "username"
        request.user.email = "user@user.com"
        request.user.user = mockAuthUser
        mockGroup = mocker.MagicMock()

        mockAccUser = mocker.MagicMock()
        mockAccUser.user.username = "UserName"

        mocker.patch("Access.models.GroupV2.objects.filter", return_value=statusFilterPatch)
        mocker.patch("Access.models.GroupV2.objects.create", return_value=mockGroup)
        mocker.patch("Access.models.MembershipV2.objects.create", return_value=None)
        mocker.patch("Access.models.User.objects.filter", return_value=[mockAccUser])
        mocker.patch("Access.email_helper.generateEmail", return_value="email body")
        mocker.patch("bootprocess.general.emailSES", return_value="")
        group_helper.generateNewGroupCreationEmailBody  = mockGenerateNewGroupCreationEmailBody

    context = group_helper.createGroup(request)
    assert str(context) == expectedContext
    if membershipCreationCallCount>0:
        assert models.MembershipV2.objects.create.call_count == membershipCreationCallCount
        models.GroupV2.objects.create.assert_called_with(name=ANY, group_id=ANY, requester=ANY, description=ANY, needsAccessApprove=needsAccessApprove)