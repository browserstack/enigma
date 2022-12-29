import traceback
from django.shortcuts import render, redirect
import logging
import json

from bootprocess.general import emailSES
from BrowserStackAutomation.settings import ACCESS_APPROVE_EMAIL
from Access.models import UserAccessMapping, GroupAccessMapping

logger = logging.getLogger(__name__)

# Use this base module when the access requires only sending a mail
# to multiple dedicated emails
# for super to work in python 2 
class BaseEmailAccess(object):
    available = True
    group_access_allowed = True

    def grant_owner(self):
        return [ ACCESS_APPROVE_EMAIL ]

    def revoke_owner(self):
        return [ ACCESS_APPROVE_EMAIL ]

    # Override in module for specific person who should mark access as revoked
    def access_mark_revoke_permission(self, access_type):
        return ACCESS_REVOKE_PERMISSIONS_MAPPING["security"]

    # module's tag() method should return a tag present in hash returned by access_types() "type" key
    def get_label_desc(self, access_label):
        data = next((each_access['desc'] for each_access in self.access_types() if each_access['type'] == access_label["data"]), "")
        for key in access_label:
            if key != "data":
                data += " ->  "+key+" - "+access_label[key]
        return data

    def combine_labels_desc(self,access_labels):
        label_desc_array = [self.get_label_desc(access_label) for access_label in access_labels]
        return ", ".join(label_desc_array)
    
    def get_label_meta(self, request_params):
        return {}

    def combine_labels_meta(self, access_labels):
        return {}

    def access_request_data(self, request, is_group=False):
        return {}

    def is_custom_secondary_approval_flow(self):
        return False

    def fetch_approver_permissions(self):
        return {
            "1": "ACCESS_APPROVE"
        }

    def get_pending_accesses(self, request, user_permissions):
        return {
            "individual_requests": self.get_pending_individual_accesses(user_permissions),
            "group_requests": self.get_pending_group_accesses(user_permissions),
        }

    def get_pending_individual_accesses(self, user_permissions):
        return self.get_pending_accesses_from_mapping(UserAccessMapping, user_permissions)

    def get_pending_group_accesses(self, user_permissions):
        return self.get_pending_accesses_from_mapping(GroupAccessMapping, user_permissions)
        
    def query_pending_accesses(self, mapping, pending_status):
        access_tag = self.tag()
        pending_accesses = []

        for pending_request in mapping.objects.filter(status=pending_status, access__access_tag=access_tag):
            pending_accesses.append(mapping.getAccessRequestDetails(pending_request, self))
        
        return pending_accesses

    def get_pending_accesses_from_mapping(self, mapping, user_permissions):
        pending_requests = []
        module_permissions = self.fetch_approver_permissions()

        status = None
        if module_permissions["1"] in user_permissions:
            status = "Pending"
        elif "2" in module_permissions and module_permissions["2"] in user_permissions and not self.is_custom_secondary_approval_flow():
            status = "SecondaryPending"

        if status: pending_requests = self.query_pending_accesses(mapping, status)

        if self.is_custom_secondary_approval_flow():
            secondary_pending_requests = self.query_pending_accesses(mapping, "SecondaryPending")

            for secondary_pending_request in secondary_pending_requests:
                req_obj = mapping.objects.get(request_id=secondary_pending_request["requestId"])
                access_label = req_obj.access.access_label
                request_specific_approver_permissions = self.fetch_approver_permissions(access_label) if access_label is not None else self.fetch_approver_permissions()
                if "2" in request_specific_approver_permissions and request_specific_approver_permissions["2"] in user_permissions and req_obj.status == "SecondaryPending":
                    pending_requests.append(secondary_pending_request)

        return pending_requests

    def approve(self, user, labels, approver, requestId, is_group=False, auto_approve_rules = None):
        try:
            label_desc = self.combine_labels_desc(labels)
            email_targets = self.email_targets(user)
            email_subject = "Approved Access: %s for access to %s for user %s" % ( requestId, self.access_desc(), user.email )
            if auto_approve_rules:
                email_body = "Access successfully granted for %s for %s to %s.<br>Request has been approved by %s. <br> Rules :- %s" % (label_desc, self.access_desc(), user.email, approver, ", ".join(auto_approve_rules))
            else:
                email_body = "Please grant access for %s for %s to %s. Request has been approved by %s" % ( label_desc, self.access_desc(), user.email, approver)

                emailSES(email_targets, email_subject, email_body)
                return True, ""
        except Exception as e:
            logger.error("Could not send email for error %s", str(traceback.format_exc()))
            return False, str(traceback.format_exc())

    def revoke(self, user, label):
        label_desc = self.get_label_desc(label)

        email_targets = self.email_targets()
        email_subject = "Revoke Request: %s for %s" % ( label_desc, user.email )
        email_body = ""

        try:
            emailSES(email_targets, email_subject, email_body)
        except Exception as e:
            logger.error("Could not send email for error %s", str(e))

    def get_extra_fields(self):
        return []

    # return valid access label array which will be added in db or raise exception
    def validate_request(self, access_labels_data, request_user, is_group=False):
        valid_access_label_array = []
        for access_label_data in access_labels_data:
            valid_access_label = {"data" : access_label_data}
            valid_access_label_array.append(valid_access_label)
        return valid_access_label_array


    def fetch_access_approve_email(self, request, data):
        context_details = {
            'approvers': {
                'primary': data['approvers']['primary'],
                'other': data['approvers']['other']
            },
            'requestId': data['requestId'],
            'user': request.user,
            'requestData': data['request_data'],
            'accessType': self.tag(),
            'accessDesc': self.access_desc(),
            'isGroup': data['is_group']
        }
        return str(render(request, 'base_email_access/accessApproveEmail.html', context_details).content.decode("utf-8"))

    def fetch_access_request_form_path(self):
        return 'base_email_access/accessRequest.html'
