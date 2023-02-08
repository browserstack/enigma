from django import template
register = template.Library()

def is_current_nav(navType, currentPath):
    pathMapping = {
        "Dashboard": "/",
        "Access": "/access/showAccessHistory",
        "Groups": "/access/group"
    }

    return pathMapping[navType] == currentPath

@register.simple_tag
def ahref_class_for_path(navType, currentPath):
    if is_current_nav(navType, currentPath):
        return "bg-gray-100 text-gray-900"

    return "text-gray-600 hover:bg-gray-50 hover:text-gray-900"

@register.simple_tag
def ahref_ariacurrent(navType, currentPath):
    if is_current_nav(navType, currentPath):
        return "page"

    return "undefined"

@register.simple_tag
def svg_class_for_path(navType, currentPath):
    if is_current_nav(navType, currentPath):
        return "text-gray-500"

    return "text-gray-400 group-hover:text-gray-500"

@register.simple_tag
def count_class_for_path(navType, currentPath):
    if is_current_nav(navType, currentPath):
        return "bg-white"

    return "bg-gray-100 group-hover:bg-gray-200"
