import pytest
from Access import accessrequest_helper
from django.http import HttpRequest, QueryDict


@pytest.mark.parametrize(
    (
        "contextoutput, getAvailableAccessModulesThrowsException,"
        " get_extra_fields_throwsException, get_noticeThrowsException"
    ),
    [
        # no exceptions are thrown
        (
            {
                "accesses": [
                    {
                        "formDesc": "desc value",
                        "accessTag": "AccModule1",
                        "accessTypes": "access types",
                        "accessRequestData": "request data",
                        "extraFields": ["fields1"],
                        "notice": "somenotice",
                        "accessRequestPath": "/path",
                    }
                ],
                "genericForm": True,
            },
            False,
            False,
            False,
        ),
        # get access_modules method raises an Exception
        (
            {
                "status": {
                    "title": "Error Occured",
                    "msg": (
                        "There was an error in getting the requested access resources."
                        " Please contact Admin"
                    ),
                }
            },
            True,
            False,
            False,
        ),
        # get_extra_fields method raises an Exception
        (
            {
                "accesses": [
                    {
                        "formDesc": "desc value",
                        "accessTag": "AccModule1",
                        "accessTypes": "access types",
                        "accessRequestData": "request data",
                        "extraFields": [],
                        "notice": "somenotice",
                        "accessRequestPath": "/path",
                    }
                ],
                "genericForm": True,
            },
            False,
            True,
            False,
        ),
        # get_notice method raises an Exception
        (
            {
                "accesses": [
                    {
                        "formDesc": "desc value",
                        "accessTag": "AccModule1",
                        "accessTypes": "access types",
                        "accessRequestData": "request data",
                        "extraFields": ["fields1"],
                        "notice": "",
                        "accessRequestPath": "/path",
                    }
                ],
                "genericForm": True,
            },
            False,
            False,
            True,
        ),
    ],
)
def test_requestAccessGet(
    mocker,
    contextoutput,
    getAvailableAccessModulesThrowsException,
    get_extra_fields_throwsException,
    get_noticeThrowsException,
):
    accessModule = mocker.MagicMock()
    accessModule.access_desc.return_value = "desc value"
    accessModule.access_types.return_value = "access types"
    accessModule.access_request_data.return_value = "request data"
    accessModule.tag.return_value = "AccModule1"

    if not get_extra_fields_throwsException:
        accessModule.get_extra_fields.return_value = ["fields1"]
    else:
        accessModule.get_extra_fields.side_effect = Exception(
            "getAvailableAccessModules error"
        )

    if not get_noticeThrowsException:
        accessModule.get_notice.return_value = "somenotice"
    else:
        accessModule.get_notice.return_value = ""

    accessModule.fetch_access_request_form_path.return_value = "/path"

    if not getAvailableAccessModulesThrowsException:
        mocker.patch(
            "Access.helpers.getAvailableAccessModules", return_value=[accessModule]
        )
    else:
        mocker.patch(
            "Access.helpers.getAvailableAccessModules",
            return_value=[accessModule],
            side_effect=Exception("getAvailableAccessModules error"),
        )

    # monkeypatch.setattr(helpers, "getAvailableAccessModules", mock_getAvailableAccessModules)

    request = HttpRequest()
    request.method = "GET"
    request.GET = QueryDict("accesses=access_AccModule1")
    context = accessrequest_helper.requestAccessGet(request)
    if not getAvailableAccessModulesThrowsException:
        assert str(context["accesses"][0]) == str(contextoutput["accesses"][0])
    else:
        assert context["status"] == context["status"]


Test_pendingFailure_NoFailures = "NoFailures"
Test_pendingFailure_UserBasedFailures = "UserBasedFailures"
Test_pendingFailure_AccessTypeBasedFailures = "AccessTypeBasedFailures"
Test_pendingFailure_Exception = "Throws Exception"


@pytest.mark.parametrize(
    "testname, expectedOutput, failures, getUserExceptionString",
    [
        # no exceptions are thrown
        (
            Test_pendingFailure_NoFailures,
            "{'failures': ['Failure1'], 'heading': 'Grant Failures'}",
            ["Failure1"],
            "",
        ),
        (
            Test_pendingFailure_UserBasedFailures,
            "{'failures': ['Failure2'], 'heading': 'Grant Failures'}",
            ["Failure2"],
            "",
        ),
        (
            Test_pendingFailure_AccessTypeBasedFailures,
            "{'failures': ['Failure3'], 'heading': 'Grant Failures'}",
            ["Failure3"],
            "",
        ),
    ],
)
def test_pendingFailure(
    mocker, testname, expectedOutput, failures, getUserExceptionString
):
    request = mocker.MagicMock()
    if testname == Test_pendingFailure_NoFailures:
        request.GET.get.return_value = False
        orderByPatch = mocker.MagicMock()
        orderByPatch.order_by.return_value = failures
        mocker.patch(
            "Access.models.UserAccessMapping.objects.filter", return_value=orderByPatch
        )

    elif testname == Test_pendingFailure_UserBasedFailures:

        def requestGet(val):
            if val == "username":
                return True
            return False

        request.GET.get = requestGet

        mockFailuresOrderBy = mocker.MagicMock()
        mockFailuresOrderBy.order_by.return_value = failures

        mockFailures = mocker.MagicMock()
        mockFailures.filter.return_value = mockFailuresOrderBy

        accessmappingfailure_orderBy = mocker.MagicMock()
        accessmappingfailure_orderBy.order_by.return_value = mockFailures

        mocker.patch(
            "Access.models.UserAccessMapping.objects.filter",
            return_value=accessmappingfailure_orderBy,
        )
        mocker.patch("Access.models.User.objects.get", return_value=mocker.MagicMock())

    elif testname == Test_pendingFailure_AccessTypeBasedFailures:

        def requestGet(val):
            if val == "access_type":
                return True
            return False

        request.GET.get = requestGet

        mockFailuresOrderBy = mocker.MagicMock()
        mockFailuresOrderBy.order_by.return_value = failures

        mockFailures = mocker.MagicMock()
        mockFailures.filter.return_value = mockFailuresOrderBy

        accessmappingfailure_orderBy = mocker.MagicMock()
        accessmappingfailure_orderBy.order_by.return_value = mockFailures

        mocker.patch(
            "Access.models.UserAccessMapping.objects.filter",
            return_value=accessmappingfailure_orderBy,
        )
        mocker.patch("Access.models.User.objects.get", return_value=mocker.MagicMock())
    elif testname == Test_pendingFailure_Exception:
        mocker.patch(
            "Access.models.UserAccessMapping.objects.filter",
            return_value=None,
            side_effect=Exception(getUserExceptionString),
        )

    context = accessrequest_helper.getGrantFailedRequests(request)
    assert str(context) == expectedOutput


test_PendingRevokeRequests_UserBasedFailures = "UserBasedFailured"
test_PendingRevokeRequests_AccessTypeBasedFailures = "AccessTypeBasedFailures"
test_PendingRevokeRequests_OtherFailures = "OtherFailures"
test_pendingRevoke_Exception = "Exception"


@pytest.mark.parametrize(
    "testname, expectedOutPut, failures, getUserExceptionString",
    [
        # no exceptions are thrown
        (
            test_PendingRevokeRequests_UserBasedFailures,
            "{'failures': ['failure1'], 'heading': 'Revoke Failures'}",
            ["failure1"],
            "",
        ),
        (
            test_PendingRevokeRequests_AccessTypeBasedFailures,
            "{'failures': ['failure2'], 'heading': 'Revoke Failures'}",
            ["failure2"],
            "",
        ),
        (
            test_PendingRevokeRequests_OtherFailures,
            "{'failures': ['failure3'], 'heading': 'Revoke Failures'}",
            ["failure3"],
            "",
        ),
    ],
)
def test_PendingRevokeRequests(
    mocker, testname, expectedOutPut, failures, getUserExceptionString
):

    request = mocker.MagicMock()
    if testname == test_PendingRevokeRequests_UserBasedFailures:

        def requestGet(val):
            if val == "username":
                return True
            return False

        request.GET.get = requestGet

        orderByPatch = mocker.MagicMock()
        orderByPatch.order_by.return_value = failures
        mocker.patch("Access.models.User.objects.get", return_value=mocker.MagicMock())
        mocker.patch(
            "Access.models.UserAccessMapping.objects.filter", return_value=orderByPatch
        )

    elif testname == test_PendingRevokeRequests_AccessTypeBasedFailures:

        def requestGet(val):
            if val == "access_type":
                return "request_type"
            return False

        request.GET.get = requestGet

        orderByPatch = mocker.MagicMock()
        orderByPatch.order_by.return_value = failures
        mocker.patch("Access.models.User.objects.get", return_value=mocker.MagicMock())
        mocker.patch(
            "Access.models.UserAccessMapping.objects.filter", return_value=orderByPatch
        )

    elif testname == test_PendingRevokeRequests_OtherFailures:

        def requestGet(val):
            if val == "access_type" or val == "username":
                return False
            return True

        request.GET.get = requestGet

        orderByPatch = mocker.MagicMock()
        orderByPatch.order_by.return_value = failures
        mocker.patch(
            "Access.models.UserAccessMapping.objects.filter", return_value=orderByPatch
        )

    elif testname == test_pendingRevoke_Exception:
        request.GET.get.return_value = True
        mocker.patch(
            "Access.models.User.objects.get",
            return_value=None,
            side_effect=Exception(getUserExceptionString),
        )

    context = accessrequest_helper.get_pending_revoke_failures(request)
    assert str(context) == expectedOutPut
