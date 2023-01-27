from bootprocess import general
from Access import helpers
from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS
import logging

logger = logging.getLogger(__name__)

NEW_GROUP_EMAIL_SUBJECT = "Request for creation of new group from:"


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
    subject = "New Group Created (" + group.name + ")"
    body = (
        "New group with name "
        + group.name
        + " has been created with owner being "
        + group.requester.user.username
        + "<br>"
    )
    if initial_member_names:
        body += "The following members have been added to this team<br>"
        body += generateGroupMemberTable(initial_member_names)
    body = helpers.generateStringFromTemplate(
        filename="email.html", emailBody=body
    )
    destination = []
    destination += MAIL_APPROVER_GROUPS[:]
    destination.append(group.requester.email)
    # TODO send a mail to initial members
    logger.debug(group_id + " -- Approved email sent to - " + str(destination))
    general.emailSES(destination, subject, body)

def send_membership_accepted_notification(user, group, membership):
    subject = "Access approved for addition of " + user.name + " to group - " + group.name
    body = "Access approved for addition of " + user.name + " to group - " + group.name + " by " + membership.approver.name + ".<BR/>Automated accesses will be triggered shortly. Access grant mails will be sent to tool owners for manual access. Track your access status <a href='https://enigma.browserstack.com/access/showAccessHistory'>here</a>."
    destination = []
    destination.append(membership.requested_by.email)
    destination.append(user.email)
    general.emailSES(destination,subject,body)

def generateGroupMemberTable(memberList):
    if len(memberList) <= 0:
        return "No members are being added initially"
    return helpers.generateStringFromTemplate("listToTable.html", memberList=memberList)
