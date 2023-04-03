"""SlackAccessRevoke feature tests."""
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
from .. import access
from Access.access_modules.slack_access.helpers import invite_user ,remove_user


@scenario('features/revoke.feature', 'Revoke User Access to a workspace fails')
def test_revoke_user_access_to_a_workspace_fails():
    """Revoke User Access to a workspace fails."""
    pass


@scenario('features/revoke.feature', 'Revoke User Access to a workspace success')
def test_revoke_user_access_to_a_workspace_success():
    """Revoke User Access to a workspace success."""
    pass


@given('A user email')
def user_email():
    """A user email."""
    return "test@test.com"


@pytest.fixture
def user(mocker):
    user = mocker.MagicMock()
    user.email = user_email()
    return user

@pytest.fixture
def user_identity(mocker,user):
    user_identity = mocker.MagicMock()
    user_identity.user = user
    return user_identity

@pytest.fixture
def labels():
    form_label = {
          'action': 'WorkspaceAccess',
          'workspace_id': 'T01234', 
          'workspace_name': 'enigma-slack'
          }
    return form_label

@given('Access can not be revoked')
def access_cant_revoked(mocker):
    """Access can not be revoked."""
    client_mock = mocker.MagicMock()
    mocker.patch('Access.access_modules.slack_access.helpers.WebClient', return_value=client_mock)
    response_mock = {'ok': False}
    client_mock.users_lookupByEmail.return_value ={"ok": False, "error": "error message"}
    client_mock.admin_users_remove.return_value = response_mock
    result , error_mssg =remove_user('test@test.com', 'enigma-slack', 'T1234')
    assert result == False

@given('Access will be revoked')
def access_revoked(mocker):
    """Access will be revoked."""
    client_mock = mocker.MagicMock()
    mocker.patch('Access.access_modules.slack_access.helpers.WebClient', return_value=client_mock)
    response_mock = {'ok': True}
    client_mock.users_lookupByEmail.return_value ={"ok": True, "user": {"id": "123"}}
    client_mock.admin_users_remove.return_value = response_mock
    result , error_mssg =remove_user('test@test.com', 'enigma-slack', 'T1234')
    assert result == True


@when('I pass revoke request',target_fixture="context_output")
def revoke_request(user_identity,labels,user,mocker):
    """I pass revoke request."""
    slack_access = access.get_object()
    return slack_access.revoke(user, user_identity, labels,mocker.MagicMock())
    

@then('return value should be False')
def false_output(context_output):
    """return value should be False."""
    assert context_output is False
   


@then('return value should be True')
def true_output(context_output):
    """return value should be True."""
    assert context_output is True

