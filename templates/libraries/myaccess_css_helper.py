from django import template
register = template.Library()

def is_current_sort(thType, sortParam):
    if not sortParam:
        sortParam = "Module"

    return thType == sortParam

@register.simple_tag
def th_sorted_class(thType, sortParam):
    if is_current_sort(thType, sortParam):
        return "bg-gray-200 text-gray-900 group-hover:bg-gray-300"

    return "invisible text-gray-400 group-hover:visible group-focus:visible"
