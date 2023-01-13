from django.contrib.auth.models import User as user
from django.db import models

from BrowserStackAutomation.settings import USER_STATUS_CHOICES, PERMISSION_CONSTANTS


class Permission(models.Model):
    """
    Permission to perform actions on enigma
    """

    label = models.CharField(max_length=255, null=False, blank=False, unique=True)

    def __str__(self):
        return "%s" % (self.label)


class Role(models.Model):
    """
    User role to attach permissions to perform actions on enigma; one user can have multiple roles
    Role is a group of permissions which can be associated with a group of users
    """

    label = models.CharField(max_length=255, null=False, blank=False, unique=True)
    permission = models.ManyToManyField(Permission)

    def __str__(self):
        return "%s" % (self.label)


class SshPublicKey(models.Model):
    """
    SSH Public keys for users
    """

    key = models.TextField(null=False, blank=False)

    STATUS_CHOICES = (("Active", "active"), ("Revoked", "revoked"))
    status = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        choices=STATUS_CHOICES,
        default="Active",
    )

    def __str__(self):
        return str(self.key)


# Create your models here.
class User(models.Model):
    """
    Represents an user belonging to the organistaion
    """

    user = models.OneToOneField(
        user, null=False, blank=False, on_delete=models.CASCADE, related_name="user"
    )
    gitusername = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=False)

    email = models.EmailField(null=True, blank=False)
    phone = models.IntegerField(null=True, blank=True)

    is_bot = models.BooleanField(null=False, blank=False, default=False)
    BOT_TYPES = (
        ("None", "none"),
        ("Github", "github"),
    )
    bot_type = models.CharField(
        max_length=100, null=False, blank=False, choices=BOT_TYPES, default="None"
    )

    alerts_enabled = models.BooleanField(null=False, blank=False, default=False)

    is_manager = models.BooleanField(null=False, blank=False, default=False)
    is_ops = models.BooleanField(null=False, blank=False, default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ssh_pub_key will be deprecated. Use ssh_public_key field
    ssh_pub_key = models.TextField(null=True, blank=True)
    ssh_public_key = models.ForeignKey(
        "SshPublicKey",
        related_name="user",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    avatar = models.TextField(null=True, blank=True)

    state = models.CharField(
        max_length=255, null=False, blank=False, choices=USER_STATUS_CHOICES, default=1
    )
    role = models.ManyToManyField(Role, blank=True)

    offbaord_date = models.DateTimeField(null=True, blank=True)
    revoker = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="user_revoker",
        on_delete=models.PROTECT,
    )

    @property
    def permissions(self):
        user_roles = self.role.all()
        user_permissions = [
            permission for role in user_roles for permission in role.permission.all()
        ]
        return user_permissions

    def has_permission(self, permission_label):
        all_permission_labels = [permission.label for permission in self.permissions]
        return permission_label in all_permission_labels

    def current_state(self):
        return dict(USER_STATUS_CHOICES).get(self.state)

    def change_state(self, final_state):
        user_states = dict(USER_STATUS_CHOICES)
        state_key = self.state
        for key in user_states:
            if user_states[key] == final_state:
                state_key = key
        self.state = state_key
        self.save()

    def isAnApprover(self, allApproverPermissions):
        permission_labels = [permission.label for permission in self.permissions]
        approver_permissions = allApproverPermissions
        return len(list(set(permission_labels) & set(approver_permissions))) > 0

    def isPrimaryApproverForModule(self, accessModule):
        module_permissions = {}
        try:
            module_permissions = accessModule.fetch_approver_permissions()
        except:
            module_permissions = {
                "1": PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]
            }
        return self.has_permission(module_permissions["1"])

    def isSecondaryApproverForModule(self, accessModule):
        module_permissions = {}
        try:
            module_permissions = accessModule.fetch_approver_permissions()
        except:
            return False
        return "2" in module_permissions and self.has_permission(module_permissions["2"])

    def getPendingApprovalsCount(self, all_access_modules):
        pendingCount = 0
        if self.has_permission(PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]):
            pendingCount += GroupV2.getPendingMemberships().count()
            pendingCount += GroupAccessMapping.objects.filter(status='Pending').count()
            pendingCount += len(GroupV2.getPendingCreation())

        for each_access_module in all_access_modules:
            access_tag = each_access_module.tag()
            if self.isPrimaryApproverForModule(each_access_module):
                pendingCount += UserAccessMapping.objects.filter(status='Pending', access__access_tag=access_tag).count()
            elif self.isSecondaryApproverForModule(each_access_module):
                pendingCount += UserAccessMapping.objects.filter(status='SecondaryPending', access__access_tag=access_tag).count()

        return pendingCount

    def getFailedGrantsCount(self):
        return UserAccessMapping.objects.filter(status__in=["grantfailed"]).count() if self.isAdminOrOps() else 0

    def getFailedRevokesCount(self):
        return UserAccessMapping.objects.filter(status__in=["revokefailed"]).count() if self.isAdminOrOps() else 0

    def getOwnedGroups(self):
        if self.isAdminOrOps():
            return GroupV2.objects.all().filter(status='Approved')

        groupOwnerMembership = MembershipV2.objects.filter(is_owner=True, user=currentUser)
        return [ membership_obj.group for membership_obj in groupOwnerMembership ]

    def isAdminOrOps(self):
        return self.is_ops or self.user.is_superuser

    def __str__(self):
        return "%s" % (self.user)


class MembershipV2(models.Model):
    """
    Membership of user in a GroupV2
    """

    membership_id = models.CharField(
        max_length=255, null=False, blank=False, unique=True
    )

    user = models.ForeignKey(
        "User",
        null=False,
        blank=False,
        related_name="membership_user",
        on_delete=models.PROTECT,
    )
    group = models.ForeignKey(
        "GroupV2",
        null=False,
        blank=False,
        related_name="membership_group",
        on_delete=models.PROTECT,
    )
    is_owner = models.BooleanField(null=False, blank=False, default=False)

    requested_by = models.ForeignKey(
        User,
        null=False,
        blank=False,
        related_name="membership_requester",
        on_delete=models.PROTECT,
    )
    requested_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    STATUS = (
        ("Pending", "pending"),
        ("Approved", "approved"),
        ("Declined", "declined"),
        ("Revoked", "revoked"),
    )
    status = models.CharField(
        max_length=255, null=False, blank=False, choices=STATUS, default="Pending"
    )

    reason = models.TextField(null=True, blank=True)

    approver = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="membership_approver",
        on_delete=models.PROTECT,
    )
    decline_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.group.name + "-" + self.user.email + "-" + self.status


class GroupV2(models.Model):
    """
    Model for Enigma Groups redefined.
    """

    group_id = models.CharField(max_length=255, null=False, blank=False, unique=True)
    requested_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=128, null=False, blank=False, unique=True)
    description = models.TextField(null=False, blank=False)

    requester = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="group_requester",
        on_delete=models.PROTECT,
    )

    STATUS = (
        ("Pending", "pending"),
        ("Approved", "approved"),
        ("Declined", "declined"),
        ("Deprecated", "deprecated"),
    )
    status = models.CharField(
        max_length=255, null=False, blank=False, choices=STATUS, default="Pending"
    )

    approver = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="group_approver",
        on_delete=models.PROTECT,
    )
    decline_reason = models.TextField(null=True, blank=True)
    needsAccessApprove = models.BooleanField(null=False, blank=False, default=True)

    @staticmethod
    def getPendingMemberships():
        return MembershipV2.objects.filter(status="Pending", group__status="Approved")

    @staticmethod
    def getPendingCreation():
        new_group_pending = GroupV2.objects.filter(status="Pending")
        new_group_pending_data = []
        for new_group in new_group_pending:
            initial_members = ", ".join(list(new_group.membership_group.values_list("user__user__username", flat=True)))
            new_group_pending_data.append({
                "groupRequest": new_group,
                "initialMembers": initial_members
            })
        return new_group_pending_data

    def __str__(self):
        return self.name


class UserAccessMapping(models.Model):
    """
    Model to map access to user. Requests are broken down
    into mappings which are sent for approval.
    """

    request_id = models.CharField(max_length=255, null=False, blank=False, unique=True)

    requested_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True)

    user = models.ForeignKey("User", null=False, blank=False, on_delete=models.PROTECT)

    request_reason = models.TextField(null=False, blank=False)

    approver_1 = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="approver_1",
        on_delete=models.PROTECT,
    )
    approver_2 = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="approver_2",
        on_delete=models.PROTECT,
    )

    access = models.ForeignKey(
        "AccessV2", null=False, blank=False, on_delete=models.PROTECT
    )

    STATUS_CHOICES = (
        ("Pending", "pending"),
        ("SecondaryPending", "secondarypending"),
        ("Processing", "processing"),
        ("Approved", "approved"),
        ("GrantFailed", "grantfailed"),
        ("Declined", "declined"),
        ("Offboarding", "offboarding"),
        ("ProcessingRevoke", "processingrevoke"),
        ("RevokeFailed", "revokefailed"),
        ("Revoked", "revoked"),
    )
    status = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    decline_reason = models.TextField(null=True, blank=True)

    TYPE_CHOICES = (("Individual", "individual"), ("Group", "group"))
    access_type = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        choices=TYPE_CHOICES,
        default="Individual",
    )
    revoker = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="user_access_revoker",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.request_id

    # Wrote the override version of save method in order to update the
    # "approved_on" field whenever the request is marked "Approved"
    def save(self, *args, **kwargs):
        super(UserAccessMapping, self).save(*args, **kwargs)
        # Consider only the first cycle of approval
        if self.status.lower() == "approved" and self.approved_on in [None, ""]:
            self.approved_on = self.updated_on
            super(UserAccessMapping, self).save(*args, **kwargs)

    def getAccessRequestDetails(self, access_module):
        access_request_data = {}
        access_tags = [self.access.access_tag]
        access_labels = [self.access.access_label]

        access_tag = access_tags[0]
        # code metadata
        access_request_data["access_tag"] = access_tag
        # ui metadata
        access_request_data["userEmail"] = self.user.email
        access_request_data["requestId"] = self.request_id
        access_request_data['accessReason'] = self.request_reason
        access_request_data['requested_on'] = self.requested_on

        access_request_data["accessType"] = access_module.access_desc()
        access_request_data["accessCategory"] = access_module.combine_labels_desc(access_labels)
        access_request_data["accessMeta"] = access_module.combine_labels_meta(access_labels)

        return access_request_data


class GroupAccessMapping(models.Model):
    """
    Model to map access to group. Requests are broken down
    into mappings which are sent for approval.
    """

    request_id = models.CharField(max_length=255, null=False, blank=False, unique=True)

    requested_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    group = models.ForeignKey(
        "GroupV2", null=False, blank=False, on_delete=models.PROTECT
    )

    requested_by = models.ForeignKey(
        "User",
        null=True,
        blank=False,
        related_name="g_requester",
        on_delete=models.PROTECT,
    )

    request_reason = models.TextField(null=False, blank=False)

    approver_1 = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="g_approver_1",
        on_delete=models.PROTECT,
    )
    approver_2 = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="g_approver_2",
        on_delete=models.PROTECT,
    )

    access = models.ForeignKey(
        "AccessV2", null=False, blank=False, on_delete=models.PROTECT
    )

    STATUS_CHOICES = (
        ("Pending", "pending"),
        ("SecondaryPending", "secondarypending"),
        ("Approved", "approved"),
        ("Declined", "declined"),
        ("Revoked", "revoked"),
        ("Inactive", "inactive"),
    )
    status = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    decline_reason = models.TextField(null=True, blank=True)

    revoker = models.ForeignKey(
        "User",
        null=True,
        blank=True,
        related_name="group_access_revoker",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.request_id

    def getAccessRequestDetails(self, access_module):
        access_request_data = {}
        access_tags = [self.access.access_tag]
        access_labels = [self.access.access_label]

        access_tag = access_tags[0]
        # code metadata
        access_request_data["access_tag"] = access_tag
        # ui metadata
        access_request_data["userEmail"] = self.requested_by.email
        access_request_data["groupName"] = self.group.name
        access_request_data["requestId"] = self.request_id
        access_request_data['accessReason'] = self.request_reason
        access_request_data['requested_on'] = self.requested_on

        access_request_data["accessType"] = access_module.access_desc()
        access_request_data["accessCategory"] = access_module.combine_labels_desc(access_labels)
        access_request_data["accessMeta"] = access_module.combine_labels_meta(access_labels)

        return access_request_data


class AccessV2(models.Model):
    access_tag = models.CharField(max_length=255)
    access_label = models.JSONField(default=dict)
    is_auto_approved = models.BooleanField(null=False, default=False)

    def __str__(self):
        try:
            if self.access_tag == "aws":
                label = self.access_label["data"]
                return "{}: Team- {} | Access: {} | Level: {} | Service: {} | Resource: {}".format(
                    self.access_tag,
                    label["team"],
                    label["awsAccessType"],
                    label["levelAccessType"],
                    label["awsService"],
                    label["awsResource"],
                )
            if self.access_tag == "other":
                return self.access_tag + " - " + self.access_label["request"]
            details_arr = []
            for data in list(self.access_label.values()):
                try:
                    details_arr.append(data.decode("utf-8"))
                except Exception:
                    details_arr.append(data)
            return self.access_tag + " - " + ", ".join(details_arr)
        except Exception:
            return self.access_tag
