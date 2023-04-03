from unittest.mock import Mock


class MockAccessModule:
    def __init__(
        self,
        name="",
        primaryApproverPermissionLabel="",
        secondaryApproverPermissionLabel="",
    ):
        self.name = name
        self.available = True
        permissions = {}
        if primaryApproverPermissionLabel != "":
            permissions = {
                "1": primaryApproverPermissionLabel,
            }
            if secondaryApproverPermissionLabel != "":
                permissions["2"] = secondaryApproverPermissionLabel
        self.fetch_approver_permissions = Mock(return_value=permissions)

    def tag(self):
        return self.name


class MockPermission:
    def __init__(self, label=""):
        self.label = label



#         from pytest_bdd import given, when, then, scenario
# from unittest.mock import Mock
# import helpers

# @scenario('test_get_request_access.feature', 'User can get access to available modules')
# def test_get_request_access():
#     pass

# @scenario('test_get_request_access.feature', 'User encounters an error while getting access')
# def test_get_request_access_error():
#     pass

# @given("the user wants to request access to certain modules")
# def user_wants_to_request_access():
#     mock_request = Mock()
#     mock_request.GET.getlist.return_value = ["access_1", "access_2"]
#     return mock_request

# @when("the user requests access with valid parameters")
# def user_requests_access(user_wants_to_request_access):
#     return get_request_access(user_wants_to_request_access)

# @then("the function should return the available access modules")
# def function_should_return_available_access_modules(user_requests_access):
#     assert "accesses" in user_requests_access
#     assert len(user_requests_access["accesses"]) == 2

# @given("an error occurs while getting the available access modules")
# def error_occurs_while_getting_access():
#     mock_helpers = Mock()
#     mock_helpers.get_available_access_modules.side_effect = Exception("Error")
#     return mock_helpers

# @when("an error occurs while getting the available access modules")
# def error_occurs_while_getting_access_modules(error_occurs_while_getting_access):
#     mock_request = Mock()
#     return get_request_access(mock_request)

# @then("the function should return an error message")
# def function_should_return_error_message(error_occurs_while_getting_access_modules):
#     assert "status" in error_occurs_while_getting_access_modules
#     assert error_occurs_while_getting_access_modules["status"]["msg"] == "There was an error in getting the requested access resources. Please contact Admin"

