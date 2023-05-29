from django.core.exceptions import PermissionDenied
from Access.helpers import getPossibleApproverPermissions


def user_admin_or_ops(function):
    def wrap(request, *args, **kwargs):
        if request.user.user.isAdminOrOps():
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def authentication_classes(authentication_classes):
    def decorator(func):
        func.authentication_classes = authentication_classes
        return func

    return decorator


def user_with_permission(permissions_list):
    def user_with_permission_decorator(function):
        def wrap(request, *args, **kwargs):
            if hasattr(request.user, "user"):
                permission_labels = [
                    permission.label for permission in request.user.user.permissions
                ]
                if len(set(permissions_list).intersection(permission_labels)) > 0:
                    return function(request, *args, **kwargs)
            raise PermissionDenied

        return wrap

    return user_with_permission_decorator


def user_any_approver(function):
    def wrap(request, *args, **kwargs):
        all_approve_permissions = getPossibleApproverPermissions()
        is_any_approver = request.user.user.isAnApprover(all_approve_permissions)
        if is_any_approver:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
