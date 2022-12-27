import pytest
from Access import helpers
from Access.helpers import getAvailableAccessModules, getAccessModules, getAccessRequestDetails

class MockAccessModule:
    def __init__(self, name=""):
        self.name = name
        self.available = True

    def tag(self):
        return "TAG"

    def access_desc(self):
        return "access_desc"

    def combine_labels_desc(self, access_labels):
        return access_labels

    def combine_labels_meta(self, access_labels):
        return access_labels

@pytest.mark.parametrize(
    "testName, available_accesses, expectedModuleList",
    [
        (
            "available_accesses has values",
            [MockAccessModule(name="name1"), MockAccessModule(name="name2")],
            [MockAccessModule(name="name1"), MockAccessModule(name="name2")],
        ),
        (
            "available_accesses has no values",
            [],
            [MockAccessModule(name="name3"), MockAccessModule(name="name4")],
        ),
    ],
)
def test_getAvailableAccessModules(
    mocker, testName, available_accesses, expectedModuleList
):
    mocker.patch("Access.helpers.getAccessModules", return_value=expectedModuleList)

    helpers.available_accesses = available_accesses
    modules = getAvailableAccessModules()
    assert len(modules) == len(expectedModuleList)
    for i in range(len(modules)):
        assert modules[i].name == expectedModuleList[i].name


@pytest.mark.parametrize(
    "testName, cached_accesses, expectedModuleList",
    [
        (
            "cached_accesses has values",
            [MockAccessModule(name="name1"), MockAccessModule(name="name2")],
            [MockAccessModule(name="name1"), MockAccessModule(name="name2")],
        ),
    ],
)
def test_getAccessModules(mocker, testName, cached_accesses, expectedModuleList):
    mocker.patch(
        "glob.glob", return_value=["dir1", "dir2"] + ["base_somedir", "__pycache__"]
    )
    mocker.patch("os.path.isfile", return_value=False)
    helpers.cached_accesses = cached_accesses
    modules = getAccessModules()
    assert len(modules) == len(expectedModuleList)
    for i in range(len(modules)):
        assert modules[i].name == expectedModuleList[i].name

# test for getAccessRequestDetails
@pytest.fixture
def each_access_request():
    class MockUser:
        def __init__(self):
            self.email = "test@test.com"

    class MockAccess:
        def __init__(self):
            self.access_tag = "TAG"
            self.access_label = "LABEL"

    class MockAccessRequest:
        def __init__(self):
            self.request_id = "1"
            self.request_reason = "Test reason"
            self.requested_on = "2022-12-27"
            self.user = MockUser()
            self.access = MockAccess()

    return MockAccessRequest()

def test_get_access_request_details(each_access_request):
    result = getAccessRequestDetails(each_access_request)
    assert result == {
        "access_tag": "TAG",
        "userEmail": "test@test.com",
        "requestId": "1",
        "accessReason": "Test reason",
        "requested_on": "2022-12-27",
        "accessType": "access_desc",
        "accessCategory": ['LABEL'],
        "accessMeta": ['LABEL']
    }
