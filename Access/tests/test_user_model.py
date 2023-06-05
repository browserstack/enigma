from unittest.mock import Mock
import pytest

from Access.models import User
from Access.tests.helper_mocks import MockPermission


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
            [
                "APPROVER PERMISSION 1",
                "APPROVER PERMISSION 2",
                "PERMISSION 1",
                "PERMISSION 2",
            ],
            [
                "APPROVER PERMISSION 1",
                "APPROVER PERMISSION 2",
                "APPROVER PERMISSION 3",
                "APPROVER PERMISSION 4",
            ],
            True,
        ),
    ],
)
def test_is_an_approver(
    mocker, testName, permissionLabels, approverPermissions, expectedAnswer
):
    mocker.patch("Access.models.User.user", return_value=Mock())
    mocker.patch("Access.models.User.permissions", return_value=Mock())

    permissions = []
    for eachPermissionLabel in permissionLabels:
        permissions.append(MockPermission(eachPermissionLabel))

    accessUser = User()
    accessUser.permissions = permissions
    assert accessUser.is_an_approver(approverPermissions) == expectedAnswer
