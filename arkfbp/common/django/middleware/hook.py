import importlib
import json
from json.decoder import JSONDecodeError
from os import walk, path

from arkfbp.flow.base import FLOW_FROZEN
from arkfbp.flow.executer import FlowExecuter
from django.conf import settings
from django.core.management import CommandError
from django.utils.deprecation import MiddlewareMixin


PROCESS_REQUEST = 'BEFORE_ROUTE'
PROCESS_VIEW = 'BEFORE_FLOW'
PROCESS_EXCEPTION = 'BEFORE_EXCEPTION'
PROCESS_RESPONSE = 'BEFORE_RESPONSE'
PROCESS_TYPE = [PROCESS_REQUEST, PROCESS_VIEW, PROCESS_EXCEPTION, PROCESS_RESPONSE]
GLOBAL_HOOKS = {
    PROCESS_REQUEST: [],
    PROCESS_VIEW: [],
    PROCESS_EXCEPTION: [],
    PROCESS_RESPONSE: [],
}


def init():
    top_dir = settings.ARKFBP_CONF if hasattr(settings, 'ARKFBP_CONF') else \
        settings.SETTINGS_MODULE.rsplit('.', 1)[0]
    hook_dir = path.join(top_dir, 'arkfbp', 'hooks')

    for root, dirs, files in walk(hook_dir):
        for filename in files:
            if not filename.endswith('.json'):
                # Ignore some files as they cause various breakages.
                continue

            filepath = path.join(root, filename)
            with open(filepath, 'r', encoding='utf8') as hook_file:
                try:
                    hook_infos = json.load(hook_file)
                except JSONDecodeError:
                    raise CommandError(f'{filepath} Decoding Error!')

            #  获取流集合并校验
            for item in PROCESS_TYPE:
                hook_info = hook_infos.get(item.lower(), [])
                if not isinstance(hook_info, list):
                    raise CommandError(f'{filepath} Invalid!')

                hook_clzes = []
                for hook in hook_info:
                    try:
                        clz = importlib.import_module(f'{hook}.main')
                        _ = clz.Main()
                        hook_clzes.append(clz)
                    except ModuleNotFoundError:
                        raise CommandError(f'{hook} Invalid!')

                #  并入全局变量
                GLOBAL_HOOKS[item] += hook_clzes


init()


def execute(request, process_type, *args, **kwargs):
    hooks = GLOBAL_HOOKS[process_type]
    if not len(hooks):
        return None

    inputs = request
    for clz in hooks:
        hook_flow = clz.Main()
        outputs = FlowExecuter.start_flow(hook_flow, inputs, *args, **kwargs)
        if hook_flow.valid_status(FLOW_FROZEN):
            return outputs

    return None


class GlobalFlowMiddleware(MiddlewareMixin):

    def process_request(self, request):
        return execute(request, PROCESS_REQUEST)

    def process_view(self, request, view_func, view_args, view_kwargs):
        flow_class = view_func.__dict__.get('view_class', None)
        return execute(request, PROCESS_VIEW, flow_class=flow_class)

    def process_exception(self, request, exception):
        return execute(request, PROCESS_EXCEPTION, exception=exception)

    def process_response(self, request, response):
        execute(request, PROCESS_RESPONSE, response=response)
        return response
