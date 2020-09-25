import importlib
import json
import os
import sys

from django.core.management import CommandError
from django.test import RequestFactory


class Executer:
    """executer for flows and nodes"""

    def start_flow(self, flow, inputs, *args, **kwargs):

        flow.request = inputs
        flow.before_initialize(inputs, *args, **kwargs)

        if flow.valid_status():
            flow.init(inputs, *args, **kwargs)

        if flow.valid_status():
            flow.initialized(inputs, *args, **kwargs)

        if flow.valid_status():
            flow.before_execute(inputs, *args, **kwargs)

        if flow.valid_status():
            ret = flow.main(inputs, *args, **kwargs)

        if flow.valid_status():
            flow.executed(inputs, ret, *args, **kwargs)

        if flow.valid_status():
            flow.before_destroy(inputs, ret, *args, **kwargs)
        flow.log_debug()
        response = flow.die() if flow.valid_status() else flow.response
        return response

    def cli_start_flow(self, flow, inputs, *args, **kwargs):
        """start a flow by cli"""
        from ..flow import ViewFlow
        if isinstance(flow, ViewFlow):
            http_method = kwargs.get('http_method')
            content_type = kwargs.get('content_type', 'application/json')
            header = kwargs.get('header')
            if not http_method:
                raise CommandError('Lack of parameter: --http_method')
            if header:
                header = json.loads(header)
            # 构造 WSGIRequest 对象
            request_factory = RequestFactory()
            if http_method.lower() in ['get']:
                _inputs = json.loads(inputs)
                query_string = ''
                for key, value in _inputs.items():
                    query_string += f'{key}={value}&'
                query_string = f'?{query_string[:-1]}'
                request = request_factory.generic(http_method, query_string, content_type=content_type, **header)
            elif http_method.lower() in ['post', 'put', 'patch', 'delete']:
                request = request_factory.generic(http_method, '', data=inputs, content_type=content_type, **header)
            else:
                raise CommandError('Invalid parameter: --http_method')

        self.start_flow(flow, request)

    def start_test_flow(self, flow, inputs, *args, **kwargs):
        """start a test flow"""
        from ..flow import ViewFlow
        if isinstance(flow, ViewFlow):
            http_method = kwargs.get('http_method')
            content_type = kwargs.get('content_type', 'application/json')
            header = kwargs.get('header')
            if not http_method:
                raise Exception('Lack of parameter: http_method')
            if header:
                header = json.loads(header)
            # 构造 WSGIRequest 对象
            request_factory = RequestFactory()
            if http_method.lower() in ['get']:
                query_string = ''
                for key, value in inputs.items():
                    query_string += f'{key}={value}&'
                query_string = f'?{query_string[:-1]}'
                request = request_factory.generic(http_method, query_string, content_type=content_type, **header)
            elif http_method.lower() in ['post', 'put', 'patch', 'delete']:
                _inputs = json.dumps(inputs)
                request = request_factory.generic(http_method, '', data=_inputs, content_type=content_type, **header)
            else:
                raise Exception('Invalid parameter: http_method')

        self.start_flow(flow, request)

    def search_flow(self, top_dir, abs_dirs=[]):
        for file in os.listdir(top_dir):
            path = os.path.join(top_dir, file)
            if os.path.isdir(path):
                if file.startswith('test') and 'main.py' in os.listdir(path):
                    abs_dirs.append(os.path.abspath(path))
                self.search_flow(os.path.abspath(path), abs_dirs=abs_dirs)
            else:
                pass
        return abs_dirs

    def start_all_test_flows(self, top_dir):
        abs_dirs = self.search_flow(top_dir)
        for abs_dir in abs_dirs:
            try:
                path = abs_dir.replace(os.getcwd(), '').replace('/', '.').strip('.')+'.main'
                print(path)
                clz = importlib.import_module(path)
                flow = clz.Main()
                sys.stdout.write(
                    self.start_test_flow(flow, inputs={}, http_method='get') + '\n')
            except Exception as e:
                sys.stdout.write(e.__str__())

    def start_node(self, node, flow, graph_node, *args, **kwargs):
        node.flow = flow

        if flow.valid_status():
            node.created(*args, **kwargs)

        if flow.valid_status():
            node.before_initialize(*args, **kwargs)

        if flow.valid_status():
            node.init(*args, **kwargs)
            node.id = graph_node.id
            node.state = flow.state
            node.inputs = flow.outputs

        if flow.valid_status():
            node.initialized(*args, **kwargs)

        if flow.valid_status():
            node.before_execute(*args, **kwargs)

        if flow.valid_status():
            outputs = node.run(*args, **kwargs)

        if flow.valid_status():
            node.executed(*args, **kwargs)
            node.outputs = outputs
            flow.outputs = outputs
            flow.state.push(node)

        return outputs


FlowExecuter = Executer()
