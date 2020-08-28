from django.utils.deprecation import MiddlewareMixin

from arkfbp.flow import Flow
from arkfbp.request import HttpRequest


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

    def execute_hook(self, hook_switch, request):
        inputs = self.convert_request(request)
        return self.main(inputs) if hook_switch else None

    def process_request(self, request):
        self.execute_hook(self.before_route, request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """TODO 处理参数"""
        self.execute_hook(self.before_flow, request)

    def process_exception(self, request, exception):
        """TODO 处理参数"""
        self.execute_hook(self.before_exception, request)

    def process_response(self, request, response):
        """TODO 处理参数"""
        self.execute_hook(self.after_flow, request)
        return response

    def set_mount(self):
        """
        Sets the global hook flow mount location,
        which can be overridden by subclasses
        """

    def convert_request(self, request):
        return HttpRequest(request.environ)