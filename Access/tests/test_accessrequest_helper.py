import pytest
from Access import accessrequest_helper
from django.http import HttpRequest, QueryDict
import json

@pytest.mark.parametrize("contextoutput, getAvailableAccessModulesThrowsException, get_extra_fields_throwsException, get_noticeThrowsException",[
        # no exceptions are thrown
        ({'accesses': [{'formDesc': 'desc value', 'accessTag': 'AccModule1', 'accessTypes': 'access types', 'accessRequestData': 'request data', 'extraFields': ['fields1'], 'notice': 'somenotice', 'accessRequestPath': '/path'}], 'genericForm': True}, False, False, False),
        # get access_modules method raises an Exception
        ({'status': {'title': 'Error Occured', 'msg': 'There was an error in getting the requested access resources. Please contact Admin'}}, True, False, False),
        # get_extra_fields method raises an Exception
        ({'accesses': [{'formDesc': 'desc value', 'accessTag': 'AccModule1', 'accessTypes': 'access types', 'accessRequestData': 'request data', 'extraFields': [], 'notice': 'somenotice', 'accessRequestPath': '/path'}], 'genericForm': True}, False, True, False),
        # get_notice method raises an Exception
        ({'accesses': [{'formDesc': 'desc value', 'accessTag': 'AccModule1', 'accessTypes': 'access types', 'accessRequestData': 'request data', 'extraFields': ['fields1'], 'notice': '', 'accessRequestPath': '/path'}], 'genericForm': True}, False, False, True),
    ])

def test_requestAccessGet(mocker, contextoutput, getAvailableAccessModulesThrowsException, get_extra_fields_throwsException, get_noticeThrowsException):
    accessModule = mocker.MagicMock()
    accessModule.access_desc.return_value = "desc value"
    accessModule.access_types.return_value = "access types"
    accessModule.access_request_data.return_value = "request data"
    accessModule.tag.return_value = "AccModule1"
    
    if not get_extra_fields_throwsException:
        accessModule.get_extra_fields.return_value = ["fields1"]
    else:
        accessModule.get_extra_fields.side_effect = Exception('getAvailableAccessModules error')

    if not get_noticeThrowsException:
        accessModule.get_notice.return_value = "somenotice"
    else:
        accessModule.get_notice.return_value = ""

    accessModule.fetch_access_request_form_path.return_value = "/path"
    
    if not getAvailableAccessModulesThrowsException:
        mocker.patch("Access.helpers.getAvailableAccessModules", return_value=[accessModule])
    else:
        mocker.patch("Access.helpers.getAvailableAccessModules", return_value=[accessModule], side_effect=Exception('getAvailableAccessModules error'))

    # monkeypatch.setattr(helpers, "getAvailableAccessModules", mock_getAvailableAccessModules)

    request = HttpRequest()
    request.method = 'GET'
    request.GET = QueryDict('accesses=access_AccModule1')
    context = accessrequest_helper.requestAccessGet(request)
    if not getAvailableAccessModulesThrowsException:
        assert str(context['accesses'][0]) == str(contextoutput["accesses"][0])
    else:
        assert context['status'] == context['status']

def test_pendingFailure(mocker):
    request = mocker.MagicMock()
