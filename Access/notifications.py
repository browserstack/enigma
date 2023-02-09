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
MEMBERSHIP_ACCEPTED_BODY = """Access approved for addition of {} to group - {} by {}.
                            <BR/>Automated accesses will be triggered shortly.
                            Access grant mails will be sent to tool owners for manual access.
                            Track your access status
                            <a href='https://enigma.browserstack.com/access/showAccessHistory'>
                            here
                            </a>."""

GROUP_ACCESS_ADDED_SUBJECT = "Group: {group_name}  new access added"


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
    body = MEMBERSHIP_ACCEPTED_BODY.format(
        user.name, group.name, membership.approver.name
    )
    destination = []
    destination.append(membership.requested_by.email)
    destination.append(user.email)
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
