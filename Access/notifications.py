from bootprocess import general
from Access import helpers
from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS
import logging

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


def send_new_group_create_notification(auth_user, date_time, new_group, member_list):
    subject = NEW_GROUP_EMAIL_SUBJECT + auth_user.email + " -- " + date_time
    body = helpers.generateStringFromTemplate(
        filename="groupCreationEmailBody.html",
        user=str(auth_user.user),
        first_name=auth_user.first_name,
        last_name=auth_user.last_name,
        email=auth_user.email,
        groupName=new_group.name,
        memberList=generateGroupMemberTable(member_list),
        reason=new_group.description,
        needsAccessApprove=new_group.needsAccessApprove,
    )
    general.emailSES(MAIL_APPROVER_GROUPS, subject, body)
    logger.debug("Email sent for " + subject + " to " + str(MAIL_APPROVER_GROUPS))


def send_new_group_approved_notification(group, group_id, initial_member_names):
    subject = NEW_GROUP_APPROVED_SUBJECT.format(group.name)
    body = NEW_GROUP_APPROVED_BODY.format(group.name, group.requester.user.username)
    if initial_member_names:
        body += NEW_MEMBERS_ADDED_MESSAGE
        body += generateGroupMemberTable(initial_member_names)
    body = helpers.generateStringFromTemplate(filename="email.html", emailBody=body)
    destination = []
    destination += MAIL_APPROVER_GROUPS[:]
    destination.append(group.requester.email)
    # TODO send a mail to initial members
    logger.debug(group_id + " -- Approved email sent to - " + str(destination))
    general.emailSES(destination, subject, body)


def send_membership_accepted_notification(user, group, membership):
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
    general.emailSES(destination, subject, body)


def send_mulitple_membership_accepted_notification(user_names, group, membership):
    subject = MEMBERSHIP_ACCEPTED_SUBJECT.format(user_names, group.name)
    body = helpers.generateStringFromTemplate(
        filename="membershipAcceptedEmailBody.html",
        user_name=",".join(user_names),
        group_name=group.name,
        approver=membership.approver.name,
    )
    destination = []
    destination.append(membership.requested_by.email)
    destination = destination + user_names
    general.emailSES(destination, subject, body)


def generateGroupMemberTable(memberList):
    if len(memberList) <= 0:
        return "No members are being added initially"
    return helpers.generateStringFromTemplate("listToTable.html", memberList=memberList)


def send_group_owners_update_mail(destination, group_name, updated_by):
    try:
        subject = "Enigma Group '" + group_name + "' owners changed"
        body = "\nGroup Name :- {} \nupdated owners :- {} \nupdated by :- {}".format(
            group_name, ", ".join(destination), updated_by
        )

        general.emailSES(destination, subject, body)
    except Exception as e:
        logger.exception(str(e))
        logger.error("Something when wrong while sending Email.")


def send_group_access_add_email(
    destination, group_name, requester, request_id, member_list
):
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
    general.emailSES(destination, subject, body)
    return ""


def send_revoke_failure_mail(
    targets, request_id, revoker_email, retries, message, access_tag=None
):
    try:
        subject = "Celery Revoke Failed for the request: {}".format(request_id)
        body = helpers.generateStringFromTemplate(
            "celery_revoke_failure_email.html",
            request_id=request_id,
            revoker_email=revoker_email,
            retries=retries,
            message=message,
            access_tag=access_tag,
        )

        general.emailSES(targets, subject, body)
    except Exception as e:
        logger.error("Something when wrong while sending membership revoke email")
        logger.exception(str(e))


def send_mail_for_request_decline(
    request, description, request_id, reason, access_type
):
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
    general.emailSES(destination, subject, body)
    logger.debug("Email sent for " + subject + " to " + str(destination))


def send_mail_for_request_granted_failure(user, approver, access_type, request_id):
    destination = [user.email]
    destination.extend(approver.email)
    subject = USER_ACCESS_REQUEST_GRANT_FAILURE_SUBJECT.format(
        str(user.email), access_type.upper(), request_id
    )
    body = "Request by %s having Request ID %s could not be approved." % (
        str(user.email),
        request_id,
    )
    general.emailSES(destination, subject, body)
    logger.debug("Email sent for " + subject + " to " + str(destination))


def send_mail_for_member_approval(userEmail, requester, group_name, reason):
    primary_approver, otherApprover = helpers.get_approvers()
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
            userEmail,
            primary_approver,
            otherApprover,
            requester,
            group_name,
            reason,
        ),
    )
    general.emailSES(destination, subject, body)


def generate_user_add_to_group_email_body(
    user_email, primary_approver, other_approver, requester, group_name, reason
):
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
    destination = [destination]
    subject = str("Access Grant Failed - ") + access_type.upper()
    body = ACCESS_GRANT_FAILED_MESSAGE.format(user_email, request_id)
    body = body + "Failure Reason - " + message
    general.emailSES(destination, subject, body)


def send_group_access_declined(
    destination, group_name, requester, decliner, request_id, declined_access, reason
):
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
    general.emailSES(destination, subject, body)


def send_accept_group_access_failed(destination, request_id, error):
    try:
        body = helpers.generateStringFromTemplate(
            "acceptGroupAccessFailed.html", request_id=request_id, error=error
        )

        subject = subject = "Failed Request " + request_id
        general.emailSES(destination, subject, body)
    except Exception as e:
        logger.exception(str(e))
        logger.error("Something when wrong while sending Email.")


def send_decline_group_access_failed(destination, request_id, error):
    try:
        body = helpers.generateStringFromTemplate(
            "declineGroupAccessFailed.html", request_id=request_id, error=error
        )

        subject = subject = "Declined Failed Request " + request_id
        general.emailSES(destination, subject, body)
    except Exception as e:
        logger.exception(str(e))
        logger.error("Something when wrong while sending Email.")
