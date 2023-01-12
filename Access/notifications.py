from bootprocess import general
from Access import helpers
from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS
import logging
logger = logging.getLogger(__name__)

NEW_GROUP_EMAIL_SUBJECT = "Request for creation of new group from:"

def send_new_group_create_notification(auth_user, date_time, new_group, member_list):
    subject = NEW_GROUP_EMAIL_SUBJECT + auth_user.email + " -- " + date_time
    body = helpers.generateStringFromTemplate(filename="groupCreationEmailBody.html",
                            user = str(auth_user.user),
                            first_name=auth_user.first_name,
                            last_name = auth_user.last_name,
                            email = auth_user.email,
                            groupName = new_group.name,
                            memberList = generateGroupMemberTable(member_list),
                            reason = new_group.description,
                            needsAccessApprove = new_group.needsAccessApprove
    )
    general.emailSES(MAIL_APPROVER_GROUPS, subject, body)
    logger.debug("Email sent for " + subject + " to " + str(MAIL_APPROVER_GROUPS))


def generateGroupMemberTable(memberList):
    if len(memberList) <= 0:
        return "No members are being added initially"
    return helpers.generateStringFromTemplate("listToTable.html", memberList=memberList)
