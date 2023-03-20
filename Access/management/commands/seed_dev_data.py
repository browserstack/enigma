from django.contrib.auth.models import User as DjangoUser
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import logging, random, string, time, datetime, pytz

from Access.models import *

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

def create_user(username, email):
    try:
        duser = DjangoUser.objects.get(username=username, name=username)
        logging.warning("User %s already exists" % (username))
    except:
        duser = DjangoUser.objects.create_superuser(username, email, 'qweqweqwe')
        duser.is_ops = True
        duser.is_manager = True
        duser.name = username
        duser.save()
        User.objects.create(email=email, user=duser, name=username)

    user = duser.user
    access_approve_permission, created = Permission.objects.get_or_create(label="ACCESS_APPROVE")

    access_approve_role, created = Role.objects.get_or_create(label="ACCESS_APPROVE_ROLE")
    if access_approve_permission not in access_approve_role.permission.all():
        access_approve_role.permission.add(access_approve_permission)
    access_approve_role.save()

    if access_approve_role not in user.role.all():
        user.role.add(access_approve_role)
    user.save()

    return duser

class Command(BaseCommand):
    help = 'Seed data for development environment'

    def handle(self, *args, **kwargs):
        logger = logging.getLogger(__name__)

        duser = create_user('root', 'root@root.root')
        user = duser.user

        approver = create_user('user1', 'user1@gmail.com').user

        AccessV2.objects.create(access_tag="old_module_tag1")
        AccessV2.objects.create(access_tag="old_module_tag2")
        AccessV2.objects.create(access_tag="old_module_tag3")
        AccessV2.objects.create(access_tag="old_module_tag4")

        all_accesses = []
        aws_access_count = 14
        confluence_access_count = 31
        github_access_count = 20
        groups_count = 80

        confluence_access_levels = ["View Access", "Edit Access", "Admin Access"]
        github_access_levels = ["push", "pull", "admin", "merge"]

        for i in range(aws_access_count):
            all_accesses.append(AccessV2.objects.create(access_tag="aws_access", access_label={"account":"dummy","group": ("dummy_group_%s" % randomword(5)),"action":"GroupAccess"}))

        for i in range(confluence_access_count):
            all_accesses.append(AccessV2.objects.create(access_tag="confluence_module", access_label={"access_workspace": ("dummy_workspace_%s" % randomword(5)),"access_type": random.choice(confluence_access_levels)}))

        for i in range(github_access_count):
            all_accesses.append(AccessV2.objects.create(access_tag="github_access", access_label={"repository": ("dummy_repo_%s" % randomword(5)),"access_level": random.choice(github_access_levels), "action": "repository_access"}))
        logging.info("Created AccessV2 Objects")

        STATUS_CHOICES = [
            "Pending",
            "Processing",
            "Approved",
            "GrantFailed",
            "Declined",
            "Offboarding",
            "ProcessingRevoke",
            "RevokeFailed",
            "Revoked",
        ]

        identities = {
            "aws_access": UserIdentity.objects.get_or_create(status="Active", identity='{}', user=user, access_tag="aws_access")[0],
            "confluence_module": UserIdentity.objects.get_or_create(status="Active", identity='{}', user=user, access_tag="confluence_module")[0],
            "github_access": UserIdentity.objects.get_or_create(status="Active", identity='{}', user=user, access_tag="github_access")[0],
        }

        random.shuffle(all_accesses)
        for each_access in all_accesses:
            base_datetime_prefix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
            request_id = (
                randomword(10)
                + "-"
                + randomword(20)
                + "-"
                + base_datetime_prefix
                + "-"
                + str(random.choice([0, 1, 2]))
            )

            status = random.choice(STATUS_CHOICES)
            userMappingObj, created = UserAccessMapping.objects.get_or_create(
                request_id = request_id,
                user_identity = identities[each_access.access_tag],
                access = each_access,
                approver_1 = approver,
                request_reason = "%s--%s--%s" % (randomword(20), randomword(10), randomword(10)),
                access_type = "Individual",
                status = status,
                updated_on = timezone.now(),
                approved_on = timezone.now(),
            )
        logging.info("Creating Groups")
        for i in range(groups_count):
            status = random.choice(['Pending', 'Approved', 'Declined', 'Deprecated'])
            new_group = GroupV2.create(
                name = randomword(12),
                description = randomword(60),
                requester = user,
                needsAccessApprove = random.choice([ True, False ])
            )
            new_group.status = status
            if status == 'Declined':
                new_group.decline_reason = randomword(50)
            if status == 'Approved':
                new_group.approver = approver
            new_group.save()

            new_membership = MembershipV2.objects.create(
                membership_id = randomword(20),
                user = user,
                group = new_group,
                is_owner = random.choice([ True, False ]),
                requested_by = user,
            )
            new_membership.status = random.choice(['Pending', 'Approved', 'Declined', 'Revoked'])
            if new_membership.status != 'Approved':
                new_membership.reason = randomword(60)
            if new_membership.status == 'Declined':
                new_membership.decline_reason = randomword(60)
            new_membership.approver = approver
            new_membership.save()
        logging.info("Done")
