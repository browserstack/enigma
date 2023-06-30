""" file containing models """
import datetime
import enum
import dataclasses
from django.contrib.auth.models import User as djangoUser
from django.db import models, transaction
from django.db.models.signals import post_save
from django.conf import settings
from enigma_automation.settings import PERMISSION_CONSTANTS


class StoredPassword(models.Model):
    """ model for stored password """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        editable=False
    )
    password = models.CharField(
        'Password hash',
        max_length=255,
        editable=False
    )
    date = models.DateTimeField(
        'Date',
        auto_now_add=True,
        editable=False
    )


class ApprovalType(enum.Enum):
    """ Enum for Approval type """
    PRIMARY = "Primary"
    SECONDARY = "Secondary"


class Permission(models.Model):
    """
    Permission to perform actions on enigma
    """

    label = models.CharField(max_length=255, null=False, blank=False, unique=True)

    def __str__(self):
        return f"{self.label}"


class Role(models.Model):
    """
    User role to attach permissions to perform actions on enigma; one user can have multiple roles
    Role is a group of permissions which can be associated with a group of users
    """

    label = models.CharField(max_length=255, null=False, blank=False, unique=True)
    permission = models.ManyToManyField(Permission)

    def __str__(self):
        return f"{self.label}"


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


class User(models.Model):
    """
    Represents a user belonging to the organisation
    """

    user = models.OneToOneField(
        djangoUser, null=False, blank=False, on_delete=models.CASCADE, related_name="user"
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

    USER_STATUS_CHOICES = [
        ("1", "active"),
        ("2", "offboarding"),
        ("3", "offboarded"),
    ]

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
        """ method to get users all permissions """
        user_roles = self.role.all()
        user_permissions = [
            permission for role in user_roles for permission in role.permission.all()
        ]
        return user_permissions

    def has_permission(self, permission_label):
        """ method to check if user has permission for permission label """
        all_permission_labels = [permission.label for permission in self.permissions]
        return permission_label in all_permission_labels

    def current_state(self):
        """ method to get users current state """
        return dict(self.USER_STATUS_CHOICES).get(self.state)

    def change_state(self, final_state):
        """ method to change users state """
        user_states = dict(self.USER_STATUS_CHOICES)
        state_key = self.state
        for key, state in user_states.items():
            if state == final_state:
                state_key = key
        self.state = state_key
        self.save()

    def is_an_approver(self, all_approver_permissions):
        """ method to check if user is an approver given all approver permissions """
        permission_labels = [permission.label for permission in self.permissions]
        approver_permissions = all_approver_permissions
        return len(list(set(permission_labels) & set(approver_permissions))) > 0

    def is_primary_approver_for_module(self, access_module, access_label=None):
        """ method to check if user is primary approver for access_module having access_label """
        module_permissions = access_module.fetch_approver_permissions(access_label)
        return self.has_permission(module_permissions["1"])

    def is_secondary_approver_for_module(self, access_module, access_label=None):
        """ method to check if user is secondary approver for access_module having access_label """
        module_permissions = access_module.fetch_approver_permissions(access_label)
        return "2" in module_permissions and self.has_permission(
            module_permissions["2"]
        )

    def is_an_approver_for_module(
        self, access_module, access_label=None, approver_type="Primary"
    ):
        """
        method to check if user is an approver for access module
        having access label and approver type
        """
        if approver_type == "Secondary":
            return self.is_secondary_approver_for_module(access_module, access_label)

        return self.is_primary_approver_for_module(access_module, access_label)

    def get_pending_approvals_count(self, all_access_modules):
        """ method to get pending approvals count for all access modules """
        pending_count = 0
        if self.has_permission(PERMISSION_CONSTANTS["DEFAULT_APPROVER_PERMISSION"]):
            pending_count += GroupV2.get_pending_memberships().count()
            pending_count += len(GroupV2.get_pending_creation())

        for _each_tag, each_access_module in all_access_modules.items():
            all_requests = each_access_module.get_pending_access_objects(self)
            pending_count += len(all_requests["individual_requests"])
            pending_count += len(all_requests["group_requests"])

        return pending_count

    def get_failed_grants_count(self):
        """ method to get failed grants count """
        return (
            UserAccessMapping.objects.filter(status__in=["GrantFailed"]).count()
            if self.is_admin_or_ops()
            else 0
        )

    def get_failed_revokes_count(self):
        """ method to get failed revokes count """
        return (
            UserAccessMapping.objects.filter(status__in=["RevokeFailed"]).count()
            if self.is_admin_or_ops()
            else 0
        )

    def get_owned_groups(self):
        """ method to get owned group of the user """
        if self.is_admin_or_ops():
            return GroupV2.objects.all().filter(status="Approved")

        group_owner_membership = MembershipV2.objects.filter(is_owner=True, user=self)
        return [membership_obj.group for membership_obj in group_owner_membership]

    def get_active_groups(self):
        """ method to get active groups """
        all_active_memberships = self.membership_user.filter(status="Approved")
        return [each_membership.group for each_membership in all_active_memberships]

    def is_admin_or_ops(self):
        """ method to check if user is admin or ops """
        return self.is_ops or self.user.is_superuser

    def get_all_approved_memberships(self):
        """ method to get all approved memberships of the user """
        return self.membership_user.filter(status="Approved")

    def is_allowed_admin_actions_on_group(self, group):
        """ method to check is admin actions allowed on group """
        return (
            group.member_is_owner(self) or self.is_admin_or_ops()
        )

    def is_allowed_to_offboard_user_from_group(self, group):
        """ method to check if it is allowed to off-board user from group """
        return group.member_is_owner(self) or self.has_permission("ALLOW_USER_OFFBOARD")

    def create_new_identity(self, access_tag="", identity=""):
        """ method to create new identity with access tag """
        return self.module_identity.create(access_tag=access_tag, identity=identity)

    def get_active_identity(self, access_tag):
        """ method to get all active identity of user by access tag """
        return self.module_identity.filter(
            access_tag=access_tag, status="Active"
        ).first()

    def get_all_active_identity(self):
        """ method to get all active identities of the user """
        return self.module_identity.filter(status="Active")

    def is_active(self):
        """ method to check if user is active """
        return self.current_state() == "active"

    def get_all_memberships(self):
        """ method to get all memberships of the user """
        return self.membership_user.all()

    def get_groups_history(self):
        """ method to get groups history """
        all_user_membership = self.get_all_memberships()
        group_history = []
        for each_membership in all_user_membership:
            group_access = each_membership.get_membership_details()
            if len(group_access) > 1:
                group_history.append(group_access)

        return group_history

    def get_group_access_count(self):
        """ method to get group access count """
        return self.membership_user.filter(group__status="Approved").count()

    def get_user_access_mapping_related_manager(self):
        """ method to get user access mapping related manager """
        all_user_identities = self.module_identity.order_by('id').reverse()
        access_request_mapping_related_manager = []
        for each_identity in all_user_identities:
            access_request_mapping_related_manager.append(each_identity.user_access_mapping)
        return access_request_mapping_related_manager

    def get_access_history(self, all_access_modules):
        """ method to get access history for all access modules """
        access_request_mapping_related_manager = self.get_user_access_mapping_related_manager()
        access_history = []

        for request_mapping_related_manager in access_request_mapping_related_manager:
            all_user_access_mappings = request_mapping_related_manager.order_by('id').reverse()
            for each_user_access_mapping in all_user_access_mappings:
                access_module = all_access_modules[each_user_access_mapping.access.access_tag]
                access_history.\
                    append(each_user_access_mapping.get_access_request_details(access_module))

        return access_history

    def get_total_access_count(self):
        """ method to get total access count """
        return UserAccessMapping.objects.filter(user_identity__user=self).count()

    def get_pending_access_count(self):
        """ method to get pending access count """
        return UserAccessMapping.objects.filter(user_identity__user=self, status="Pending").count()

    def get_group_pending_access_count(self):
        """" method to get pending access count from group """
        return UserAccessMapping.objects.filter(
            user_identity__user=self, access_type="Group"
        ).count()

    @staticmethod
    def get_user_from_username(username):
        """ method to get user from username """
        try:
            return User.objects.get(user__username=username)
        except User.DoesNotExist:
            return None

    def get_accesses_by_access_tag_and_status(self, access_tag, status):
        """ method to get accesses by access tag and status """
        try:
            user_identities = self.module_identity.filter(access_tag=access_tag)
        except UserIdentity.DoesNotExist:
            return None
        return UserAccessMapping.objects.filter(
            user_identity__in=user_identities,
            access__access_tag=access_tag,
            status__in=status,
        )

    def update_revoker(self, revoker):
        """ method to update revoker """
        self.revoker = revoker
        self.save()

    def offboard(self, revoker):
        """ method to off-board user by revoker """
        self.change_state("offboarding")
        self.update_revoker(revoker)
        self.offbaord_date = datetime.datetime.now()
        self.user.is_active = False
        self.save()

    def revoke_all_memberships(self):
        """ method to revoke all memberships """
        self.membership_user.filter(status__in=["Pending", "Approved"]).update(
            status="Revoked"
        )

    def get_or_create_active_identity(self, access_tag):
        """ method to get or create active identity for access_tag """
        identity, _created = self.module_identity.get_or_create(
            access_tag=access_tag, status="Active"
        )
        return identity

    @staticmethod
    def get_users_by_emails(emails):
        """ method to get users by emails """
        return User.objects.filter(email__in=emails)

    @staticmethod
    def get_user_by_email(email):
        """ method to get user by email """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_active_users_with_permission(permission_label):
        """ method to get active users with permission based on permission_label """
        try:
            return User.objects.filter(
                role__permission__label=permission_label, state=1
            )
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_system_user():
        """ method to get system users """
        try:
            return User.objects.get(user__username="system_user")
        except User.DoesNotExist:
            django_user = djangoUser.objects.create(username="system_user",
                                                    email="system_user@root.root")
            return django_user.user

    def get_active_users(self):
        """ method to get active users """
        return User.objects.filter(state='1').exclude(user=self.user)

    def __str__(self):
        return f"{self.user}"


def create_user(sender, instance, created, **_kwargs):
    """
    create a user when a django  user is created
    """
    del sender, created
    user, _created = User.objects.get_or_create(user=instance)
    user.name = instance.first_name
    user.email = instance.email
    try:
        user.avatar = instance.avatar
    except Exception:
        pass
    user.save()


post_save.connect(create_user, sender=djangoUser)


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
        """ method to deactivate request """
        self.status = "Revoked"
        self.save()

    def approve(self, approver):
        """ method to approve membership """
        self.status = "Approved"
        self.approver = approver
        self.save()

    def unapprove(self):
        """ method to un-approve membership """
        self.status = "Pending"
        self.approver = None
        self.save()

    def get_status(self):
        """ method to get status """
        return self.status

    def is_self_approval(self, approver):
        """ method to check is self-approval """
        return self.requested_by == approver

    def is_pending(self):
        """ method to check is status Pending """
        return self.status == "Pending"

    @staticmethod
    def approve_membership(membership_id, approver):
        """ method to approve membership """
        membership = MembershipV2.objects.get(membership_id=membership_id)
        membership.approve(approver=approver)

    def decline(self, reason, decliner):
        """ method to decline request """
        self.status = "Declined"
        self.decline_reason = reason
        self.approver = decliner
        self.save()

    def is_already_processed(self):
        """ method to check is request already processed """
        return self.status in ["Declined", "Approved", "Processing", "Revoked"]

    def revoke_membership(self):
        """ method to revoke membership """
        self.status = "Revoked"
        self.save()

    @staticmethod
    def update_membership(group, reason):
        """ method to update membership """
        membership = MembershipV2.objects.filter(group=group)
        membership.update(status="Declined", decline_reason=reason)

    def get_membership_details(self):
        """ method to get membership details """
        access_request_data = {}
        if self.group.status == "Approved":
            access_request_data["group_id"] = self.group.group_id
            access_request_data["name"] = self.group.name
            access_request_data["status"] = self.status
            access_request_data["role"] = "Owner" if self.is_owner else "Member"

        return access_request_data

    @staticmethod
    def get_membership(membership_id):
        """ method to get membership by membership id """
        try:
            return MembershipV2.objects.get(membership_id=membership_id)
        except MembershipV2.DoesNotExist:
            return None

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
        """ method to check if group exists by group name """
        if GroupV2.objects.filter(name=group_name):
            return True
        return False

    @staticmethod
    def create(
        name="", requester=None, description="", needs_access_approve=True, date_time=""
    ):
        """ method to create group """
        return GroupV2.objects.create(
            name=name,
            group_id=name + "-group-" + date_time,
            requester=requester,
            description=description,
            needsAccessApprove=needs_access_approve,
        )

    def add_member(
        self, user=None, is_owner=False, requested_by=None, reason="", date_time=""
    ):
        """ method to add member in the group """
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
        """ method to add members """
        if users:
            for usr in users:
                self.add_member(
                    user=usr,
                    requested_by=requested_by,
                    reason=reason,
                    date_time=date_time,
                )

    @staticmethod
    def get_pending_memberships():
        """ method to get pending memberships """
        return MembershipV2.objects.filter(status="Pending", group__status="Approved")

    def is_already_processed(self):
        """ method to check if status is already processed """
        return self.status in ['Declined', 'Approved', 'Processing', 'Revoked']

    def decline_access(self, decline_reason=None):
        """ method to get decline access """
        self.status = "Declined"
        self.decline_reason = decline_reason
        self.save()

    @staticmethod
    def get_pending_creation():
        """ method to get pending creation """
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
        """ method to get pending group """
        try:
            return GroupV2.objects.get(group_id=group_id, status="Pending")
        except GroupV2.DoesNotExist:
            return None

    @staticmethod
    def get_approved_group(group_id):
        """ method to get approved group """
        try:
            return GroupV2.objects.get(group_id=group_id, status="Approved")
        except GroupV2.DoesNotExist:
            return None

    @staticmethod
    def get_active_group_by_name(group_name):
        """ method to get active group by name """
        try:
            return GroupV2.objects.get(name=group_name, status="Approved")
        except GroupV2.DoesNotExist:
            return None

    @staticmethod
    def get_approved_group_by_name(group_name):
        """ method to get approved group by name """
        try:
            return GroupV2.objects.filter(name=group_name, status="Approved").first()
        except GroupV2.DoesNotExist:
            return None

    def approve_all_pending_users(self, approved_by):
        """ method to approve all pending users """
        self.membership_group.filter(status="Pending").update(
            status="Approved", approver=approved_by
        )

    def get_all_members(self):
        """ method to get all members """
        group_members = self.membership_group.all()
        return group_members

    def get_approved_and_pending_member_emails(self):
        """ method to get approved and pending members emails """
        group_member_emails = self.membership_group.filter(
            status__in=["Approved", "Pending"]
        ).values_list("user__email", flat=True)
        return group_member_emails

    def member_is_owner(self, user):
        """ method to check if member is owner of the group """
        try:
            membership = self.membership_group.get(user=user)
        except MembershipV2.DoesNotExist:
            return False
        return membership.is_owner

    def get_active_accesses(self):
        """ method to get active accesses """
        return self.group_access_mapping.filter(
            status__in=["Approved", "Pending", "Declined", "SecondaryPending"]
        )

    def get_group_access_count(self):
        """ method to get group access count """
        return self.get_active_accesses().count()

    def is_self_approval(self, approver):
        """ method to check it is self-approval """
        return self.requester == approver

    def approve(self, approved_by):
        """ method ot approve """
        self.approver = approved_by
        self.status = "Approved"
        self.save()

    def unapprove(self):
        """ method ot un-approve """
        self.approver = None
        self.status = "Pending"
        self.save()

    def unapprove_memberships(self):
        """ method to un-approve memberships """
        self.membership_group.filter(status="Approved").update(
            status="Pending", approver=None
        )

    def is_owner_by_user(self, user):
        """ method to check if user is owner """
        return (
            self.membership_group.filter(is_owner=True)
            .filter(user=user)
            .first()
            is not None
        )

    def add_access(self, request_id, requested_by, request_reason, access):
        """ method to add access """
        self.group_access_mapping.create(
            request_id=request_id,
            requested_by=requested_by,
            request_reason=request_reason,
            access=access,
        )

    def check_access_exist(self, access):
        """ method to if access exist """
        try:
            self.group_access_mapping.get(access=access, status__in=["Approved"])
            return True
        except GroupAccessMapping.DoesNotExist:
            return False

    def access_mapping_exists(self, access):
        """ method to check access mapping exists """
        try:
            self.group_access_mapping.get(access=access, status__in=["Approved", "Pending"])
            return True
        except GroupAccessMapping.DoesNotExist:
            return False

    def get_all_approved_members(self):
        """ method to get all approved members """
        return self.membership_group.filter(status="Approved")

    def get_approved_accesses(self):
        """ method to get approved accesses """
        return self.group_access_mapping.filter(status="Approved")

    def is_owner(self, email):
        """ method to check if user is owner based on email """
        return (
            self.membership_group.filter(is_owner=True)
            .filter(user__email=email)
            .first()
            is not None
        )

    def __str__(self):
        return str(self.name)


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

    fail_reason = models.TextField(null=True, blank=True)

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
        return str(self.request_id)

    # Wrote the override version of save method in order to update the
    # "approved_on" field whenever the request is marked "Approved"
    def save(self, *args, **kwargs):
        """ method to save UserAccessMapping request """
        super().save(*args, **kwargs)
        # Consider only the first cycle of approval
        if self.status.lower() == "approved" and self.approved_on in [None, ""]:
            self.approved_on = self.updated_on
            super().save(*args, **kwargs)

    @staticmethod
    def get_access_request(request_id):
        """ method to get access request """
        try:
            return UserAccessMapping.objects.get(request_id=request_id)
        except UserAccessMapping.DoesNotExist:
            return None

    def get_access_request_details(self, access_module):
        """ method to get access request details """
        access_request_data = {}
        access_tags = [self.access.access_tag]
        access_labels = [self.access.access_label]

        access_tag = access_tags[0]
        # code metadata
        access_request_data["access_tag"] = access_tag
        # ui metadata
        access_request_data["user"] = self.user_identity.user.name
        access_request_data["userEmail"] = self.user_identity.user.email
        access_request_data["requestId"] = self.request_id
        access_request_data["accessReason"] = self.request_reason
        access_request_data["requested_on"] = self.requested_on

        access_request_data["access_desc"] = access_module.access_desc()
        access_request_data["accessCategory"] = access_module.combine_labels_desc(
            access_labels
        )
        access_request_data["accessMeta"] = access_module.combine_labels_meta(
            access_labels
        )
        access_request_data["access_label"] = [
            key + "-" + str(val).strip("[]")
            for key, val in list(self.access.access_label.items())
            if key != "keySecret"
        ]
        access_request_data["access_type"] = self.access_type
        access_request_data["approver_1"] = (
            self.approver_1.user.username if self.approver_1 else ""
        )
        access_request_data["approver_2"] = (
            self.approver_2.user.username if self.approver_2 else ""
        )
        access_request_data["approved_on"] = (
            self.approved_on if self.approved_on else ""
        )
        access_request_data["updated_on"] = (
            str(self.updated_on)[:19] + "UTC" if self.updated_on else ""
        )
        access_request_data["status"] = self.status
        access_request_data["revoker"] = (
            self.revoker.user.username if self.revoker else ""
        )
        access_request_data["offboarding_date"] = (
            str(self.user_identity.user.offbaord_date)[:19] + "UTC"
            if self.user_identity.user.offbaord_date
            else ""
        )
        access_request_data["revokeOwner"] = ",".join(access_module.revoke_owner())
        access_request_data["grantOwner"] = ",".join(access_module.grant_owner())
        access_request_data["accessRequestType"] = self.access_type

        return access_request_data

    def update_meta_data(self, key, data):
        """ method to update metadata """
        with transaction.atomic():
            setattr(self.meta_data, key, data)
            self.save()
        return True

    def revoke(self, revoker=None):
        """ method to revoke access mapping """
        self.status = "Revoked"
        if revoker:
            self.revoker = revoker
        self.save()

    @staticmethod
    def get_accesses_not_declined():
        """ method to get accesses excluding the ones with declined status """
        return UserAccessMapping.objects.exclude(status="Declined")

    @staticmethod
    def get_unrevoked_accesses_by_request_id(request_id):
        """ method to get un-revoked access by request id """
        return UserAccessMapping.objects.filter(request_id=request_id).exclude(
            status="Revoked"
        )

    @staticmethod
    def get_unique_statuses():
        """ method to get unique statuses """
        return [
            status[0]
            for status in UserAccessMapping.objects.order_by().values_list('status').distinct()
        ]

    def is_approved(self):
        """ method to check is status Approved """
        return self.status == "Approved"

    def is_processing(self):
        """ method to check is status Processing """
        return self.status == "Processing"

    def is_pending(self):
        """ method to check is status Pending """
        return self.status == "Pending"

    def is_secondary_pending(self):
        """ method to check is SecondaryPending """
        return self.status == "SecondaryPending"

    def is_grantfailed(self):
        """ method to check if grant failed """
        return self.status == "GrantFailed"

    @staticmethod
    def get_pending_access_mapping(request_id):
        """ method to get pending access mapping """
        return UserAccessMapping.objects.filter(
            request_id__icontains=request_id, status__in=["Pending", "SecondaryPending"]
        ).values_list("request_id", flat=True)

    def update_access_status(self, current_status):
        """ method to update access status """
        self.status = current_status
        self.save()

    def is_already_processed(self):
        """ method to check if UserAccessMapping is already processed """
        return self.status in ["Declined", "Approved", "Processing", "Revoked"]

    def grant_fail_access(self, fail_reason=None):
        """ method for grant fail access """
        self.status = "GrantFailed"
        self.fail_reason = fail_reason
        self.save()

    def revoke_failed(self, fail_reason=None):
        """ method for revoke failed """
        self.status = "RevokeFailed"
        self.fail_reason = fail_reason
        self.save()

    def decline_access(self, decline_reason=None):
        """ method to decline access """
        self.status = "Declined"
        self.decline_reason = decline_reason
        self.save()

    def approve_access(self):
        """ method to approve access """
        self.status = "Approved"
        self.save()

    def revoking(self, revoker):
        """ method to set revoker """
        self.revoker = revoker
        self.status = "ProcessingRevoke"
        self.save()

    def processing(self, approval_type, approver):
        """ method to set approver """
        if approval_type == ApprovalType.PRIMARY:
            self.approver_1 = approver
        elif approval_type == ApprovalType.SECONDARY:
            self.approver_2 = approver
        else:
            raise Exception("Invalid ApprovalType")
        self.status = "Processing"
        self.save()

    @staticmethod
    def create(
        request_id,
        user_identity,
        access,
        approver_1,
        approver_2,
        request_reason,
        access_type,
        status,
    ):
        """ method to create UserAccessMapping """
        mapping = UserAccessMapping(
            request_id=request_id,
            user_identity=user_identity,
            access=access,
            approver_1=approver_1,
            approver_2=approver_2,
            request_reason=request_reason,
            access_type=access_type,
            status=status,
        )
        mapping.save()
        return mapping

    def get_user_name(self):
        """ method to get username """
        return self.user_identity.user.name


class GroupAccessMapping(models.Model):
    """
    Model to map access to group. Requests are broken down
    into mappings which are sent for approval.
    """

    request_id = models.CharField(max_length=255, null=False, blank=False, unique=True)

    requested_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    group = models.ForeignKey(
        "GroupV2",
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name="group_access_mapping",
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
        return str(self.request_id)

    def get_access_request_details(self, access_module):
        """ method to get access request details """
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
        access_request_data["module"] = access_tag.split('_')[0].capitalize()

        return access_request_data

    @staticmethod
    def get_by_id(request_id):
        """ method to get by id """
        try:
            return GroupAccessMapping.objects.get(request_id=request_id)
        except GroupAccessMapping.DoesNotExist:
            return None

    def mark_revoked(self, revoker):
        """ method to mark revoked """
        self.status = "Revoked"
        self.revoker = revoker
        self.save()

    @staticmethod
    def get_by_request_id(request_id):
        """ method to get request id """
        try:
            return GroupAccessMapping.objects.get(request_id=request_id)
        except GroupAccessMapping.DoesNotExist:
            return None

    @staticmethod
    def get_pending_access_mapping(request_id):
        """ method to get pending access mapping """
        return GroupAccessMapping.objects.filter(
            request_id__icontains=request_id, status__in=["Pending", "SecondaryPending"]
        ).values_list("request_id", flat=True)

    def is_pending(self):
        """ method to check if status is Pending """
        return self.status == "Pending"

    def is_secondary_pending(self):
        """ method to check if status is SecondaryPending """
        return self.status == "SecondaryPending"

    def set_primary_approver(self, approver):
        """ method to set primary approver """
        self.approver_1 = approver
        self.save()

    def set_secondary_approver(self, approver):
        """ method to set secondary approver """
        self.approver_2 = approver
        self.save()

    def get_primary_approver(self):
        """ method to get primary approver """
        return self.approver_1

    def get_secondary_approver(self):
        """ method to get secondary approver """
        return self.approver_2

    def approve_access(self):
        """ method to approve access """
        self.status = "Approved"
        self.save()

    def decline_access(self, decline_reason):
        """ method to decline access """
        self.status = "Declined"
        self.decline_reason = decline_reason
        self.save()

    def update_access_status(self, current_status):
        """ method to update access status to current_status """
        self.status = current_status
        self.save()

    def is_self_approval(self, approver):
        """ method to check self approval """
        return self.requested_by == approver

    def is_already_processed(self):
        """ method to check if Group Access mapping already processed """
        return self.status in ['Declined', 'Approved', 'Processing', 'Revoked']


class AccessV2(models.Model):
    """ model for AccessV2 """
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
    def get(access_tag, access_label):
        """ method to get AccessV2 object for given access_tag and access_label """
        try:
            return AccessV2.objects.get(
                access_tag=access_tag, access_label=access_label
            )
        except AccessV2.DoesNotExist:
            return None

    @staticmethod
    def create(access_tag, access_label):
        """ method to create AccessV2 object """
        return AccessV2.objects.create(access_tag=access_tag, access_label=access_label)


class UserIdentity(models.Model):
    """ model for User identity """
    @dataclasses.dataclass
    class Meta:
        """ class to store metadata """
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
        """ method to deactivate the status for UserIdentity """
        self.status = "Inactive"
        self.save()

    def get_active_access_mapping(self):
        """ method to get active access mappings for UserIdentity """
        return self.user_access_mapping.filter(
            status__in=["Approved", "Pending",
                        "SecondaryPending",
                        "GrantFailed"],
            access__access_tag=self.access_tag
        )

    def get_all_granted_access_mappings(self):
        """ method to get all granted access mappings for UserIdentity """
        return self.user_access_mapping.filter(
            status__in=["Approved", "Processing", "Offboarding"],
            access__access_tag=self.access_tag,
        )

    def get_all_non_approved_access_mappings(self):
        """ method to get all non-approved access mappings for UserIdentity """
        return self.user_access_mapping.filter(
            status__in=["Pending", "SecondaryPending", "GrantFailed"]
        )

    def decline_all_non_approved_access_mappings(self, decline_reason):
        """ method to decline all non approved access mappings for UserIdentity """
        user_mapping = self.get_all_non_approved_access_mappings()
        user_mapping.update(status="Declined", decline_reason=decline_reason)

    def get_granted_access_mapping(self, access):
        """ method to get granted access mappings for UserIdentity """
        return self.user_access_mapping.filter(
            status__in=["Approved", "Processing", "Offboarding"], access=access
        )

    def get_non_approved_access_mapping(self, access):
        """ method to get non approved access mappings for UserIdentity """
        return self.user_access_mapping.filter(
            status__in=["Pending", "SecondaryPending", "GrantFailed"],
            access=access,
        )

    def decline_non_approved_access_mapping(self, access, decline_reason):
        """ method to decline non approved access mapping for UserIdentity """
        user_mapping = self.get_non_approved_access_mapping(access)
        user_mapping.update(status="Declined", decline_reason=decline_reason)

    def offboarding_approved_access_mapping(self, access):
        """ method to offboard approved access mapping for UserIdentity """
        user_mapping = self.get_granted_access_mapping(access)
        user_mapping.update(status="Offboarding")

    def revoke_approved_access_mapping(self, access):
        """ method to revoke approved access mapping for UserIdentity """
        user_mapping = self.get_granted_access_mapping(access)
        user_mapping.update(status="Revoked")

    def mark_revoke_failed_for_approved_access_mapping(self, access):
        """ method to mark revoke failed for approved access mapping for UserIdentity """
        user_mapping = self.get_granted_access_mapping(access)
        user_mapping.update(status="RevokeFailed")

    def access_mapping_exists(self, access):
        """ method to check if access mapping exists fo rUserIdentity """
        try:
            self.user_access_mapping.get(
                access=access, status__in=["Approved", "Pending"]
            )
            return True
        except Exception:
            return False

    def replicate_active_access_membership_for_module(
        self, existing_user_access_mapping
    ):
        """ method to replicate active access membership for module for UserIdentity """
        new_user_access_mapping = []

        for i, user_access in enumerate(existing_user_access_mapping):
            base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
            request_id = (
                self.user.user.username
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
                    access=user_access.access,
                    approver_1=user_access.approver_1,
                    approver_2=user_access.approver_2,
                    request_reason=user_access.request_reason,
                    access_type=user_access.access_type,
                    status=access_status,
                )
            )
        return new_user_access_mapping

    def create_access_mapping(
        self,
        request_id,
        access,
        approver_1,
        approver_2,
        reason,
        access_type="Individual",
    ):
        """ method to create access mapping for UserIdentity """
        return self.user_access_mapping.create(
            request_id=request_id,
            access=access,
            approver_1=approver_1,
            approver_2=approver_2,
            request_reason=reason,
            access_type=access_type,
        )

    def has_approved_access(self, access):
        """ method to check approved access for UserIdentity """
        return self.user_access_mapping.filter(
            status="Approved", access=access
        ).exists()

    def __str__(self):
        return f"{self.identity}"
