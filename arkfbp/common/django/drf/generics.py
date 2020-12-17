"""Process requests from django.

A flow is a django view which process request.
 We convert an interface in config.json to an APIView, and process requests with flows.
"""
from arkfbp.graph import GraphParser
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet as ModelViewSetBase
from arkfbp.executer import Executer
from arkfbp.flow.base import Flow, FLOW_ERROR
from state import FlowState, AppState


class ViewsetMeta(type):
    """
    要用这个元类生成一个具有全部求值环境的ModelViewSet类
    """

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)


class GeneralSerializer(serializers.ModelSerializer):

    class Meta:
        model = None
        fields = '__all__'


# pylint: disable=abstract-method
class ModelViewSet(ModelViewSetBase, Flow):
    """
    经过改造后的ModelViewSet基类。混合两个主要特性: Flow 的特性， 标准查改增删特性
    """

    def __init__(self, *args, **kwargs):
        self.graph = self.create_graph()
        self._state = FlowState()
        self._app_state = AppState()
        manual_state = self.create_state()
        if isinstance(manual_state, dict):
            self.state.commit(manual_state)
        self._request = None
        self._response = None
        self._status = 'CREATED'
        self.error = None
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        model = self.model
        return model.objects.all()

    def get_serializer_class(self):
        if self.serializer_class:
            return self.serializer_class
        else:
            GeneralSerializer.Meta.model = self.model
            return GeneralSerializer

    def dispatch(self, request, *args, **kwargs):
        """
        override django view function dispatch.
        """
        self.args = args
        self.kwargs = kwargs
        if request.method in self.allowed_methods:
            return Executer.start_flow(self, request, *args, **kwargs)

    @classmethod
    def set_http_method(cls, method: list):
        """
        set http method.
        """
        cls.allow_http_method = method

    def shutdown(self, outputs, **kwargs):
        """
        shutdown the flow.
        """
        self.response_status = kwargs.get('response_status', 200)
        super().shutdown(outputs)

    @property
    def response(self):
        """
        generate a http response.
        """
        return self.outputs

    def terminate(self, exception):
        """
        when a exception raises in a flow,it will be called.
        """
        self._status = FLOW_ERROR
        self.error = exception
        response = self.handle_exception(exception)

        response = self.finalize_response(self.request, response, *self.args, **self.kwargs)
        self.outputs = response

    def run_sub_flow(self, sub_flow, *args, **kwargs):
        """在当前上下文环境运行一个sub_flow,获得结果。"""
        graph_parser = GraphParser(sub_flow.graph)
        graph_node = graph_parser.get_entry_node()
        outputs = None
        while graph_node:
            # 获取`node`实例
            graph_node = graph_parser.parse_graph_node(graph_node)
            node = graph_node.instance
            # 运行`node`实例
            outputs = Executer.start_node(node, self, graph_node, *args, **kwargs)
            if not self.valid_status():
                return self.outputs
            graph_node = graph_node.next_graph_node(outputs)
        return outputs
