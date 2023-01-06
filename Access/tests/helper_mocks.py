from unittest.mock import Mock

class MockAccessModule:
    def __init__(self, name="", primaryApproverPermissionLabel="", secondaryApproverPermissionLabel=""):
        self.name = name
        self.available = True
        if primaryApproverPermissionLabel != "":
            permissions = {
                    "1": primaryApproverPermissionLabel,
                    }
            if secondaryApproverPermissionLabel != "":
                permissions["2"] = secondaryApproverPermissionLabel
            self.fetch_approver_permissions = Mock(return_value=permissions)

class MockPermission:
    def __init__(self, label=""):
        self.label = label

class MockAccessUser:
    def __init__(self, permissionLabels=[]):
        self.permissions = []
        for each_permission_label in permissionLabels:
            self.permissions.extend([MockPermission(each_permission_label)])

class MockDjangoUser:
    def __init__(self, permissionLabels=[]):
        self.user = MockAccessUser(permissionLabels)
