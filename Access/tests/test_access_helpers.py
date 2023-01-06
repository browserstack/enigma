import pytest
from functools import partial

from Access import helpers
from Access.helpers import getAvailableAccessModules, getAccessModules, getPossibleApproverPermissions
from Access.tests.helper_mocks import MockAccessModule

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
    assert getPossibleApproverPermissions().sort() == expectedApprovers.sort()
