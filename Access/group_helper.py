from Access.models import User, GroupV2, MembershipV2, Role, GroupAccessMapping
from Access import email_helper, helpers
import datetime
import logging
from bootprocess import general
from Access import views_helper
import threading

from BrowserStackAutomation.settings import MAIL_APPROVER_GROUPS

logger = logging.getLogger(__name__)


def createGroup(request):
    try:
        data = request.POST
        data = dict(data.lists())
        newGroupName = (data["newGroupName"][0]).lower()
        # Group name has to be unique.
        existing_groups = GroupV2.objects.filter(name=newGroupName).filter(
            status__in=["approved", "pending"]
        )
        if len(existing_groups):
            # the group name is not unique.
            context = {}
            context["error"] = {
                "error_msg": "Invalid Group Name",
                "msg": "A group with name "
                + newGroupName
                + " already exists. Please choose a new name.",
            }
            return context

        base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        group_id = newGroupName + "-group-" + base_datetime_prefix

        needsAccessApprove = True
        if (
            not "requiresAccessApprove" in data
            or data["requiresAccessApprove"][0] != "true"
        ):
            needsAccessApprove = False

        group = GroupV2.objects.create(
            name=newGroupName,
            group_id=group_id,
            requester=request.user.user,
            description=data["newGroupReason"][0],
            needsAccessApprove=needsAccessApprove,
        )

        membership_id = (
            str(request.user.user.user.username)
            + "-"
            + newGroupName
            + "-membership-"
            + base_datetime_prefix
        )
        MembershipV2.objects.create(
            membership_id=membership_id,
            user=request.user.user,
            group=group,
            is_owner=True,
            requested_by=request.user.user,
            reason="Group Owner. Added as initial group member by requester.",
        )

        if "selectedUserList" in data:
            initialMembers = list(map(str, data["selectedUserList"]))
            for memberEmail in initialMembers:
                user = User.objects.filter(email=memberEmail)
                if len(user):
                    user = user[0]
                    membership_id = (
                        str(user.user.username)
                        + "-"
                        + newGroupName
                        + "-membership-"
                        + base_datetime_prefix
                    )
                    MembershipV2.objects.create(
                        membership_id=membership_id,
                        user=user,
                        group=group,
                        requested_by=request.user.user,
                        reason="Added as initial group member by requester.",
                    )
        else:
            initialMembers = [request.user.email]

        # Create a email for it.
        subject = (
            "Request for creation of new group from "
            + request.user.email
            + " -- "
            + base_datetime_prefix
        )
        body = email_helper.generateEmail(
            generateNewGroupCreationEmailBody(
                request,
                group_id,
                newGroupName,
                initialMembers,
                data["newGroupReason"][0],
                needsAccessApprove,
            )
        )

        # Send the email to the approvers.
        # TODO remove email references
        general.emailSES(MAIL_APPROVER_GROUPS, subject, body)
        logger.debug("Email sent for " + subject + " to " + str(MAIL_APPROVER_GROUPS))

        # Ack the user.
        context = {}
        context["status"] = {
            "title": "New Group Request submitted",
            "msg": "A request for New Group with name "
            + newGroupName
            + " has been submitted for approval. You will be notified for any changes in request status.",
        }
        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Create New Group request.")
        context = {}
        context["error"] = {
            "error_msg": "Internal Error",
            "msg": "Error Occured while loading the page. Please contact admin",
        }
        return context

def getGroupAccessList(request, groupName):
    try:
        context = {}
        group = GroupV2.objects.filter(name=groupName).filter(status='Approved')
        #check if the groupName is valid.
        if len(group) == 0:
            #there does not exist no such group.
            logger.debug("groupAccessList-- url received a bad group name request-"+request.user.username)
            context = {}
            context['error'] = {'title':'Invalid Group','msg':'There is no group named '+groupName+'. Please contact admin for any queries.'}
            return context

        group = group[0]
        groupMembers = MembershipV2.objects.filter(group=group).filter(status="Approved")
        
        if not requesterIsOwner(request, groupMembers):
            raise Exception("Permission denied, requester is non owner")
        # updating owner
        if request.POST:
            context["notification"] = updateOwner(request, groupName,group, context)
            # # if request.user.user.email not in ownersEmail and not request.user.is_superuser:
            # #     raise Exception("Permission denied, requester is non owner")
            # if not requesterIsOwner(request, groupMembers):
            #     raise Exception("Permission denied, requester is non owner")

            # logger.debug("updating owners for group "+ groupName+ " requested by "+ request.user.username)
            # data=request.POST
            # data=dict(data.lists())
            # if "owners" not in data:
            #     data["owners"] = []

            # destination = [request.user.user.email]
            # # we will only get data["owners"] as owners who are checked in UI(exluding disabled checkbox owner who requested the change)
            # for membership_obj in MembershipV2.objects.filter(group=group,status='Approved').exclude(user=request.user.user):
            #     if membership_obj.user.email in data["owners"]:
            #         membership_obj.is_owner = True
            #         destination.append(membership_obj.user.email)
            #     else:
            #         membership_obj.is_owner = False
            #     membership_obj.save()

            # logger.debug("Owners changed to "+", ".join(destination))
            # context["notification"] = "Owner's updated"
            # subject = "Enigma Group '"+groupName+"' owners changed"
            # body= "\nGroup Name :- {} \nupdated owners :- {} \nupdated by :- {}".format(groupName,", ".join(destination),request.user.user.email)
            # destination.extend(MAIL_APPROVER_GROUPS)
            # general.emailSES(destination,subject,body)
        
        groupMembers = getGroupMembers(groupMembers)
        
        context["userList"] = groupMembers
        context["groupName"] = groupName

        groupMappings = GroupAccessMapping.objects.filter(group=group, status__in=["Approved", "Pending", "Declined", "SecondaryPending"])
        accessV2s = [(groupMapping.access, groupMapping.request_id, groupMapping.status) for groupMapping in groupMappings]

        allow_revoke = False
        if helpers.check_user_permissions(request.user, "ALLOW_USER_OFFBOARD") or check_user_is_group_owner(request.user, group):
            allow_revoke = True
        context["allowRevoke"] = allow_revoke
        
        if accessV2s:
            split_details = []
            access_details = list(map(helpers.getAccessDetails, [access[0] for access in accessV2s]))
            for idx,each_access in enumerate(access_details):
                each_access["request_id"] = accessV2s[idx][1]
                each_access["status"] = accessV2s[idx][2]
                split_details.append(each_access)
            context["genericAccesses"] = split_details
        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Group Access List request.")
        context = {}
        context['error'] = {'error_msg': 'Internal Error', 'msg': "Error Occured while loading the page. Please contact admin, "+str(e)}
        return context

def updateOwner(request, groupName, group, context):
    logger.debug("updating owners for group "+ groupName+ " requested by "+ request.user.username)
    data=request.POST
    data=dict(data.lists())
    
    if "owners" not in data:
        data["owners"] = []
    destination = [request.user.user.email]

    # we will only get data["owners"] as owners who are checked in UI(exluding disabled checkbox owner who requested the change)
    for membership_obj in MembershipV2.objects.filter(group=group,status='Approved').exclude(user=request.user.user):
        if membership_obj.user.email in data["owners"]:
            membership_obj.is_owner = True
            destination.append(membership_obj.user.email)
        else:
            membership_obj.is_owner = False
        membership_obj.save()

    logger.debug("Owners changed to "+", ".join(destination))
    subject = "Enigma Group '"+groupName+"' owners changed"
    body= "\nGroup Name :- {} \nupdated owners :- {} \nupdated by :- {}".format(groupName,", ".join(destination),request.user.user.email)
    destination.extend(MAIL_APPROVER_GROUPS)
    general.emailSES(destination,subject,body)
    context["notification"] = "Owner's updated"

def requesterIsOwner(request,groupMembers):
    ownersEmail = [member.user.email for member in groupMembers.filter(is_owner = True)]
    print(ownersEmail)
    is_approver = len(User.objects.filter(role=Role.objects.get(label='TEAMS:ACCESSAPPROVE'),state=1, email=request.user.user.email)) > 0
    
    if request.user.user.email not in ownersEmail and not (request.user.is_superuser or request.user.user.is_ops or is_approver):
        return False
    return True

def getGroupMembers(groupMembers):
    return [{"name":member.user.name,"email":member.user.email,"is_owner":member.is_owner,"current_state":member.user.current_state(), "membership_id":member.membership_id} for member in groupMembers]

def check_user_is_group_owner(user_name, group):
    user = User.objects.get(user__username=user_name)
    try:
        return MembershipV2.objects.get(user=user, status="Approved", group__name=group.name).is_owner
    except:
        return False

def approveNewGroupRequest(request, group_id):
    try:
        try:
            groupObject = GroupV2.objects.get(group_id=group_id, status='Pending')
        except Exception as e:
            logger.error("Error in approveNewGroup request, Not found OR Invalid request type")
            json_response = {}
            json_response['error'] = "Error request not found OR Invalid request type"
            return json_response

        if groupObject.status in ['Declined','Approved','Processing','Revoked']:
            logger.warning("An Already Approved/Declined/Processing Request was accessed by - "+request.user.username)
            json_response = {}
            json_response['error'] = 'The Request ('+group_id+') is already Processed By : '+groupObject.approver.user.username
            return json_response
        elif request.user.username == groupObject.requester.user.username:
            # Approving self request
            context = {}
            context["error"] = "You cannot approve your own request. Please ask other admins to do that"
            return context
        else:
            json_response = {}
            json_response['msg'] = 'The Request ('+group_id+') is now being processed'

            groupObject.approver = request.user.user
            groupObject.status = 'Approved'
            groupObject.save()
            
            MembershipV2.objects.filter(group=groupObject, status="Pending").update(status="Approved", approver=request.user.user)
            initial_members = list(MembershipV2.objects.filter(group=groupObject).values_list("user__user__username", flat=True))

            subject = "New Group Created ("+groupObject.name+")"
            body = "New group with name "+groupObject.name+" has been created with owner being "+groupObject.requester.user.username+"<br>"
            if initial_members:
                body += "The following members have been added to this team<br>"
                body += generateGroupMemberTable(initial_members)
            body = email_helper.generateEmail(body)
            destination = []
            destination += MAIL_APPROVER_GROUPS[:]
            destination.append(groupObject.requester.email)
            # TODO send a mail to initial members
            logger.debug(group_id+" -- Approved email sent to - "+str(destination))
            general.emailSES(destination,subject,body)

            logger.debug("Approved group creation for - "+group_id+" - Approver="+request.user.username)
            if initial_members:
                logger.debug("Members added to group - "+group_id+" ="+", ".join(initial_members))
            return json_response
    except Exception as e:
        groupObject = GroupV2.objects.filter(group_id=group_id, status='Approved')
        if len(groupObject):
            groupObject = groupObject[0]
            groupObject.status = "Pending"
            groupObject.save()
            MembershipV2.objects.filter(group=groupObject).update(status="Pending", approver=None)
        logger.exception(e)
        logger.error("Error in Approving New Group request.")
        context = {}
        context['error'] = "Error Occured while Approving group creation. Please contact admin - "+str(e)
        return context    

def addUserToGroup(request, groupName):
    try:
        if request.POST:
            data = request.POST
            data = dict(data.lists())
            group = GroupV2.objects.filter(name=data['groupName'][0]).filter(status='Approved')[0]

            PrimaryApprover , otherApprover = helpers.getApprovers()
            subject='Request for addition of new members to group ('+ data['groupName'][0] +')'
            destination=MAIL_APPROVER_GROUPS[:]
            subject += "["+PrimaryApprover+"]"

            groupMembers = MembershipV2.objects.filter(group=group).filter(status__in=["Approved", "Pending"]).only('user')

            ownersEmail = [member.user.email for member in groupMembers.filter(is_owner = True)]
            requesterEmail = request.user.user.email
            isRequesterAdmin = request.user.is_superuser
            isRequesterOwner = requesterEmail in ownersEmail
            groupMembersEmail = [member.user.email for member in groupMembers]
            groupAccessMappings = GroupAccessMapping.objects.filter(group=group, status="Approved")
            groupAccessV2s = [(groupMapping.access, groupMapping.request_id) for groupMapping in groupAccessMappings]
            group_has_github = helpers.check_group_has_github(groupAccessV2s)

            if not (isRequesterOwner or isRequesterAdmin):
                raise Exception("Permission denied, requester is non owner")

            for userEmail in data['selectedUserList']:
                if userEmail in groupMembersEmail:
                    context = {}
                    context['error'] = {'error_msg': 'Duplicate Request', 'msg': "User " + userEmail + " is already added to group/or pending approval for group addition"}
                    return context

                if userEmail not in groupMembersEmail:
                    user = User.objects.filter(email=userEmail)[0]
                    if helpers.check_group_has_ssh(groupAccessV2s) and user.ssh_public_key == None:
                        context = {}
                        context['error'] = {'error_msg':'Request Not Submitted', 'msg': 'The user has not added a SSH key in enigma and hence can not add user to this group as this group has a SSH request. Please ask the user to add a ssh key and then try adding the user again to the group.'}
                        return context

                    membership_id = user.name+'-'+str(group)+'-membership-'+datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    member = MembershipV2.objects.create(group=group,user=user,reason=data['memberReason'][0],membership_id=membership_id,requested_by=request.user.user)

                    if not group.needsAccessApprove and isRequesterOwner:
                        json_response = {}
                        json_response['accessStatus'] = {'msg': 'The Request ('+membership_id+') is now being processed', 'desc': 'A email will be sent after the requested access are granted'}
                        member.approver = request.user.user
                        member.status = 'Approved'

                        userMappingsList = views_helper.generateUserMappings(user, group, member)
                        member.save()
                        group_name = member.group.name
                        accessAcceptThread = threading.Thread(target=views_helper.executeGroupAccess, args=(request, group_name, userMappingsList))
                        accessAcceptThread.start()

                        logger.debug("Process has been started for the Approval of request - " + membership_id + " - Approver=" + request.user.username)

                        return json_response
                    else:

                        body = email_helper.generateEmail(generateUserAddToGroupEmailBody(membership_id,userEmail, PrimaryApprover, otherApprover, str(request.user),data['groupName'][0],request.META['HTTP_HOST'],data['memberReason'][0]))
                        general.emailSES(destination,subject,body)

            context = {}
            context['status'] = {'title':'Request Submitted', 'msg': 'Once Approved the newly added members will be granted the same permissions as the group'}
            return context

        context = {}
        group = GroupV2.objects.filter(name=groupName).filter(status='Approved')
        #check if the groupName is valid.
        if len(group) == 0:
            #there does not exist no such group.
            logger.debug("addUserToGroup-- url received a bad group name requester-"+request.user.username)
            context = {}
            context['status'] = {'title':'Invalid Group','msg':'There is no group named '+groupName+'. Please contact admin for any queries.'}
            return context
        group = group[0]
        groupMembers = MembershipV2.objects.filter(group=group).filter(status="Approved").only('user')
        ownersEmail = [member.user.email for member in groupMembers.filter(is_owner = True)]
        if request.user.user.email not in ownersEmail and not request.user.is_superuser:
            raise Exception("Permission denied, you're not owner of this group")
        groupMembers = [member.user for member in groupMembers]
        context['groupMembers'] = groupMembers
        context['groupName'] = groupName
        return context
    except Exception as e:
        logger.exception(e)
        logger.error("Error in Add New User to Group request.")
        context = {}
        context['error'] = {'error_msg': 'Internal Error', 'msg': "Error Occured while loading the page. Please contact admin, " + str(e)}
        return context

def generateUserAddToGroupEmailBody(requestId, userEmail, PrimaryApprover, otherApprover, requester, groupName, http_host, reason):
    ret = """<center><h1> Access Request </h1></center>
    <h4>Primary Approver: <h4>"""+PrimaryApprover+""", <h4>Other:</h4>"""+otherApprover+"""
    <br><br>
    <b>"""+requester+"""</b> has requested to add <b>"""+ userEmail +"""</b> to his group <b>("""+groupName+""")</b><br>
    <br>
    Reason: """+reason+"""
    <br>
    <center>
    <a href='https://enigma.browserstack.com/access/pendingRequests' class="button button2" style="color:white;">Go to access-approve Dashboard</a>
    </center>"""
    return ret

def generateNewGroupCreationEmailBody(
    request, requestId, groupName, memberList, reason, needsAccessApprove
):
    ret = (
        """<center><h1> New Group Request from """
        + str(request.user.user)
        + """ </h1></center>
    <br>
    <b>"""
        + request.user.first_name
        + """ """
        + request.user.last_name
        + """</b>("""
        + request.user.email
        + """) has requested for creation of new group with name <b>"""
        + str(groupName)
        + """</b>
    <br><br>
    Following members are requested for being added to the group."""
    )
    ret += (
        generateGroupMemberTable(memberList)
        + """
    <br>
    Reason : """
        + reason
        + """
    <br>"""
    )

    if needsAccessApprove:
        ret += "Further addition of members <b>will</b> require premission from access_approve"
    else:
        ret += "Further addition of members <b>will not</b> require premission from access_approve"

    ret += """<center>
    <a href='https://enigma.browserstack.com/access/pendingRequests' class="button button2" style="color:white;">Go to access-approve Dashboard</a>
    </center>"""
    return ret


def generateGroupMemberTable(memberList):
    if len(memberList) <= 0:
        return "No members are being added initially"
    ret = """<table>
      <tr>
        <th>Member Email</th>
      </tr>"""
    for member in memberList:
        ret += (
            """
        <tr>
        <td>"""
            + member
            + """</td>
        </tr>"""
        )
    ret += """</table>"""
    return ret
