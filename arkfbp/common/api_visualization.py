"""
API information synchronization
"""


class VisualAPI:
    """
    Base Visual API
    """

    def __init__(self, routes_info):
        self.routes_info = routes_info
        self.namespace = routes_info.get('namespace', None)
        self.routes = routes_info.get('routes', None)

    def generate_api(self):
        """
        Generate different forms of routing according to different frameworks
        """
        raise NotImplemented

    def validate_routeinfo(self):
        if not isinstance(self.namespace, str):
            raise Exception('Invalid namespace! namespace must be string.')

        if not isinstance(self.routes, list):
            raise Exception('Invalid routes! routes must be list.')


class DjangoVisualApi(VisualAPI):
    """
    Visual API for Django
    """

    def generate_api_context(self):
        # 校验路由信息的大致完整性
        self.validate_routeinfo()

        modules, apis = [], []
        for route in self.routes:
            for key, value in route.items():
                # 查找method相对应
                if isinstance(value, dict):
                    for method, flow in value.items():
                        modules, apis = self.extend_api_context(modules, apis, flow=flow, key=key, method=method)
                # 默认method为get
                elif isinstance(value, str):
                    modules, apis = self.extend_api_context(modules, apis, flow=value, key=key)
                else:
                    raise Exception('Invalid route information was found while generating the API!')
        return modules, apis

    def extend_api_context(self, modules, apis, **kwargs):
        """extend api context"""
        cls_as = kwargs.get('flow').replace('.', '_')
        http_method = [kwargs.get('method', 'GET').upper()]
        api = "path('{0}', {1}.pre_as_view(http_method={2}), name='{3}')".format(
            self.namespace + kwargs.get('key'),
            cls_as,
            http_method,
            cls_as
        )

        apis.append(api)
        module = 'from {0}.main import Main as {1}'.format(
            kwargs.get("flow"),
            cls_as
        )
        modules.append(module)
        return modules, apis
