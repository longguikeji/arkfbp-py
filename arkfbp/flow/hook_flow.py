from django.utils.deprecation import MiddlewareMixin

from ..flow import Flow
from ..request import HttpRequest
from ..flow.executer import FlowExecuter


class GlobalHookFlow(MiddlewareMixin, Flow):
    """
    Base Hook Flow
    When 'BaseHookFlow' is initialized, the 'set_mount' method needs
    to be overridden to specify where the hook should be opened.

    For example:
        class HookFlow(BaseHookFlow):
            def create_nodes(self):
                return [
                    {
                        'cls': StartNode,
                        'id': 'start',
                        'next': 'stop'
                    },
                    {
                        'cls': StopNode,
                        'id': 'stop'
                    }
                ]
            def set_mount(self):
                self._before_route = True
    """

    def __init__(self, get_response=None):
        self.before_route = False
        self.before_flow = False
        self.after_flow = False
        self.before_exception = False
        self.set_mount()
        super(GlobalHookFlow, self).__init__(get_response)

    def execute_hook(self, hook_switch, request, *args, **kwargs):
        inputs = self.convert_request(request)
        return FlowExecuter.start_flow(self, inputs, *args, **kwargs) if hook_switch else None

    def process_request(self, request):
        self.execute_hook(self.before_route, request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        flow_class = view_func.__dict__.get('view_class', None)
        self.execute_hook(self.before_flow, request, flow_class=flow_class)

    def process_exception(self, request, exception):
        self.execute_hook(self.before_exception, request, exception=exception)

    def process_response(self, request, response):
        self.execute_hook(self.after_flow, request, response=response)
        return response

    def set_mount(self):
        """
        Sets the global hook flow mount location,
        which can be overridden by subclasses
        """

    @classmethod
    def convert_request(cls, request):
        _request = HttpRequest(request.environ)
        request.__dict__.update(arkfbp_request=_request)
        return request
