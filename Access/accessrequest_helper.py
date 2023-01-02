from Access import helpers
import logging
from Access.models import UserAccessMapping, User

logger = logging.getLogger(__name__)

def requestAccessGet(request):
    context = {}
    try:
        for each_access in helpers.getAvailableAccessModules():
            if "access_" + each_access.tag() in request.GET.getlist('accesses'):
                if 'accesses' not in context:
                    context['accesses'] = []
                    context['genericForm'] = True
                    try:
                        extra_fields = each_access.get_extra_fields()
                    except:
                        extra_fields = []
                    try:
                        notice = each_access.get_notice()

                    except Exception:
                        notice = ""
                    context['accesses'].append({
                            'formDesc': each_access.access_desc(),
                            'accessTag': each_access.tag(),
                            'accessTypes': each_access.access_types(),
                            'accessRequestData': each_access.access_request_data(request, is_group=False),
                            'extraFields': extra_fields,
                            'notice': notice,
                            'accessRequestPath': each_access.fetch_access_request_form_path()
                        })
    except Exception as e:
        logger.exception(e)
        context = {}
        context['status'] = {'title':'Error Occured', 'msg': 'There was an error in getting the requested access resources. Please contact Admin'}
    return context


def getGrantFailedRequests(request):
    try:
        failures = UserAccessMapping.objects.filter(status__in=['grantfailed']).order_by('-requested_on')
        if request.GET.get('username'):
            user = User.objects.get(user__username=request.GET.get('username'))
            failures = failures.filter(user=user).order_by('-requested_on')
        if request.GET.get('access_type'):
            access_tag = request.GET.get('access_type')
            failures = failures.filter(access__access_tag=access_tag).order_by('-requested_on')

        context = {
            'failures': failures,
            'heading': "Grant Failures"
        }
        return context
    except Exception as e:
        logger.debug("Error in request not found OR Invalid request type")
        logger.exception(e)
        json_response = {}
        json_response['error'] = {'error_msg': str(e), 'msg': "Error in request not found OR Invalid request type"}
        return json_response
