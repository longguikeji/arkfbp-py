"""
Executer for both flow and node
"""
import importlib
import json
import os
import sys

from django.core.management import CommandError
from django.test import RequestFactory


class Executer:
    """executer for flows and nodes"""
    @classmethod
    def start_flow(cls, flow, inputs, *args, **kwargs):
        """
        start a flow
        """
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

    @classmethod
    def cli_start_flow(cls, flow, inputs, *args, **kwargs):
        """
        start a flow by cli
        """
        # pylint: disable=import-outside-toplevel
        from .flow import ViewFlow
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

        cls.start_flow(flow, request, *args, **kwargs)

    @classmethod
    def start_testflow(cls, flow, inputs, *args, **kwargs):
        """start a test flow"""
        # pylint: disable=import-outside-toplevel
        from .flow import ViewFlow
        if isinstance(flow, ViewFlow):
            http_method = kwargs.get('http_method')
            content_type = kwargs.get('content_type', 'application/json')
            header = kwargs.get('header', {})
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

        return cls.start_flow(flow, request, *args, **kwargs)

    @classmethod
    def start_testflows(cls, top_dir):
        """
        start a test flow
        """
        def collect(_top_dir, _abs_dirs=None):
            if _abs_dirs is None:
                _abs_dirs = []
            for file in os.listdir(_top_dir):
                path = os.path.join(_top_dir, file)
                if os.path.isdir(path):
                    if file.startswith('test') and 'main.py' in os.listdir(path):
                        _abs_dirs.append(os.path.abspath(path))
                    collect(os.path.abspath(path), _abs_dirs=_abs_dirs)
                else:
                    pass
            return _abs_dirs

        abs_dirs = collect(top_dir)
        for abs_dir in abs_dirs:
            try:
                path = abs_dir.replace(os.getcwd(), '').replace('/', '.').strip('.') + '.main'
                print(path)
                clz = importlib.import_module(path)
                flow = clz.Main()
                print(cls.start_testflow(flow, inputs={}, http_method='get'))
            # pylint: disable=broad-except
            except Exception as exception:
                sys.stdout.write(exception.__str__())

    @classmethod
    def start_node(cls, node, flow, *args, graph_node=None, **kwargs):
        """
        start a node
        """
        node.flow = flow

        if flow.valid_status():
            node.created(*args, **kwargs)

        if flow.valid_status():
            node.before_initialize(*args, **kwargs)

        if flow.valid_status():
            node.init(*args, **kwargs)
            node.id = graph_node.id if graph_node else node.__class__.__name__
            node.state = flow.state
            node.inputs = kwargs.get('inputs', None) or flow.outputs

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
