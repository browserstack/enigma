""" module for sending notifications and emails """
import logging
from bootprocess import general
from Access import helpers
from enigma_automation.settings import MAIL_APPROVER_GROUPS

logger = logging.getLogger(__name__)

NEW_GROUP_EMAIL_SUBJECT = "Request for creation of new group from:"
NEW_GROUP_APPROVED_SUBJECT = "New Group Created ({})"
NEW_GROUP_APPROVED_BODY = (
    "New group with name {} has been created with owner being {} <br>"
)
NEW_MEMBERS_ADDED_MESSAGE = "The following members have been added to this team<br>"
MEMBERSHIP_ACCEPTED_SUBJECT = "Access approved for addition of {} to group - {}"
MEMBERSHIP_ACCEPTED_BODY = "Access approved for addition of {} to group - {} by {}. \
<BR/>Automated accesses will be triggered shortly. \
Access grant mails will be sent to tool owners for manual access."
ACCESS_GRANT_FAILED_MESSAGE = "Request by {} having Request ID {} is GrantFailed. \
Please debug and rerun the grant.<BR/>"
GROUP_ACCESS_ADDED_SUBJECT = "Group: {group_name}  new access added"
USER_ACCESS_REQUEST_DENIED_SUBJECT = (
    "[Enigma][Access Management] {} - {} - {} Request Denied"
)
USER_ACCESS_REQUEST_GRANT_FAILURE_SUBJECT = "[Enigma][Access Management] {} - {} - {} \
    Failed to Approve Request"
USER_REQUEST_RESOLVE_SUBJECT = "[Enigma][Access Management] - Request Resolved - {}"


def send_new_group_create_notification(auth_user, date_time, new_group, member_list):
    """ method to send group create notification """
    subject = NEW_GROUP_EMAIL_SUBJECT + auth_user.email + " -- " + date_time
    body = helpers.generateStringFromTemplate(
        filename="groupCreationEmailBody.html",
        user=str(auth_user.user),
        first_name=auth_user.first_name,
        last_name=auth_user.last_name,
        email=auth_user.email,
        groupName=new_group.name,
        memberList=generate_group_member_table(member_list),
        reason=new_group.description,
        needsAccessApprove=new_group.needsAccessApprove,
    )
    general.email_via_smtp(MAIL_APPROVER_GROUPS, subject, body)
    logger.debug("Email sent for %s to %s ", subject, str(MAIL_APPROVER_GROUPS))


def send_new_group_approved_notification(group, group_id, initial_member_names):
    """ method to send new group approved notification """
    subject = NEW_GROUP_APPROVED_SUBJECT.format(group.name)
    body = NEW_GROUP_APPROVED_BODY.format(group.name, group.requester.user.username)
    if initial_member_names:
        body += NEW_MEMBERS_ADDED_MESSAGE
        body += generate_group_member_table(initial_member_names)
    body = helpers.generateStringFromTemplate(filename="email.html", emailBody=body)
    destination = []
    destination += MAIL_APPROVER_GROUPS[:]
    destination.append(group.requester.email)

    logger.debug("%s -- Approved email sent to - %s", group_id, str(destination))
    general.email_via_smtp(destination, subject, body)


def send_membership_accepted_notification(user, group, membership):
    """ method to send membership accepted notification """
    subject = MEMBERSHIP_ACCEPTED_SUBJECT.format(user.name, group.name)
    body = helpers.generateStringFromTemplate(
        filename="membershipAcceptedEmailBody.html",
        user_name=user.name,
        group_name=group.name,
        approver=membership.approver.name,
    )
    destination = []
    destination.append(membership.requested_by.email)
    destination.append(user.email)
    general.email_via_smtp(destination, subject, body)


def send_mulitple_membership_accepted_notification(all_user_emails, group_name, membership):
    """ method to send multiple membership accepted notification """
    for each_user_email in all_user_emails.keys():
        subject = MEMBERSHIP_ACCEPTED_SUBJECT.format(each_user_email, group_name)
        body = helpers.generateStringFromTemplate(
            filename="membershipAcceptedEmailBody.html",
            user_name=",".join(each_user_email),
            group_name=group_name,
            approver=membership.approver.name,
        )
        destination = []
        destination.append(membership.requested_by.email)
        destination.append(each_user_email)
        general.email_via_smtp(destination, subject, body)


def generate_group_member_table(member_list):
    """ method to generate group number table """
    if len(member_list) <= 0:
        return "No members are being added initially"
    return helpers.generateStringFromTemplate("listToTable.html", memberList=member_list)


def send_group_owners_update_mail(destination, group_name, updated_by):
    """ method to send email for group owners update """
    try:
        subject = "Enigma Group '" + group_name + "' owners changed"
        body = f"\nGroup Name :- {group_name} \nupdated owners :- " \
               f"{', '.join(destination)} \nupdated by :- {updated_by}"

        general.email_via_smtp(destination, subject, body)
    except Exception as exc:
        logger.exception(str(exc))
        logger.error("Something when wrong while sending Email.")


def send_group_access_add_email(
    destination, group_name, requester, request_id, member_list
):
    """ method to send email for group access add """
    body = helpers.generateStringFromTemplate(
        filename="email.html",
        emailBody=helpers.generateStringFromTemplate(
            "add_access_to_group.html",
            request_id=request_id,
            group_name=group_name,
            requester=requester,
            member_list=member_list,
        ),
    )
    subject = GROUP_ACCESS_ADDED_SUBJECT.format(group_name=group_name)
    general.email_via_smtp(destination, subject, body)
    return ""


def send_revoke_failure_mail(
    targets, request_id, revoker_email, retries, message, access_tag=None
):
    """ method to send email for revoke failure """
    try:
        subject = f"Celery Revoke Failed for the request: {request_id}"
        body = helpers.generateStringFromTemplate(
            "celery_revoke_failure_email.html",
            request_id=request_id,
            revoker_email=revoker_email,
            retries=retries,
            message=message,
            access_tag=access_tag,
        )

        general.email_via_smtp(targets, subject, body)
    except Exception as exc:
        logger.error("Something when wrong while sending membership revoke email")
        logger.exception(str(exc))


def send_mail_for_request_decline(
    request, description, request_id, reason, access_type
):
    """ method to send email for request decline """
    auth_user = request.user
    destination = [auth_user.email]
    subject = USER_ACCESS_REQUEST_DENIED_SUBJECT.format(
        auth_user.email, access_type, description
    )
    body = helpers.generateStringFromTemplate(
        filename="requestDeclineEmail.html",
        user=auth_user.email,
        request_id=request_id,
        approver=request.user.username,
        reason=reason,
    )
    general.email_via_smtp(destination, subject, body)
    logger.debug("Email sent for %s to %s", subject, str(destination))


def send_mail_for_request_granted_failure(user, approver, access_type, request_id):
    """ method to send email for request granted failure """
    destination = [user.email]
    destination.append(approver.email)
    subject = USER_ACCESS_REQUEST_GRANT_FAILURE_SUBJECT.format(
        str(user.email), access_type.upper(), request_id
    )
    body = f"Request by {str(user.email)} having Request ID {request_id} could not be approved."
    general.email_via_smtp(destination, subject, body)
    logger.debug("Email sent for %s to %s", subject, str(destination))


def send_mail_for_member_approval(user_email, requester, group_name, reason):
    """ method to send email for member approval """
    primary_approver, other_approver = helpers.get_approvers()
    subject = (
        "Request for addition of new members to group ("
        + group_name
        + ")"
        + "["
        + primary_approver
        + "]"
    )
    destination = MAIL_APPROVER_GROUPS[:]
    body = helpers.generateStringFromTemplate(
        filename="email.html",
        emailBody=generate_user_add_to_group_email_body(
            user_email,
            primary_approver,
            other_approver,
            requester,
            group_name,
            reason,
        ),
    )
    general.email_via_smtp(destination, subject, body)


def generate_user_add_to_group_email_body(
    user_email, primary_approver, other_approver, requester, group_name, reason
):
    """ method to generate user add to group email body """
    return helpers.generateStringFromTemplate(
        filename="add_user_to_group_mail.html",
        user_email=user_email,
        primary_approver=primary_approver,
        other_approver=other_approver,
        requester=requester,
        group_name=group_name,
        reason=reason,
    )


def send_mail_for_access_grant_failed(
    destination, access_type, user_email, request_id, message
):
    """ method to send email for access grant failed """
    destination = [destination]
    subject = str("Access Grant Failed - ") + access_type.upper()
    body = ACCESS_GRANT_FAILED_MESSAGE.format(user_email, request_id)
    body = body + "Failure Reason - " + message
    general.email_via_smtp(destination, subject, body)


def send_group_access_declined(
    destination, group_name, requester, decliner, request_id, declined_access, reason
):
    """ method to send email for group access declined """
    body = helpers.generateStringFromTemplate(
        "groupAccessDeclined.html",
        request_id=request_id,
        requester=requester,
        decliner=decliner,
        group_name=group_name,
        declined_access=declined_access,
        reason=reason,
    )

    subject = subject = "Declined Request " + request_id
    general.email_via_smtp(destination, subject, body)


def send_accept_group_access_failed(destination, request_id, error):
    """ method to send email for accept group access failed """
    try:
        body = helpers.generateStringFromTemplate(
            "acceptGroupAccessFailed.html", request_id=request_id, error=error
        )

        subject = subject = "Failed Request " + request_id
        general.email_via_smtp(destination, subject, body)
    except Exception as exc:
        logger.exception(str(exc))
        logger.error("Something when wrong while sending Email.")


def send_decline_group_access_failed(destination, request_id, error):
    """ method to send decline group access failed """
    try:
        body = helpers.generateStringFromTemplate(
            "declineGroupAccessFailed.html", request_id=request_id, error=error
        )

        subject = subject = "Declined Failed Request " + request_id
        general.email_via_smtp(destination, subject, body)
    except Exception as exc:
        logger.exception(str(exc))
        logger.error("Something when wrong while sending Email.")


def send_mail_for_request_resolve(auth_user, access_type, request_id):
    """ method to send mail for request resolve """
    destination = [auth_user.email]
    subject = USER_REQUEST_RESOLVE_SUBJECT.format(request_id)
    body = helpers.generateStringFromTemplate(
        filename="requestResolvedEmail.html",
        user=auth_user.email,
        request_id=request_id,
        access_type=access_type,
    )
    general.email_via_smtp(destination, subject, body)
    logger.debug("Email sent for %s to %s ", subject, str(destination))
