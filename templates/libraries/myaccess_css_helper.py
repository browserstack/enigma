from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def access_status_content(status):
    span_paths = {
        "exclaim": '''<path d="M11 15h2v2h-2v-2zm0-8h2v6h-2V7zm.99-5C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>''',
        "thumbs_down": '''<path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.58-6.59c.37-.36.59-.86.59-1.41V5c0-1.1-.9-2-2-2zm0 12l-4.34 4.34L11.77 14H3v-2l3-7h9v10zm4-12h4v12h-4z"/>''',
        "thumbs_up": '''<path d="M9 21h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.58 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2zM9 9l4.34-4.34L12 10h9v2l-3 7H9V9zM1 9h4v12H1z"/>''',
        "cross": '''<path d="M14.59 8L12 10.59 9.41 8 8 9.41 10.59 12 8 14.59 9.41 16 12 13.41 14.59 16 16 14.59 13.41 12 16 9.41 14.59 8zM12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>''',
    }
    status_mapping = {
        "Processing": {
            "icon_class": "text-amber-500",
            "text_class": "text-amber-700",
            "span_path": span_paths["exclaim"],
        },
        "Pending": {
            "icon_class": "text-amber-500",
            "text_class": "text-amber-700",
            "span_path": span_paths["exclaim"],
        },
        "SecondaryPending": {
            "icon_class": "text-amber-500",
            "text_class": "text-amber-700",
            "span_path": span_paths["exclaim"],
        },
        "Declined": {
            "icon_class": "text-red-400",
            "text_class": "text-red-600",
            "span_path": span_paths["thumbs_down"],
        },
        "RevokeFailed": {
            "icon_class": "text-red-400",
            "text_class": "text-red-600",
            "span_path": span_paths["thumbs_down"],
        },
        "GrantFailed": {
            "icon_class": "text-red-400",
            "text_class": "text-red-600",
            "span_path": span_paths["thumbs_down"],
        },
        "Approved": {
            "icon_class": "text-green-500",
            "text_class": "text-green-700",
            "span_path": span_paths["thumbs_up"],
        },
        "Revoked": {
            "icon_class": "text-gray-500",
            "text_class": "text-gray-700",
            "span_path": span_paths["cross"],
        },
        "ProcessingRevoke": {
            "icon_class": "text-amber-500",
            "text_class": "text-amber-700",
            "span_path": span_paths["cross"],
        },
        "Offboarding": {
            "icon_class": "text-amber-500",
            "text_class": "text-amber-700",
            "span_path": span_paths["cross"],
        },
    }
    details = status_mapping[status]

    return mark_safe('''
    <span class="inline-flex ''' + details["icon_class"] + '''">
        <svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 0 24 24" width="18px" fill="#000000" class="h-6 w-6" stroke="currentColor">''' + details["span_path"] + '''</svg>
        <span class="px-3 ''' + details["text_class"] + '''">''' + status + '''</span>
    </span>
    ''')

@register.simple_tag
def get_navigation_class(current_page, nav_page):
    if str(current_page) == str(nav_page):
        return "border-blue-500 text-blue-600"

    return "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
