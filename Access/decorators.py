from django.core.exceptions import PermissionDenied
from Access.helpers import get_possible_approver_permissions
from django.core.paginator import Paginator


def user_admin_or_ops(function):
    def wrap(request, *args, **kwargs):
        if request.user.user.is_admin_or_ops():
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
        all_approve_permissions = get_possible_approver_permissions()
        is_any_approver = request.user.user.is_an_approver(all_approve_permissions)
        if is_any_approver:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def paginated_search(view_function):
    def wrap(request, *args, **kwargs):
        template, context = view_function(request, *args, **kwargs)
        if context.get("error"):
            template.context_data = context
            return template.render()
        page = request.GET.get("page")
        max_page_size = 25
        key = context["search_data_key"]
        search_rows = context["search_rows"]
        filter_rows = context["filter_rows"]
        search = request.GET.get("search")
        filters = {}
        for filter_row in filter_rows:
            params = request.GET.getlist(filter_row)
            if not params and len(params) == 0:
                continue
            filters[filter_row] = params

        final_values = []

        for value in context[key]:
            in_final_values = True
            if search:
                in_any_search_row = False
                for row in search_rows:
                    in_any_search_row = in_any_search_row or (search in value[row])
                in_final_values = in_any_search_row

            if filters:
                for row, val in filters.items():
                    if value[row] not in val:
                        in_final_values = in_final_values and False

            if in_final_values:
                final_values.append(value)

        if len(final_values) != 0:
            context[key] = final_values
        else:
            context[
                "search_error"
            ] = "Please try adjusting your search criteria or browse by filters to find what you're looking for."

        paginator = Paginator(context[key], max_page_size)
        if not page:
            page = 1
            context[key] = paginator.get_page(1)
        else:
            context[key] = paginator.get_page(page)

        context["maxPagination"] = int(paginator.num_pages)
        context["allPages"] = range(1, paginator.num_pages + 1)
        context["currentPagination"] = int(page)
        template.context_data = context

        return template.render()

    wrap.__doc__ = view_function.__doc__
    wrap.__name__ = view_function.__name__
    return wrap
