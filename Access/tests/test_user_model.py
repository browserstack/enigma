import pytest
from functools import partial
from unittest.mock import Mock
from django.contrib.auth.models import User as DjangoUser

from Access import helpers
from Access.models import User, Role, Permission
from Access.helpers import getPossibleApproverPermissions
from Access.tests.helper_mocks import MockDjangoUser

@pytest.fixture
def user_setup():
    djangoUser = DjangoUser()
    djangoUser.save()

    accessUser = User()
    accessUser.user = djangoUser
    accessUser.save()

    role = Role()
    role.save()
    accessUser.role.add(role)
    return accessUser

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
@pytest.mark.django_db
def test_isAnApprover(user_setup, mocker, testName, permissionLabels, approverPermissions, expectedAnswer):
    mocker.patch("Access.helpers.getPossibleApproverPermissions", return_value=approverPermissions)

    for permissionLabel in permissionLabels:
        permission = Permission()
        permission.label = permissionLabel
        permission.save()
        user_setup.role.all()[0].permission.add(permission)

    assert user_setup.isAnApprover(approverPermissions) == expectedAnswer
