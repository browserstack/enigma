from django.contrib.auth.models import User as user
from django.db import models, transaction
from BrowserStackAutomation.settings import USER_STATUS_CHOICES, PERMISSION_CONSTANTS
import datetime


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

    def isPrimaryApproverForModule(self, accessModule, accessLabel=None):
        module_permissions = accessModule.fetch_approver_permissions(accessLabel)
        return self.has_permission(module_permissions["1"])

    def isSecondaryApproverForModule(self, accessModule, accessLabel=None):
        module_permissions = accessModule.fetch_approver_permissions(accessLabel)
        return "2" in module_permissions and self.has_permission(
            module_permissions["2"]
        )

    def isAnApproverForModule(
        self, accessModule, accessLabel=None, approverType="Primary"
    ):
        if approverType == "Secondary":
            return self.isSecondaryApproverForModule(accessModule, accessLabel)

        return self.isPrimaryApproverForModule(accessModule, accessLabel)

    def getPendingApprovals(self, all_access_modules):
        return self.__query_pending_accesses()

    def getPendingApprovalsCount(self, all_access_modules):
        pendingCount = 0
        if self.has_permission(PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]):
            pendingCount += GroupV2.getPendingMemberships().count()
            pendingCount += len(GroupV2.getPendingCreation())

        for each_access_module in all_access_modules:
            all_requests = each_access_module.get_pending_access_objects(self)
            pendingCount += len(all_requests["individual_requests"])
            pendingCount += len(all_requests["group_requests"])

        return pendingCount

    def getFailedGrantsCount(self):
        return (
            UserAccessMapping.objects.filter(status__in=["grantfailed"]).count()
            if self.isAdminOrOps()
            else 0
        )

    def getFailedRevokesCount(self):
        return (
            UserAccessMapping.objects.filter(status__in=["revokefailed"]).count()
            if self.isAdminOrOps()
            else 0
        )

    def getOwnedGroups(self):
        if self.isAdminOrOps():
            return GroupV2.objects.all().filter(status="Approved")

        groupOwnerMembership = MembershipV2.objects.filter(
            is_owner=True, user=currentUser
        )
        return [membership_obj.group for membership_obj in groupOwnerMembership]

    def isAdminOrOps(self):
        return self.is_ops or self.user.is_superuser

    def get_all_memberships(self):
        return self.membership_user.all()

    def is_allowed_admin_actions_on_group(self, group):
        return (
            group.member_is_owner(self)
            or self.user.is_superuser
            or self.is_ops
            or self.has_permission(PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"])
        )

    def is_allowed_to_offboard_user_from_group(self, group):
        return group.member_is_owner(self) or self.has_permission("ALLOW_USER_OFFBOARD")
    
    def create_new_identity(self, access_tag="", identity=""):
        return self.module_identity.create(access_tag=access_tag, identity=identity)

    def get_active_identity(self, access_tag):
        return self.module_identity.filter(
            access_tag=access_tag, status="Active"
        ).first()

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

    def deactivate(self):
        self.status = "Revoked"
        self.save()

    def approve(self, approver):
        self.status = "Approved"
        self.approver = approver
        self.save()

    def unapprove(self):
        self.status = "Pending"
        self.approver = None
        self.save()

    def get_status(self):
        return self.status

    def is_self_approval(self, approver):
        return self.requested_by == approver

    def is_already_processed(self):
        return self.status in ["Declined", "Approved", "Processing", "Revoked"]

    @staticmethod
    def approve_membership(membership_id, approver):
        membership = MembershipV2.objects.get(membership_id=membership_id)
        membership.approve(approver=approver)

    @staticmethod
    def get_membership(membership_id):
        return MembershipV2.objects.get(membership_id=membership_id)

    def get_owners(self):
        return self.membership_group.filter(is_owner=True)
    
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
    def group_exists(group_name):
        if len(
            GroupV2.objects.filter(name=group_name).filter(
                status__in=["Approved", "Pending"]
            )
        ):
            return True
        return False

    @staticmethod
    def create(
        name="", requester=None, description="", needsAccessApprove=True, date_time=""
    ):
        return GroupV2.objects.create(
            name=name,
            group_id=name + "-group-" + date_time,
            requester=requester,
            description=description,
            needsAccessApprove=needsAccessApprove,
        )

    def add_member(
        self, user=None, is_owner=False, requested_by=None, reason="", date_time=""
    ):
        membership_id = (
            str(user.user.username) + "-" + self.name + "-membership-" + date_time
        )
        return self.membership_group.create(
            membership_id=membership_id,
            user=user,
            is_owner=is_owner,
            requested_by=requested_by,
            reason=reason,
        )

    def add_members(self, users=None, requested_by=None, reason="", date_time=""):
        if users:
            for usr in users:
                self.add_member(
                    user=usr,
                    requested_by=requested_by,
                    reason=reason,
                    date_time=date_time,
                )

    def getPendingMemberships():
        return MembershipV2.objects.filter(status="Pending", group__status="Approved")

    @staticmethod
    def getPendingCreation():
        new_group_pending = GroupV2.objects.filter(status="Pending")
        new_group_pending_data = []
        for new_group in new_group_pending:
            initial_members = ", ".join(
                list(
                    new_group.membership_group.values_list(
                        "user__user__username", flat=True
                    )
                )
            )
            new_group_pending_data.append(
                {"groupRequest": new_group, "initialMembers": initial_members}
            )
        return new_group_pending_data

    @staticmethod
    def get_pending_group(group_id):
        try:
            return GroupV2.objects.get(group_id=group_id, status="Pending")
        except GroupV2.DoesNotExist:
            return None

    @staticmethod
    def get_approved_group(group_id):
        try:
            return GroupV2.objects.get(group_id=group_id, status="Approved")
        except GroupV2.DoesNotExist:
            return None

    @staticmethod
    def get_active_group_by_name(group_name):
        try:
            return GroupV2.objects.get(name=group_name, status="Approved")
        except GroupV2.DoesNotExist:
            return None

    def approve_all_pending_users(self, approved_by):
        self.membership_group.filter(status="Pending").update(
            status="Approved", approver=approved_by
        )

    def get_all_members(self):
        group_members = self.membership_group.all()
        return group_members

    def member_is_owner(self, user):
        return self.membership_group.get(user=user).is_owner

    def get_active_accesses(self):
        return self.groupaccessmapping_set.filter(
            status__in=["Approved", "Pending", "Declined", "SecondaryPending"]
        )

    def is_self_approval(self, approver):
        return self.requester == approver

    def approve(self, approved_by):
        self.approver = approved_by
        self.status = "Approved"
        self.save()

    def unapprove(self):
        self.approver = None
        self.status = "Pending"
        self.save()

    def unapprove_memberships(self):
        self.membership_group.filter(status="Approved").update(
            status="Pending", approver=None
        )

    def is_owner(self, email):
        return self.membership_group.filter(is_owner=True).filter(user__email = email).first() != None

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
    meta_data = models.JSONField(default=dict, blank=True, null=True)

    user_identity = models.ForeignKey(
        "UserIdentity",
        null=True,
        blank=True,
        related_name="user_access_mapping",
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
        access_request_data["accessReason"] = self.request_reason
        access_request_data["requested_on"] = self.requested_on

        access_request_data["accessType"] = access_module.access_desc()
        access_request_data["accessCategory"] = access_module.combine_labels_desc(
            access_labels
        )
        access_request_data["accessMeta"] = access_module.combine_labels_meta(
            access_labels
        )
        access_request_data["status"] = self.status
        access_request_data["revokeOwner"] = ",".join(access_module.revoke_owner())
        access_request_data["grantOwner"] = ",".join(access_module.grant_owner())

        return access_request_data

    def updateMetaData(self, key, data):
        with transaction.atomic():
            mapping = UserAccessMapping.objects.select_for_update().get(
                request_id=self.request_id
            )
            mapping.meta_data[key] = data
            mapping.save()
        return True

    def is_approved(self):
        return self.status == "Approved"


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
        access_request_data["accessReason"] = self.request_reason
        access_request_data["requested_on"] = self.requested_on

        access_request_data["accessType"] = access_module.access_desc()
        access_request_data["accessCategory"] = access_module.combine_labels_desc(
            access_labels
        )
        access_request_data["accessMeta"] = access_module.combine_labels_meta(
            access_labels
        )
        access_request_data["status"] = self.status
        access_request_data["revokeOwner"] = ",".join(access_module.revoke_owner())
        access_request_data["grantOwner"] = ",".join(access_module.grant_owner())

        return access_request_data


class AccessV2(models.Model):
    access_tag = models.CharField(max_length=255)
    access_label = models.JSONField(default=dict)
    is_auto_approved = models.BooleanField(null=False, default=False)

    def __str__(self):
        try:
            details_arr = []
            for data in list(self.access_label.values()):
                try:
                    details_arr.append(data.decode("utf-8"))
                except Exception:
                    details_arr.append(data)
            return self.access_tag + " - " + ", ".join(details_arr)
        except Exception:
            return self.access_tag
    
    @staticmethod
    def get(access_type, access_label):
        try:
            return AccessV2.objects.get(access_tag=access_type, access_label=access_label)
        except:
            return None
        
class UserIdentity(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "access_tag", "status"],
                condition=models.Q(status="Active"),
                name="one_active_identity_per_access_module_per_user",
            )
        ]

    access_tag = models.CharField(max_length=255)

    user = models.ForeignKey(
        "User",
        null=False,
        blank=False,
        related_name="module_identity",
        on_delete=models.PROTECT,
    )
    identity = models.JSONField(default=dict)

    STATUS_CHOICES = (
        ("Active", "active"),
        ("Inactive", "inactive"),
    )

    status = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        choices=STATUS_CHOICES,
        default="Active",
    )

    def deactivate(self):
        self.status = 0
        self.save()

    def get_active_access(self):
        return self.user_access_mapping.filter(
            status__in=["Approved", "Pending"], access__access_tag=self.access_tag
        )
    
    def get_active_access(self, access):
        return self.user_access_mapping.filter(access=access, status__in=["Approved", "Pending"])
    
    def access_exists(self, access):
        if self.get_active_access(access=access):
            return True
        return False

    def replicate_active_access_membership_for_module(
        self, existing_user_access_mapping
    ):
        new_user_access_mapping = []

        for i, user_access in enumerate(existing_user_access_mapping):
            base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
            request_id = (
                self.user.username
                + "-"
                + user_access.access_type
                + "-"
                + base_datetime_prefix
                + "-"
                + str(i)
            )
            access_status = user_access.status
            if user_access.status.lower() == "approved":
                access_status = "Processing"

            new_user_access_mapping.append(
                self.user_access_mapping.create(
                    request_id=request_id,
                    user=self,
                    access=user_access.access,
                    approver_1=user_access.approver_1,
                    approver_2=user_access.approver_2,
                    request_reason=user_access.request_reason,
                    access_type=user_access.access_type,
                    status=access_status,
                )
            )
            user_access.deactivate()
        return new_user_access_mapping

    def __str__(self):
        return "%s" % (self.identity)
