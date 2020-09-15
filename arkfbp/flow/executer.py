import importlib
import json
import os
import sys

from django.core.management import CommandError
from django.test import RequestFactory


class Executer:
    """"""

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
        return flow.response

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

            inputs = ViewFlow.convert_request(request)

        self.start_flow(flow, inputs)

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

            inputs = ViewFlow.convert_request(request)

        self.start_flow(flow, inputs)

    def search_flow(self, top_dir, absdir = []):
        for file in os.listdir(top_dir):
            path = os.path.join(top_dir,file)
            if os.path.isdir(path) and file.startswith('test'):
                if 'main.py' in os.listdir(path):
                    absdir.append(os.path.abspath(path))

            elif os.path.isdir(path):
                self.search_flow(os.path.abspath(path),absdir=absdir)
            else:
                pass
        return absdir

    def start_all_test_flows(self, top_dir):
        dirlist = self.search_flow(top_dir)
        for start_dir in dirlist:
            try:
                test_dir = start_dir.replace(os.getcwd(),'').replace('/','.').strip('.')+'.main'
                print(test_dir)
                a = importlib.import_module(test_dir)
                main = a.Main()
                sys.stdout.write(
                    self.start_test_flow(main, inputs={}, http_method='get') + '\n')
            except Exception as e:
                sys.stdout.write(str(e))

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
