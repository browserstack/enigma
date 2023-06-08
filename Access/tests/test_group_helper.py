import pytest
from django.http import QueryDict
from Access import models, helpers
from Access import group_helper
from bootprocess import general

testGroupName = "testgroupname"
# TESTCASE NAMES
GroupAlreadyExists = "GroupExists"
GroupDoesNotExists_DoesNotNeedsApproval_1 = "GroupDoesNotExists Does not Need Approval"
GroupDoesNotExists_DoesNotNeedsApproval_2 = (
    "GroupDoesNotExists Does not Need Approval with SelectedUserList"
)
GroupDoesNotExists_NeedsApproval_3 = (
    "GroupDoesNotExists NeedsApproval with SelectedUserList"
)


test_approve_new_group_request_GroupNotFound = "GroupNotFound"
test_approve_new_group_request_ReqNotInPending = "ReuestNotInPendingState"
test_approve_new_group_request_UserApprovingHisOwn = "UserApprovingHisOwnRequest"
test_approve_new_group_request_ProcessReq = "ProcessReq"
test_approve_new_group_request_ThrowsException = "ThrowsException"


@pytest.mark.parametrize(
    "testname,expectedoutput, groupID, requestApproved, throwsException",
    [
        (
            test_approve_new_group_request_GroupNotFound,
            "{'error': 'Error Occured while loading the page. Please contact admin'}",
            "1",
            False,
            False,
        ),
        (
            test_approve_new_group_request_UserApprovingHisOwn,
            (
                "{'error': 'You cannot approve your own request. Please ask other"
                " admins to do that'}"
            ),
            "1",
            False,
            False,
        ),
        (
            test_approve_new_group_request_ProcessReq,
            "{'error': 'You cannot approve your own request. Please ask other admins to do that'}",
            "grp1",
            True,
            False,
        ),
        (
            test_approve_new_group_request_ThrowsException,
            "{'error': 'You cannot approve your own request. Please ask other admins to do that'}",
            "grp1",
            False,
            True,
        ),
    ],
)
def test_approve_new_group_request(
    mocker, testname, expectedoutput, groupID, requestApproved, throwsException
):
    request = mocker.MagicMock()

    if testname == test_approve_new_group_request_GroupNotFound:
        mocker.patch(
            "Access.models.GroupV2.objects.get",
            return_value=[],
            side_effect=Exception("GroupNotFound"),
        )

    elif testname == test_approve_new_group_request_ReqNotInPending:
        request.user.username = "username1"
        mock_groupObject = mocker.MagicMock()
        mock_groupObject.status = "Declined"
        mock_groupObject.approver.user.username = "username2"
        mocker.patch("Access.models.GroupV2.objects.get", return_value=mock_groupObject)

    elif testname == test_approve_new_group_request_UserApprovingHisOwn:
        request.user.username = "username1"
        mock_groupObject = mocker.MagicMock()
        mock_groupObject.status = "Pending"
        mock_groupObject.approver.user.username = "username2"
        mock_groupObject.requester.user.username = "username1"
        mocker.patch("Access.models.GroupV2.objects.get", return_value=mock_groupObject)

    elif testname == test_approve_new_group_request_ProcessReq:
        request.user.username = "username1"
        request.user.user = mocker.MagicMock()
        mock_groupObject = mocker.MagicMock()
        mock_groupObject.status = "Pending"
        mock_groupObject.approver.user.username = "username2"
        mock_groupObject.requester.user.username = "username3"
        mock_groupObject.save.return_value = True
        mock_groupObject.requester.email = "requester@email.com"

        mock_membership_update = mocker.MagicMock()
        mock_membership_update.update.return_value = True
        mock_membership_update.values_list.return_value = ["member1"]
        mocker.patch("Access.models.GroupV2.objects.get", return_value=mock_groupObject)
        mocker.patch(
            "Access.models.MembershipV2.objects.filter",
            return_value=mock_membership_update,
        )
        mocker.patch(
            "Access.helpers.generate_string_from_template", return_value="email body"
        )
        mocker.patch("bootprocess.general.email_via_smtp", return_value=True)

    elif testname == test_approve_new_group_request_ThrowsException:
        request.user.username = "username1"
        request.user.user = mocker.MagicMock()
        mock_groupObject = mocker.MagicMock()
        mock_groupObject.status = "Pending"
        mock_groupObject.approver.user.username = "username2"
        mock_groupObject.requester.user.username = "username3"
        mock_groupObject.save.return_value = True
        mock_groupObject.requester.email = "requester@email.com"

        mock_membership_update = mocker.MagicMock()
        mock_membership_update.update.return_value = True
        mock_membership_update.values_list.return_value = ["member1"]
        mocker.patch("Access.models.GroupV2.objects.get", return_value=mock_groupObject)
        mocker.patch(
            "Access.models.MembershipV2.objects.filter",
            return_value=mock_membership_update,
        )
        mocker.patch(
            "Access.helpers.generate_string_from_template", return_value="email body"
        )
        mocker.patch(
            "bootprocess.general.email_via_smtp",
            return_value=True,
            side_effect=Exception("sendEmailError"),
        )
        mocker.patch("Access.models.GroupV2.objects.filter", return_value=[])

    response = group_helper.approve_new_group_request(request, groupID)

    assert str(response) == expectedoutput
    assert models.GroupV2.objects.get.call_count == 1

    if testname != test_approve_new_group_request_ProcessReq and requestApproved:
        assert general.email_via_smtp.call_count == 1
        assert models.MembershipV2.objects.filter.call_count == 2
        assert helpers.generate_string_from_template.call_count == 2


test_get_user_group_group_not_found = "GroupNotFound"
test_get_user_group_cannot_access_group = "UserIsNotOwnerOfGroupOrSuperUser"
test_get_user_group_can_access_group = "UserCanAccessGroup"


@pytest.mark.parametrize(
    "test_name, group_name,expected_output",
    [
        (
            test_get_user_group_group_not_found,
            "TestGroupName1",
            "{'group_existing_member_emails': set(), 'groupMembers': [], 'groupName': 'TestGroupName1'}",
        ),
        (
            test_get_user_group_cannot_access_group,
            "TestGroupName1",
            "{'group_existing_member_emails': set(), 'groupMembers': [], 'groupName': 'TestGroupName1'}",
        ),
        (
            test_get_user_group_can_access_group,
            "TestGroupName1",
            "{'group_existing_member_emails': set(), 'groupMembers': 'user1', 'groupName': 'TestGroupName1'}",
        ),
    ],
)
def test_get_user_group(mocker, test_name, group_name, expected_output):
    request = mocker.MagicMock()
    if test_name == test_get_user_group_group_not_found:
        mock_filtered_group = mocker.MagicMock()
        mock_filtered_group.filter.return_value = []
        mocker.patch(
            "Access.models.GroupV2.objects.filter", return_value=mock_filtered_group
        )
    elif test_name == test_get_user_group_cannot_access_group:
        request.user.user.email = "member0@email.com"
        request.user.is_superuser = False
        mocker.patch(
            "Access.models.User.is_allowed_admin_actions_on_group", return_value=False
        )

        mock_group = mocker.MagicMock()
        mock_filtered_group = mocker.MagicMock()
        mock_filtered_group.filter.return_value = [mock_group]
        mocker.patch(
            "Access.models.GroupV2.objects.filter", return_value=mock_filtered_group
        )

        mock_membership_only_filter = mocker.MagicMock()
        mock_membership_filter1 = mocker.MagicMock()
        mock_group_member = mocker.MagicMock()
        mock_group_member.filter.return_value = ["member1@email.com"]

        mock_membership_filter1.filter.return_value = mock_membership_only_filter

        mocker.patch(
            "Access.models.MembershipV2.objects.filter",
            return_value=mock_membership_filter1,
        )

    elif test_name == test_get_user_group_can_access_group:
        request.user.user.email = "member1@email.com"
        request.user.is_superuser = True
        mocker.patch(
            "Access.models.User.is_allowed_admin_actions_on_group", return_value=True
        )

        mock_group = mocker.MagicMock()
        mock_filtered_group = mocker.MagicMock()
        mock_filtered_group.filter.return_value = [mock_group]
        mocker.patch(
            "Access.models.GroupV2.objects.filter", return_value=mock_filtered_group
        )

        mock_membership_filter1 = mocker.MagicMock()
        mocker.patch(
            "Access.models.MembershipV2.objects.filter",
            return_value=mock_membership_filter1,
        )

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


test_add_user_to_group_permission_denied = "PermissionDenied"
test_add_user_to_group_duplicate_request = "DuplicateRequest"
test_add_user_to_group_needs_approval = "NeedsApproval"
test_add_user_to_group_doesnot_need_approval = "DoesNotNeedApproval"


# TODO: fix this test case and enable it back
@pytest.mark.skip
@pytest.mark.parametrize(
    "test_name, post_data ,expected_output",
    [
        (
            test_add_user_to_group_permission_denied,
            "groupName=TestGroupName",
            "{'error': {'error_msg': 'Internal Error',"
            + " 'msg': 'Error Occured while loading the page."
            + " Please contact admin, Permission denied, requester is non owner'}}",
        ),
        (
            test_add_user_to_group_duplicate_request,
            "groupName=TestGroupName&selectedUserList=member2@member2.com",
            "{'error': {'error_msg': 'Duplicate Request',"
            + " 'msg': 'User member2@member2.com is already added to group/or"
            + " pending approval for group addition'}}",
        ),
        (
            test_add_user_to_group_needs_approval,
            "groupName=TestGroupName&selectedUserList=member2@member2.com&memberReason=somereason",
            "{'status': {'title': 'Request Submitted',"
            + " 'msg': 'Once Approved the newly added members will be granted"
            + " the same permissions as the group'}}",
        ),
        (
            test_add_user_to_group_doesnot_need_approval,
            "groupName=TestGroupName&selectedUserList=member2@member2.com&memberReason=somereason",
            "is now being processed',"
            + " 'desc': 'A email will be sent after the requested access are"
            " granted'}}",
        ),
    ],
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

        mocker.patch(
            "Access.models.GroupV2.objects.filter", return_value=mock_group_filter
        )
        mocker.patch(
            "Access.models.MembershipV2.objects.filter", return_value=mock_member_filter
        )
        mocker.patch(
            "Access.models.User.is_allowed_admin_actions_on_group", return_value=False
        )

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

        mocker.patch("Access.group_helper.is_user_in_group", return_value=True)

        mocker.patch(
            "Access.models.GroupV2.objects.filter", return_value=mock_group_filter
        )
        mocker.patch(
            "Access.models.MembershipV2.objects.filter", return_value=mock_member_filter
        )
        mocker.patch(
            "Access.models.User.is_allowed_admin_actions_on_group", return_value=True
        )

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

        mocker.patch("Access.group_helper.is_user_in_group", return_value=False)

        mocker.patch(
            "Access.models.GroupV2.objects.filter", return_value=mock_group_filter
        )
        mocker.patch(
            "Access.models.MembershipV2.objects.filter", return_value=mock_member_filter
        )
        mocker.patch("Access.models.User.objects.filter", return_value=mock_user)
        mocker.patch(
            "Access.models.MembershipV2.objects.create", return_value=mocker.MagicMock()
        )
        mocker.patch(
            "Access.models.User.is_allowed_admin_actions_on_group", return_value=True
        )
        mocker.patch("Access.group_helper.sendMailForGroupApproval", return_value=True)

    # skip the test for now as it is not working
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

        mocker.patch("Access.group_helper.is_user_in_group", return_value=False)

        mocker.patch(
            "Access.models.GroupV2.objects.filter", return_value=mock_group_filter
        )
        mocker.patch(
            "Access.models.MembershipV2.objects.filter", return_value=mock_member_filter
        )
        mocker.patch("Access.models.User.objects.filter", return_value=[mock_user])
        mocker.patch(
            "Access.models.MembershipV2.objects.create", return_value=mock_member
        )
        mocker.patch("Access.group_helper.sendMailForGroupApproval", return_value=True)
        mocker.patch(
            "Access.models.User.is_allowed_admin_actions_on_group", return_value=True
        )
        mocker.patch(
            "Access.views_helper.generate_user_mappings", return_value=mocker.MagicMock()
        )

        mock_thread = mocker.MagicMock()
        mock_thread.start.return_value = True

        mocker.patch("threading.Thread", return_value=mock_thread)

    context = group_helper.add_user_to_group(request)
    assert expected_output in str(context)
