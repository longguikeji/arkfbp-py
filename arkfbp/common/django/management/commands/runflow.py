import importlib
import json

from django.core.management.base import BaseCommand, CommandError
from django.test import RequestFactory

from arkfbp.flow import ViewFlow, start_flow


class Command(BaseCommand):
    help = "Run a Arkfbp Flow for the given flow name"
    # missing_args_message = "You must provide an flow name."

    def handle(self, **options):
        path = options.get('flow')
        input = options.get('input')
        http_method = options.get('http_method', None)
        try:
            clz = importlib.import_module(f'{path}.main')
            instance = clz.Main()
            cli_start_flow(instance, input, http_method=http_method)
        except ModuleNotFoundError:
            raise CommandError('Run failed, Invalid flow.')

    def add_arguments(self, parser):
        parser.add_argument('--flow', type=str, help='Specifies the import path for the target flow name.')
        parser.add_argument('--input', type=str, help='Input data at the beginning of the flow.')
        parser.add_argument('--http_method', type=str, help='HTTP method of flow.')


def cli_start_flow(flow, inputs, *args, **kwargs):
    """start a flow by cli"""
    if isinstance(flow, ViewFlow):
        http_method = kwargs.get('http_method')
        content_type = kwargs.get('content_type', 'application/json')
        if not http_method:
            raise CommandError('缺少请求访问方式参数: --http_method')
        # 构造 WSGIRequest 对象
        request_factory = RequestFactory()

        if http_method.lower() in ['get']:
            _inputs = json.loads(inputs)
            query_string = ''
            for key, value in _inputs.items():
                query_string += f'{key}={value}&'
            query_string = f'?{query_string[:-1]}'
            request = request_factory.generic(http_method, query_string, content_type=content_type)
        elif http_method.lower() in ['post', 'put', 'patch', 'delete']:
            request = request_factory.generic(http_method, '', data=inputs, content_type=content_type)
        else:
            raise CommandError('无效的请求访问方式参数: --http_method')

        inputs = ViewFlow.convert_request(request)

    start_flow(flow, inputs)
