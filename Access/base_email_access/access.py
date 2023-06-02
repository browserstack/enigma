from django.shortcuts import render
import logging
import traceback

from Access.models import UserAccessMapping, GroupAccessMapping
from EnigmaAutomation.settings import ACCESS_APPROVE_EMAIL, PERMISSION_CONSTANTS
from bootprocess.general import email_via_smtp

logger = logging.getLogger(__name__)


# Use this base module when the access requires only sending a mail
# to multiple dedicated emails
# for super to work in python 2
class BaseEmailAccess(object):
    available = True
    group_access_allowed = True

    def grant_owner(self):
        return [ACCESS_APPROVE_EMAIL]

    def revoke_owner(self):
        return [ACCESS_APPROVE_EMAIL]

    # Override in module for specific person who should mark access as revoked
    def access_mark_revoke_permission(self, access_type):
        return ACCESS_APPROVE_EMAIL

    # module's tag() method should return a tag present in
    # hash returned by access_types() "type" key
    def get_label_desc(self, access_label):
        data = next(
            (
                each_access["desc"]
                for each_access in self.access_types()
                if each_access["type"] == access_label["data"]
            ),
            "",
        )
        for key in access_label:
            if key != "data":
                data += " ->  " + key + " - " + access_label[key]
        return data

    def combine_labels_desc(self, access_labels):
        label_desc_array = [
            self.get_label_desc(access_label) for access_label in access_labels
        ]
        return ", ".join(label_desc_array)

    def get_label_meta(self, request_params):
        return {}

    def combine_labels_meta(self, access_labels):
        return {}

    def access_request_data(self, request, is_group=False):
        return {}

    def fetch_approver_permissions(self, access_label=None):
        return {"1": PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]}

    def get_pending_accesses(self, accessUser):
        pending_access_objects = self.get_pending_access_objects(accessUser)
        return {
            request_type: [
                request.getAccessRequestDetails(self) for request in all_requests
            ]
            for request_type, all_requests in pending_access_objects.items()
        }

    def get_pending_access_objects(self, accessUser):
        return {
            "individual_requests": self.__get_pending_individual_access_objects(
                accessUser
            ),
            "group_requests": self.__get_pending_group_access_objects(accessUser),
        }

    def __get_pending_individual_access_objects(self, accessUser):
        return self.__get_pending_access_objects_from_mapping(
            UserAccessMapping, accessUser
        )

    def __get_pending_group_access_objects(self, accessUser):
        return self.__get_pending_access_objects_from_mapping(
            GroupAccessMapping, accessUser
        )

    def __query_pending_accesses(self, mapping, pending_status):
        return mapping.objects.filter(
            status=pending_status, access__access_tag=self.tag()
        )

    def __query_pending_accesses_for_user(self, accessUser, mapping, pending_status):
        user_pending_requests = []
        all_pending_requests = self.__query_pending_accesses(mapping, pending_status)

        for each_pending_request in all_pending_requests:
            approverType = "Primary" if pending_status == "Pending" else "Secondary"

            if accessUser.isAnApproverForModule(
                self, each_pending_request.access.access_label, approverType
            ):
                user_pending_requests.append(each_pending_request)

        return user_pending_requests

    def __get_pending_access_objects_from_mapping(self, mapping, accessUser):
        user_pending_requests = []

        user_pending_requests.extend(
            self.__query_pending_accesses_for_user(accessUser, mapping, "Pending")
        )
        user_pending_requests.extend(
            self.__query_pending_accesses_for_user(
                accessUser, mapping, "SecondaryPending"
            )
        )

        return user_pending_requests

    def approve(
        self, user, labels, approver, requestId, is_group=False, auto_approve_rules=None
    ):
        try:
            label_desc = self.combine_labels_desc(labels)
            email_targets = self.email_targets(user)
            email_subject = "Approved Access: %s for access to %s for user %s" % (
                requestId,
                self.access_desc(),
                user.email,
            )
            if auto_approve_rules:
                email_body = (
                    "Access successfully granted for %s for %s to %s.<br>Request has"
                    " been approved by %s. <br> Rules :- %s"
                    % (
                        label_desc,
                        self.access_desc(),
                        user.email,
                        approver,
                        ", ".join(auto_approve_rules),
                    )
                )
            else:
                email_body = (
                    "Please grant access for %s for %s to %s. Request has been approved"
                    " by %s" % (label_desc, self.access_desc(), user.email, approver)
                )

                self.email_via_smtp(email_targets, email_subject, email_body)
                return True, ""
        except Exception as e:
            logger.error(
                "Could not send email for error %s", str(traceback.format_exc())
            )
            logger.error(e)
            return False, str(traceback.format_exc())

    def revoke(self, user, label):
        label_desc = self.get_label_desc(label)

        email_targets = self.email_targets()
        email_subject = "Revoke Request: %s for %s" % (label_desc, user.email)
        email_body = ""

        try:
            self.email_via_smtp(email_targets, email_subject, email_body)
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))

    def get_extra_fields(self):
        return []

    def can_auto_approve(self):
        return False

    # return valid access label array which will be added in db or raise exception
    def validate_request(self, access_labels_data, request_user, is_group=False):
        valid_access_label_array = []
        for access_label_data in access_labels_data:
            valid_access_label = {"data": access_label_data}
            valid_access_label_array.append(valid_access_label)
        return valid_access_label_array

    def fetch_access_approve_email(self, request, data):
        context_details = {
            "approvers": {
                "primary": data["approvers"]["primary"],
                "other": data["approvers"]["other"],
            },
            "requestId": data["requestId"],
            "user": request.user,
            "requestData": data["request_data"],
            "accessType": self.tag(),
            "accessDesc": self.access_desc(),
            "isGroup": data["is_group"],
        }
        return str(
            render(
                request, "base_email_access/accessApproveEmail.html", context_details
            ).content.decode("utf-8")
        )

    def fetch_access_request_form_path(self):
        return "base_email_access/accessRequest.html"

    def email_via_smtp(self, destination, subject, body):
        """
         method to send email via smtp.
         It is calling bootprocess.general.email_via_smtp under the hood to reduce external imports of bootprocess in
         access_modules
        """
        email_via_smtp(destination, subject, body)
