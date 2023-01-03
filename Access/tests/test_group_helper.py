import pytest
from django.http import QueryDict
from Access import models, helpers
from Access import group_helper
from unittest.mock import ANY
from bootprocess import general

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
        mocker.patch("Access.helpers.generateStringFromTemplate", return_value="email body")
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
        mocker.patch("Access.helpers.generateStringFromTemplate", return_value="email body")
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
        mocker.patch("Access.helpers.generateStringFromTemplate", return_value="email body")
        mocker.patch("bootprocess.general.emailSES", return_value="")
        group_helper.generateNewGroupCreationEmailBody  = mockGenerateNewGroupCreationEmailBody

    context = group_helper.createGroup(request)
    assert str(context) == expectedContext
    if membershipCreationCallCount>0:
        assert models.MembershipV2.objects.create.call_count == membershipCreationCallCount
        models.GroupV2.objects.create.assert_called_with(name=ANY, group_id=ANY, requester=ANY, description=ANY, needsAccessApprove=needsAccessApprove)


test_getGroupAccessList_groupDoesNotExist= "groupDoesNotExist"
test_getGroupAccessList_groupExists_NoPermission= "groupDoesNotExist_UserDoesNotHavePermission"
test_getGroupAccessList_groupExists_HasPermission = "groupDoesNotExist_UserHasPermission"

@pytest.mark.parametrize("testname, expectedOutput",
    [
        (
            test_getGroupAccessList_groupDoesNotExist, 
            "{'error': {'title': 'Invalid Group', 'msg': 'There is no group named testgroupname. Please contact admin for any queries.'}}"
        ),
        (
            test_getGroupAccessList_groupExists_NoPermission, 
            "{'error': {'error_msg': 'Internal Error', 'msg': 'Error Occured while loading the page. Please contact admin, Permission denied, requester is non owner'}}"
        ),
        (
            test_getGroupAccessList_groupExists_HasPermission, 
            "{'userList': ['member1', 'member2'], 'groupName': 'testgroupname', 'allowRevoke': False}"
        ),
    ]
)
def test_getGroupAccessList(mocker, testname, expectedOutput):
    request = mocker.MagicMock()
    groupName = "testgroupname"

    if testname == test_getGroupAccessList_groupDoesNotExist:
        groupFilter = mocker.MagicMock()
        groupFilter.filter.return_value = []
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=groupFilter)

    elif testname == test_getGroupAccessList_groupExists_NoPermission:
        request.user.user.email = "loggedinuser@user.com"
        request.user.is_superuser = False
        request.user.user.is_ops = False
        groupFilter = mocker.MagicMock()
        groupFilter.filter.return_value = ["group1"]
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=groupFilter)

        member1 = mocker.MagicMock()
        member1.user.email = "user1@user.com"
        member2 = mocker.MagicMock()
        member2.user.email = "user2@user.com"


        groupMembersFilter2 = mocker.MagicMock()
        groupMembersFilter2.filter.return_value = [member1, member2]

        groupMembersFilter = mocker.MagicMock()
        groupMembersFilter.filter.return_value = groupMembersFilter2
        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=groupMembersFilter)
        mocker.patch("Access.models.Role.objects.get", return_value="")
        mocker.patch("Access.models.User.objects.filter", return_value=[])

    elif testname == test_getGroupAccessList_groupExists_HasPermission:
        request.POST = False
        request.user.user.email = "loggedinuser@user.com"
        request.user.is_superuser = False
        request.user.user.is_ops = True
        groupFilter = mocker.MagicMock()
        groupFilter.filter.return_value = ["group1"]
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=groupFilter)


        member1 = mocker.MagicMock()
        member1.user.email = "user1@user.com"
        member1.user.name = "user1"
        member1.is_owner = False
        member1.user.current_state.return_value = "is_active"
        member1.membership_id = "1"

        member2 = mocker.MagicMock()
        member2.user.email = "user2@user.com"
        member2.user.name = "user2"
        member2.is_owner = False
        member2.user.current_state.return_value = "is_active"
        member2.membership_id = "2"
        


        groupMembersFilter2 = mocker.MagicMock()
        groupMembersFilter2.filter.return_value = [member1, member2]

        groupMembersFilter = mocker.MagicMock()
        groupMembersFilter.filter.return_value = groupMembersFilter2

        def mock_getGroupMembers(groupMembers):
            return ["member1", "member2"]

        group_helper.getGroupMembers = mock_getGroupMembers

        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=groupMembersFilter)
        mocker.patch("Access.models.Role.objects.get", return_value="")
        mocker.patch("Access.models.User.objects.filter", return_value=[])

        mocker.patch("Access.models.GroupAccessMapping.objects.filter", return_value=[])

        mocker.patch("Access.helpers.check_user_permissions", return_value=False)
        def mock_getAccessDetails(eachAccess):
            return eachAccess
        helpers.getAccessDetails = mock_getAccessDetails
        
        def mock_check_user_is_group_owner(user_name, group):
            return []
        group_helper.check_user_is_group_owner = mock_check_user_is_group_owner

    context = group_helper.getGroupAccessList(request, groupName)
    assert str(context) == expectedOutput

def test_updateOwner(mocker):
    request = mocker.MagicMock()
    request.user.user.email = "loggedinuser@user.com"
    request.user.is_superuser = False
    request.user.user.is_ops = False
    request.POST = QueryDict("owners=user1@user.com&newGroupReason")

    mock_membershipObj = mocker.MagicMock()
    mock_membershipObj.user.email = "user1@user.com"
    mock_membershipObj.save.return_value = True

    mock_excludeMembership = mocker.MagicMock()
    mock_excludeMembership.exclude.return_value = [mock_membershipObj]

    mocker.patch("Access.models.Role.objects.get", return_value="")
    mocker.patch("Access.models.User.objects.filter", return_value=[])
    mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_excludeMembership)
    mocker.patch("bootprocess.general.emailSES", return_value=True)
    context = {}
    group_helper.updateOwner(request, "testgroupname","", context)
    assert context["notification"] == "Owner's updated"


test_approveNewGroupRequest_GroupNotFound="GroupNotFound"
test_approveNewGroupRequest_ReqNotInPending="ReuestNotInPendingState"
test_approveNewGroupRequest_UserApprovingHisOwn="UserApprovingHisOwnRequest"
test_approveNewGroupRequest_ProcessReq = "ProcessReq"
test_approveNewGroupRequest_ThrowsException = "ThrowsException"
@pytest.mark.parametrize("testname,expectedoutput, groupID, requestApproved, throwsException",
    [
        (
            test_approveNewGroupRequest_GroupNotFound,
            "{'error': 'Error request not found OR Invalid request type'}",
              "1", False, False,
        ),
        (
            test_approveNewGroupRequest_ReqNotInPending,
            "{'error': 'The Request (1) is already Processed By : username2'}",
            "1", False, False,
        ),
        (
            test_approveNewGroupRequest_UserApprovingHisOwn,
            "{'error': 'You cannot approve your own request. Please ask other admins to do that'}",
            "1", False, False,
        ),
        (
            test_approveNewGroupRequest_ProcessReq,
            "{'msg': 'The Request (grp1) is now being processed'}",
            "grp1", True, False,
        ),
        (
            test_approveNewGroupRequest_ThrowsException,
            "{'error': 'Error Occured while Approving group creation. Please contact admin - sendEmailError'}",
            "grp1", False, True,
        ),        
    ]
)

def test_approveNewGroupRequest(mocker, testname, expectedoutput,groupID, requestApproved, throwsException):
    request = mocker.MagicMock()

    if testname == test_approveNewGroupRequest_GroupNotFound:
        mocker.patch("Access.models.GroupV2.objects.get", return_value=[], side_effect = Exception("GroupNotFound"))

    elif testname == test_approveNewGroupRequest_ReqNotInPending:
        request.user.username = "username1"
        mock_groupObject = mocker.MagicMock()
        mock_groupObject.status="Declined"
        mock_groupObject.approver.user.username = "username2"
        mocker.patch("Access.models.GroupV2.objects.get", return_value=mock_groupObject)
        
    elif testname == test_approveNewGroupRequest_UserApprovingHisOwn:
        request.user.username = "username1"
        mock_groupObject = mocker.MagicMock()
        mock_groupObject.status="Pending"
        mock_groupObject.approver.user.username = "username2"
        mock_groupObject.requester.user.username = "username1"
        mocker.patch("Access.models.GroupV2.objects.get", return_value=mock_groupObject)

    elif testname == test_approveNewGroupRequest_ProcessReq:
        request.user.username = "username1"
        request.user.user = mocker.MagicMock()
        mock_groupObject = mocker.MagicMock()
        mock_groupObject.status="Pending"
        mock_groupObject.approver.user.username = "username2"
        mock_groupObject.requester.user.username = "username3"
        mock_groupObject.save.return_value = True
        mock_groupObject.requester.email = "requester@email.com"
        
        mock_membership_update = mocker.MagicMock()
        mock_membership_update.update.return_value = True
        mock_membership_update.values_list.return_value = ["member1"]
        mocker.patch("Access.models.GroupV2.objects.get", return_value=mock_groupObject)
        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_membership_update)
        mocker.patch("Access.helpers.generateStringFromTemplate", return_value="email body")
        mocker.patch("bootprocess.general.emailSES", return_value=True)

    elif testname == test_approveNewGroupRequest_ThrowsException:
        request.user.username = "username1"
        request.user.user = mocker.MagicMock()
        mock_groupObject = mocker.MagicMock()
        mock_groupObject.status="Pending"
        mock_groupObject.approver.user.username = "username2"
        mock_groupObject.requester.user.username = "username3"
        mock_groupObject.save.return_value = True
        mock_groupObject.requester.email = "requester@email.com"
        
        mock_membership_update = mocker.MagicMock()
        mock_membership_update.update.return_value = True
        mock_membership_update.values_list.return_value = ["member1"]
        mocker.patch("Access.models.GroupV2.objects.get", return_value=mock_groupObject)
        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_membership_update)
        mocker.patch("Access.helpers.generateStringFromTemplate", return_value="email body")
        mocker.patch("bootprocess.general.emailSES", return_value=True, side_effect=Exception("sendEmailError"))
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=[])

    response = group_helper.approveNewGroupRequest(request, groupID)

    assert str(response) == expectedoutput
    assert models.GroupV2.objects.get.call_count == 1

    if requestApproved:
        assert general.emailSES.call_count == 1
        assert models.MembershipV2.objects.filter.call_count == 2
        assert helpers.generateStringFromTemplate.call_count == 2
    if throwsException:
        assert models.GroupV2.objects.filter.call_count == 1
        assert models.MembershipV2.objects.filter.call_count == 2
        assert general.emailSES.call_count == 1
        assert helpers.generateStringFromTemplate.call_count == 2
        

test_get_user_group_group_not_found = "GroupNotFound"
test_get_user_group_cannot_access_group = "UserIsNotOwnerOfGroupOrSuperUser"
test_get_user_group_can_access_group = "UserCanAccessGroup"
@pytest.mark.parametrize("test_name, group_name,expected_output",
    [
        (
            test_get_user_group_group_not_found,
            "TestGroupName1",
            "{'status': {'title': 'Invalid Group', 'msg': 'There is no group named TestGroupName1. Please contact admin for any queries.'}}",
        ),
        (
            test_get_user_group_cannot_access_group,
            "TestGroupName1",
            "{'error': {'error_msg': 'Internal Error', 'msg': \"Error Occured while loading the page. Please contact admin, Permission denied, you're not owner of this group\"}}",
        ),
        (
            test_get_user_group_can_access_group,
            "TestGroupName1",
            "{'groupMembers': 'user1', 'groupName': 'TestGroupName1'}",
        ),        
    ]
)
def test_get_user_group(mocker, test_name, group_name, expected_output):
    request = mocker.MagicMock()
    if test_name == test_get_user_group_group_not_found:
        mock_filtered_group = mocker.MagicMock()
        mock_filtered_group.filter.return_value = []
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=mock_filtered_group)
    elif test_name == test_get_user_group_cannot_access_group:
        request.user.user.email = "member0@email.com"
        request.user.is_superuser = False

        mock_group = mocker.MagicMock()
        mock_filtered_group = mocker.MagicMock()
        mock_filtered_group.filter.return_value = [mock_group]
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=mock_filtered_group)

        mock_membership_only_filter = mocker.MagicMock()
        mock_membership_filter1 = mocker.MagicMock()
        mock_group_member = mocker.MagicMock()
        mock_group_member.filter.return_value = ["member1@email.com"]
        
        mock_membership_filter1.filter.return_value = mock_membership_only_filter

        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_membership_filter1)
    
    elif test_name == test_get_user_group_can_access_group:
        request.user.user.email = "member1@email.com"
        request.user.is_superuser = True

        mock_group = mocker.MagicMock()
        mock_filtered_group = mocker.MagicMock()
        mock_filtered_group.filter.return_value = [mock_group]
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=mock_filtered_group)

        mock_membership_filter1 = mocker.MagicMock()
        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_membership_filter1)

        mock_membership_only_filter = mocker.MagicMock()
        
        def mock_get_users_from_groupmembers(groupMembers):
            return "user1"

        group_helper.get_users_from_groupmembers = mock_get_users_from_groupmembers
        mock_member = mocker.MagicMock()
        mock_member.user.email = "member1@email.com"

        mock_group_member = mocker.MagicMock()
        mock_group_member.filter.return_value = [mock_member]
        mock_membership_only_filter.only.return_value = mock_group_member        
        mock_membership_filter1.filter.return_value = mock_membership_only_filter

        
    context = group_helper.get_user_group(request, group_name)
    assert str(context) == expected_output


test_add_user_to_group_permission_denied= "PermissionDenied"
test_add_user_to_group_duplicate_request= "DuplicateRequest"
test_add_user_to_group_needs_approval= "NeedsApproval"
test_add_user_to_group_doesnot_need_approval= "DoesNotNeedApproval"

@pytest.mark.parametrize("test_name, post_data ,expected_output",
[
        (
            test_add_user_to_group_permission_denied,
            "groupName=TestGroupName",
            "{'error': {'error_msg': 'Internal Error', 'msg': 'Error Occured while loading the page. Please contact admin, Permission denied, requester is non owner'}}",
        ),
        (
            test_add_user_to_group_duplicate_request,
            "groupName=TestGroupName&selectedUserList=member2@member2.com",
            "{'error': {'error_msg': 'Duplicate Request', 'msg': 'User member2@member2.com is already added to group/or pending approval for group addition'}}",
        ),
       (
            test_add_user_to_group_needs_approval,
            "groupName=TestGroupName&selectedUserList=member2@member2.com&memberReason=somereason",
            "{'status': {'title': 'Request Submitted', 'msg': 'Once Approved the newly added members will be granted the same permissions as the group'}}",
        ),
       (
            test_add_user_to_group_doesnot_need_approval,
            "groupName=TestGroupName&selectedUserList=member2@member2.com&memberReason=somereason",
            "is now being processed', 'desc': 'A email will be sent after the requested access are granted'}}",
        ),    
]
)
def test_add_user_to_group(mocker, test_name, post_data, expected_output):
    request = mocker.MagicMock()

    request.user.email = "member1@member1.com"
    request.user.is_superuser = False

    if test_name == test_add_user_to_group_permission_denied:
        request.POST = QueryDict(post_data)
        request.user.email = "member1@member1.com"
        request.user.is_superuser = False

        mock_member = mocker.MagicMock()
        mock_member.user.email = "member2@member2.com"


        mock_group_filter = mocker.MagicMock()
        mock_group_filter.filter.return_value = ["group1"]

        mock_member_filter1 = mocker.MagicMock()
        mock_member_filter1.filter.return_value = [mock_member]

        mock_member_filter = mocker.MagicMock()
        mock_member_filter.filter.return_value = mock_member_filter
        mock_member_filter.only.return_value = mock_member_filter1

        mocker.patch("Access.models.GroupV2.objects.filter", return_value=mock_group_filter)
        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_member_filter)

    elif test_name == test_add_user_to_group_duplicate_request:
        request.POST = QueryDict(post_data)
        request.user.email = "member1@member1.com"
        request.user.is_superuser = True

        mock_member = mocker.MagicMock()
        mock_member.user.email = "member2@member2.com"

        mock_group_filter = mocker.MagicMock()
        mock_group_filter.filter.return_value = ["group1"]

        mock_member_filter1 = mocker.MagicMock()
        mock_member_filter1.filter.return_value = [mock_member]

        mock_member_filter = mocker.MagicMock()
        mock_member_filter.filter.return_value = mock_member_filter
        mock_member_filter.only.return_value = mock_member_filter1

        mocker.patch("Access.group_helper.is_user_in_group", return_value = True)

        mocker.patch("Access.models.GroupV2.objects.filter", return_value=mock_group_filter)
        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_member_filter)

    elif test_name == test_add_user_to_group_needs_approval:
        request.POST = QueryDict(post_data)
        request.user.email = "member1@member1.com"
        request.user.is_superuser = True
        

        mock_member = mocker.MagicMock()
        mock_member.user.email = "member2@member2.com"

        mock_group = mocker.MagicMock()
        mock_group.needsAccessApprove = True

        mock_group_filter = mocker.MagicMock()
        mock_group_filter.filter.return_value = [mock_group]

        mock_member_filter1 = mocker.MagicMock()
        mock_member_filter1.filter.return_value = [mock_member]

        mock_member_filter = mocker.MagicMock()
        mock_member_filter.filter.return_value = mock_member_filter
        mock_member_filter.only.return_value = mock_member_filter1

        mock_user = mocker.MagicMock()
        mock_user.user.name = "username"

        mocker.patch("Access.group_helper.is_user_in_group", return_value = False)

        mocker.patch("Access.models.GroupV2.objects.filter", return_value=mock_group_filter)
        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_member_filter)
        mocker.patch("Access.models.User.objects.filter", return_value=mock_user)
        mocker.patch("Access.models.MembershipV2.objects.create", return_value=mocker.MagicMock())
        mocker.patch("Access.group_helper.sendMailForGroupApproval", return_value=True)

    elif test_name == test_add_user_to_group_doesnot_need_approval:
        request.POST = QueryDict(post_data)
        request.user.email = "member1@member1.com"
        request.user.is_superuser = True
        request.user.user = mocker.MagicMock()

        mock_member = mocker.MagicMock()
        mock_member.user.email = "member2@member2.com"

        mock_group = mocker.MagicMock()
        mock_group.needsAccessApprove = False
        mock_group.__str__.return_value = "grp1"

        mock_group_filter = mocker.MagicMock()
        mock_group_filter.filter.return_value = [mock_group]

        mock_member_filter1 = mocker.MagicMock()
        mock_member_filter1.filter.return_value = [mock_member]

        mock_member_filter = mocker.MagicMock()
        mock_member_filter.filter.return_value = mock_member_filter
        mock_member_filter.only.return_value = mock_member_filter1

        mock_user = mocker.MagicMock()
        mock_user.name = "username"

        mock_member = mocker.MagicMock()
        mock_member.save.return_value = True

        mocker.patch("Access.group_helper.is_user_in_group", return_value = False)

        mocker.patch("Access.models.GroupV2.objects.filter", return_value=mock_group_filter)
        mocker.patch("Access.models.MembershipV2.objects.filter", return_value=mock_member_filter)
        mocker.patch("Access.models.User.objects.filter", return_value=[mock_user])
        mocker.patch("Access.models.MembershipV2.objects.create", return_value=mock_member)
        mocker.patch("Access.group_helper.sendMailForGroupApproval", return_value=True)
        mocker.patch("Access.views_helper.generateUserMappings", return_value=mocker.MagicMock())

        mock_thread = mocker.MagicMock()
        mock_thread.start.return_value = True

        mocker.patch("threading.Thread", return_value = mock_thread)
    

    context = group_helper.add_user_to_group(request)
    assert expected_output in str(context)
