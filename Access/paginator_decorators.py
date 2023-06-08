from django.core.paginator import Paginator
from django.http import JsonResponse

def paginator(view_function):
    def wrap(request, *args, **kwargs):
        response = view_function(request, *args, **kwargs)
        if type(response) == JsonResponse:
            return response
        page = (int(request.GET.get("page")) if request.GET.get("page") else 1)
        paginator = Paginator(response[response["rowList"]], 10)
        response["next_page"] = (page + 1 if page < paginator.num_pages else None)
        response["prev_page"] = (page - 1 if page > 1 else None)
        response[response["rowList"]] = list(paginator.get_page(page))

        return JsonResponse(response)

    wrap.__doc__ = view_function.__doc__
    wrap.__name__ = view_function.__name__
    return wrap
