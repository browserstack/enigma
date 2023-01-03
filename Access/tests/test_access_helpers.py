import pytest
from functools import partial
from unittest.mock import Mock

from Access import helpers
from Access.helpers import getAvailableAccessModules, getAccessModules, isUserAnApprover, getPossibleApproverPermissions

class MockAccessModule:
    def __init__(self, name="", primaryApproverPermissionLabel="", secondaryApproverPermissionLabel=""):
        self.name = name
        self.available = True
        if primaryApproverPermissionLabel != "":
            permissions = {
                    "1": primaryApproverPermissionLabel,
                    }
            if secondaryApproverPermissionLabel != "":
                permissions["2"] = secondaryApproverPermissionLabel
            self.fetch_approver_permissions = Mock(return_value=permissions)

class MockPermission:
    def __init__(self, label=""):
        self.label = label

class MockAccessUser:
    def __init__(self, permissionLabels=[]):
        self.permissions = []
        for each_permission_label in permissionLabels:
            self.permissions.extend([MockPermission(each_permission_label)])

class MockDjangoUser:
    def __init__(self, permissionLabels=[]):
        self.user = MockAccessUser(permissionLabels)


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

@pytest.mark.parametrize(
    "testName, permissionLabels, approverPermissions, expectedAnswer",
    [
        (
            "user is not any kind of approver",
            ["PERMISSION 1", "PERMISSION 2"],
            ["APPROVER PERMISSION 1", "APPROVER PERMISSION 2"],
            False,
        ),
        (
            "user does not have any permissions",
            [],
            ["APPROVER PERMISSION 1", "APPROVER PERMISSION 2"],
            False,
        ),
        (
            "user is approver for multiple types of accesses",
            ["APPROVER PERMISSION 1", "APPROVER PERMISSION 2", "PERMISSION 1", "PERMISSION 2"],
            ["APPROVER PERMISSION 1", "APPROVER PERMISSION 2", "APPROVER PERMISSION 3", "APPROVER PERMISSION 4"],
            True,
        ),
    ],
)
def test_isUserAnApprover(mocker, testName, permissionLabels, approverPermissions, expectedAnswer):
    mocker.patch("Access.helpers.getPossibleApproverPermissions", return_value=approverPermissions)
    mockUser = MockDjangoUser(permissionLabels)
    assert isUserAnApprover(mockUser) == expectedAnswer

@pytest.mark.parametrize(
    "testName, modulesPresent, expectedApprovers",
    [
        (
            "no modules are overriding fetch_approver_permissions",
            [MockAccessModule(name="name1"), MockAccessModule(name="name2")],
            ["ACCESS_APPROVE"],
        ),
        (
            "some modules are overriding fetch_approver_permissions",
            [MockAccessModule(name="name1", primaryApproverPermissionLabel="PERM1", secondaryApproverPermissionLabel="PERM2"), MockAccessModule(name="name2")],
            ["ACCESS_APPROVE", "PERM1", "PERM2"],
        ),
        (
            "all modules are overriding fetch_approver_permissions with overlaps",
            [MockAccessModule(name="name1", primaryApproverPermissionLabel="PERM1", secondaryApproverPermissionLabel="PERM2"), MockAccessModule(name="name2", primaryApproverPermissionLabel="PERM1")],
            ["PERM1", "PERM2"],
        ),
        (
            "all modules are overriding fetch_approver_permissions without overlaps",
            [MockAccessModule(name="name1", primaryApproverPermissionLabel="PERM1", secondaryApproverPermissionLabel="PERM2"), MockAccessModule(name="name2", primaryApproverPermissionLabel="PERM3")],
            ["PERM1", "PERM2", "PERM3"],
        ),
    ],
)
def test_getPossibleApproverPermissions(mocker, testName, modulesPresent, expectedApprovers):
    mocker.patch("Access.helpers.getAvailableAccessModules", return_value=modulesPresent)
    assert getPossibleApproverPermissions() == expectedApprovers
