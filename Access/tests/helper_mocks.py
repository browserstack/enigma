from unittest.mock import Mock


class MockAccessModule:
    def __init__(
        self,
        name="",
        primaryApproverPermissionLabel="",
        secondaryApproverPermissionLabel="",
    ):
        self.name = name
        self.available = True
        permissions = {}
        if primaryApproverPermissionLabel != "":
            permissions = {
                "1": primaryApproverPermissionLabel,
            }
            if secondaryApproverPermissionLabel != "":
                permissions["2"] = secondaryApproverPermissionLabel
        self.fetch_approver_permissions = Mock(return_value=permissions)

    def tag(self):
        return self.name


class MockPermission:
    def __init__(self, label=""):
        self.label = label
