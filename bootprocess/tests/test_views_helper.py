""" test file for views_helper """
import threading
import pytest
from bootprocess import views_helper
from Access import models
from enigma_automation.settings import DEFAULT_ACCESS_GROUP


class MockAuthUser:
    """ mocking AuthUser """
    def __init__(self, username="", user=""):
        self.user = user
        self.username = username


class MockRequest:
    """ mocking Request """
    def __init__(self, username=""):
        self.user = MockAuthUser(username)


@pytest.mark.parametrize(
    (
        "_test_name, user_is_in_default_access_group,"
        " group_count"
    ),
    [
        # user is not part of default group and has respective count of git repo,
        # dashboard, ssh machines and group accesses
        ("UserInDefaultGroup", True, 40),
        ("UserInDefaultGroup", False, 40),
    ],
)
def test_get_dashboard_data(monkeypatch, _test_name, user_is_in_default_access_group, group_count):
    """ method to test get_dashboard_data """
    class MockUserModelobj:
        """ mocking method UserModelobj """
        def __init__(self, user="", gitusername="", name=""):
            self.user = user
            self.gitusername = gitusername
            self.name = name

        def get(self, user__username=""):
            """ mocked method get """
            self.user = user__username
            return MockUserModelobj(user="username", gitusername="username")

    class MockGitAccessModelobj:
        """ mocking GitAccessModelobj """
        def __init__(self, request_info=None):
            del request_info
            self.user = ""

        def filter(self, requester="", status=""):
            """ mocked method filter """
            del requester
            if status == "Approved":
                return [MockGitAccessModelobj()]
            return MockGitAccessModelobj()

    class MockGroupV2:
        """ mocking class GroupV2 """
        def filter(self, name="", status=""):
            """ mocked method filter """
            del name
            if status == "Approved":
                return [MockGroupV2()]
            return MockGitAccessModelobj()

    class MockUserAccessMapping:
        """ mocking UserAccessMapping """
        def filter(self, user="", status="", access__access_tag=""):
            """ mocked method filter """
            del user, status
            if access__access_tag == "other":
                return []
            if access__access_tag == "github_access":
                return []
            if access__access_tag == "ssh":
                return []
            group = []
            for i in range(group_count):
                group.append(i)
            return group

    class Group:
        """ class Group """
        def __init__(self):
            self.name = ""

    class MockMembershipV2:
        """ mocking class MembershipV2 """
        def __init__(self, is_owner=False, approver="", status="", user=""):
            self.is_owner = is_owner
            self.approver = approver
            self.status = status
            self.user = user
            self.group = Group()

        def filter(self, user="", status="", group="", is_owner=False):
            """ mocked method filter """
            del user, status, group
            if is_owner:
                return [MockMembershipV2()]
            return MockMembershipV2()

        def only(self, _filter):
            """ mocked method only """
            return MockMembershipV2()

        def create(self, *_, **__):
            """ mocked method create """
            return MockMembershipV2()

        def save(self):
            """ mocked method save """
            return ""

        def __str__(self):
            if user_is_in_default_access_group:
                return DEFAULT_ACCESS_GROUP
            return ""

        def __len__(self):
            return group_count

    class MockThread:
        """ class for mocking Thread """
        def start(self):
            """ method to mock start method of Thread """
            return True

    def mockgenerate_user_mappings(*_, **__):
        return []

    views_helper.generate_user_mappings = mockgenerate_user_mappings

    def mock_thread(*_, **__):
        return MockThread()

    monkeypatch.setattr(threading, "Thread", mock_thread)

    models.MembershipV2.objects = MockMembershipV2()
    models.User.objects = MockUserModelobj()
    models.UserAccessMapping.objects = MockUserAccessMapping()
    models.GroupV2.objects = MockGroupV2()
    request = MockRequest(username="username1")
    context = views_helper.get_dashboard_data(request)
    assert context["regions"] == ["eu-central-1"]
    assert context["groupCount"] == group_count
