import logging
import json
from Access.base_email_access.access import BaseEmailAccess
from bootprocess.general import emailSES
from .helpers import (
    invite_user,
    remove_user,
    get_workspace_list,
)

from . import constants
from django.template import loader

logger = logging.getLogger(__name__)


class Slack(BaseEmailAccess):
    """Slack Access module."""

    urlpatterns = []
    labels = "slack_access"

    def fetch_access_request_form_path(self):
        """Returns path to slack module access request form."""
        return "slack_access/access_request_form.html"

    def email_targets(self, user):
        """Returns email targets.
        Args:
            user (User): User whose access is being changed.
        Returns:
            array: Email address of the User and the module owners.
        """
        return [user.email] + self.grant_owner()

    def _generate_string_from_template(self, filename, **kwargs):
        template = loader.get_template(filename)
        vals = {}
        for key, value in kwargs.items():
            vals[key] = value
        return template.render(vals)

    def __send_approve_email(self, user, label_desc, request_id, approver):
        """Generates and sends email in access grant."""
        email_targets = self.email_targets(user)
        email_subject = "Approved Access: %s for access to %s for user %s" % (
            request_id,
            label_desc,
            user.email,
        )
        body = self._generate_string_from_template(
            filename="approve_email.html",
            label_desc=label_desc,
            user_email=user.email,
            approver=approver,
        )

        emailSES(email_targets, email_subject, body)

    def __send_revoke_email(self, user, label_desc, request_id):
        """Generates and sends email in for access revoke."""
        email_targets = self.email_targets(user)
        email_subject = "Revoke Request: %s for access to %s for user %s" % (
            request_id,
            label_desc,
            user.email,
        )
        email_body = ""

        emailSES(email_targets, email_subject, email_body)

    def approve(
        self,
        user_identity,
        labels,
        approver,
        request,
        is_group=False,
        auto_approve_rules=None,
    ):
        """Approves a users access request.
        Args:
            user_identity (User): User identity object represents user whose access is being approved.
            labels (str): Access Label that respesents the access to be approved.
            approver (User): User who is approving the access.
            request (UserAccessMapping): Access mapping that repesents the User Access.
            is_group (bool, optional): Whether the access is requested for a User or a Group.
                                       Defaults to False.
            auto_approve_rules (str, optional): Rules for auto approval. Defaults to None.
        Returns:
            bool: True if the access approval is success, False in case of failure with error string.
        """

        user = user_identity.user
        label_desc = self.combine_labels_desc(labels)
        for label in labels:
            workspace_name = label["workspace_name"]
            invite_user_resp = invite_user(
                user.email, label["workspace_id"], workspace_name
            )
            if not invite_user_resp:
                logger.error(
                    f"Could not invite user to requested workspace {workspace_name}. Please contact Admin."
                )
                return False

        try:
            self.__send_approve_email(user, label_desc, request.request_id, approver)
            return True
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
            return False

    def revoke(self, user, user_identity, label, request):
        """Revoke access to Slack.
        Args:
            user (User): User whose access is to be revoked.
            user_identity (UserIdentity): User Identity object represents identity of user.
            labels (str): Access label representing the access to be revoked.
            request (UserAccessMapping): UserAccessMapping representing the access.
        Returns:
            bool: True if revoke succeed. False if revoke fails.
            response: (array): Array of user details.
        """
        access_workspace = label["workspace_name"]
        response, error_message = remove_user(
            user_identity.user.email, access_workspace, label["workspace_id"]
        )
        if not response:
            logger.error(
                f"Could not remove user from requested workspace {access_workspace} : {error_message}"
            )
            return False

        label_desc = self.get_label_desc(label)
        try:
            self.__send_revoke_email(user, label_desc, request.request_id)
            return True
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))
            return False

    def get_label_desc(self, labels):
        """Returns access label description.
        Args:
            labels: access label whose access to be requested.
        Returns:
            string: Description of access label.
        """
        access_workspace = labels["workspace_name"]

        return "Slack access for Workspace: " + access_workspace

    def combine_labels_desc(self, labels):
        """Combines multiple labelss.
        Args:
            labelss (array): Array of access labels.
        Returns:
            str: Comma seperated access labels.
        """
        label_descriptions_set = set()
        for access_labe in labels:
            label_desc = self.get_label_desc(access_labe)
            label_descriptions_set.add(label_desc)

        return ", ".join(label_descriptions_set)

    def validate_request(self, labels, user, is_group=False):
        """Combines multiple labelss.
        Args:
            labelss_data (array): Array of access lables types.
            request_user (UserAccessMaping): Object of UserAccessMapping represents requested user.
        Returns:
            array (json objects): key value pair of access lable and it's access type.
        """
        valid_labels_array = []

        for label in labels:
            slack_workspace_data = label["slackAccessWorkspace"]
            slack_workspace_data = json.loads(slack_workspace_data.replace("'", '"'))

            if slack_workspace_data is None:
                raise Exception(constants.ERROR_MESSAGES)

            if not slack_workspace_data.get("workspacename"):
                raise Exception(constants.VALID_WORKSPACE_REQUIRED_ERROR)

            if not slack_workspace_data.get("workspace_id"):
                raise Exception(constants.VALID__WORKSPACE_ID_REQUIRED_ERROR)

            valid_labels = {
                "action": "WorkspaceAccess",
                "workspace_id": slack_workspace_data["workspace_id"],
                "workspace_name": slack_workspace_data["workspacename"],
            }

            valid_labels_array.append(valid_labels)

        return valid_labels_array

    def access_request_data(self, request, is_group=False):
        workspace_data = [workspace for workspace in get_workspace_list()]
        data = {"slackWorkspaceList": workspace_data}
        return data

    def get_identity_template(self):
        """Returns path to user identity form template"""
        return ""
    
    def verify_identity(self, request, email):
        """Verifying user Identity.
        Returns:
            json object: Empty.
        """

        return {}

    def can_auto_approve(self):
        """Checks if access can be auto approved or manual approval is needed.
        Returns:
            bool: True for auto access and False for manual approval.
        """
        return False

    def access_types(self):
        """Returns types of slack access.
        Returns:
            array of json object: type of access type and description of access type.
        """
        return []

    def access_desc(self):
        """Returns slack access description."""
        return "Slack Access"

    def tag(self):
        """Returns slack access tag."""
        return "slack_access"


def get_object():
    """Returns instance of Slack access Module."""
    return Slack()
