"""SlackAccess Grant feature tests."""
import pytest
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
from .. import access
from Access.access_modules.slack_access.helpers import invite_user


@scenario('features/approve.feature', 'Grant Slack Workspace Access Fails')
def test_grant_slack_workspace_access_fails():
    """Grant Slack Workspace Access Fails."""
    pass


@scenario('features/approve.feature', 'Grant Slack Workspace Access Success')
def test_grant_slack_workspace_access_success():
    """Grant Slack Workspace Access Success."""
    pass


@given('A user email',target_fixture="user_email")
def user_email():
    """A user email."""
    return 'test@test.com'


@given('user in not invited earlier for workspace',target_fixture="user_not_invited_output")
def user_not_invited_earlier(mocker):
    """user in not invited earlier for workspace."""
    client_mock = mocker.MagicMock()
    mocker.patch('Access.access_modules.slack_access.helpers.WebClient', return_value=client_mock)
    response_mock = {'ok': True}
    client_mock.admin_conversations_search.return_value ={
    "ok": True,
    "conversations": [
        {
            "id": "GSEV0B5PY",
            "name": "privacy-channel"
         
        }
    ],
    "next_cursor": "aWQ6Mw=="
}
    client_mock.admin_users_invite.return_value = response_mock
    result = invite_user('test@example.com', '123', 'enigma-slack')
    assert result == True



@given('Access can be granted to user for slack')
def access_can_be_granted(mocker):
    """Access can be granted to user for slack."""
    client_mock = mocker.MagicMock()
    mocker.patch('Access.access_modules.slack_access.helpers.WebClient', return_value=client_mock)
    response_mock = {'ok': True}
    client_mock.admin_conversations_search.return_value ={
    "ok": True,
    "conversations": [
        {
            "id": "GSEV0B5PY",
            "name": "privacy-channel",
            "purpose": "Group messaging with: @rita @nwhere @meanie",
            "member_count": -1,
            "created": 1578423973,
            "creator_id": "WPQ65MVKK",
            "is_private": True,
            "is_archived": True,
            "is_general": False,
            "last_activity_ts": 1583198954000200,
            "is_ext_shared": False,
            "is_global_shared": True,
            "is_org_default": False,
            "is_org_mandatory": False,
            "is_org_shared": True,
            "is_frozen": False,
            "connected_team_ids": [],
            "internal_team_ids_count": 4,
            "internal_team_ids_sample_team": "T013F30DBAB",
            "pending_connected_team_ids": [],
            "is_pending_ext_shared": False
        }
    ],
    "next_cursor": "aWQ6Mw=="
}
    client_mock.admin_users_invite.return_value = response_mock
    result = invite_user('test@example.com', '123', 'enigma-slack')
    assert result == True

@given('Access cannot be granted to user for slack')
def access_cant_be_granted(mocker):
    """Access cannot be granted to user for slack."""
    client_mock = mocker.MagicMock()
    mocker.patch('Access.access_modules.slack_access.helpers.WebClient', return_value=client_mock)
    response_mock = {'ok': False}
    client_mock.admin_users_invite.return_value = response_mock
    result = invite_user('test@example.com', '123', 'enigma-slack')
    assert result == False

@pytest.fixture
def user_identity(mocker):
    user_identity = mocker.MagicMock()
    user_identity.user.email = user_email()
    return user_identity

@pytest.fixture
def labels():
    form_label =  [
         {
          'action': 'WorkspaceAccess',
          'workspace_id': 'T01234', 
          'workspace_name': 'enigma-slack'
          }
      ]
    return form_label


@when('I pass approval request',target_fixture="context_output")
def approve_request(labels ,user_identity ,mocker):
    """I pass approval request."""
    slack_access = access.get_object()
    return slack_access.approve(user_identity, labels, "test-approver",mocker.MagicMock())


@then('return value should be False')
def false_output(context_output):
    """return value should be False."""
    return_value = context_output
    assert return_value is False


@then('return value should be True')
def true_output(context_output):
    """return value should be True."""
    return_value = context_output
    assert return_value is True

