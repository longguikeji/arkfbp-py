import abc
import os
import sys

import six

from ..graph import Graph, GraphParser
from ..node.base import start_node
from ..state import State, AppState


FLOW_CREATED = 'CREATED'
FLOW_RUNNING = 'RUNNING'
FLOW_ERROR = 'ERROR'
FLOW_STOPPED = 'STOPPED'
FLOW_STATUS = [FLOW_CREATED, FLOW_RUNNING, FLOW_ERROR, FLOW_STOPPED]


@six.add_metaclass(abc.ABCMeta)
class Flow:

    inputs = None
    outputs = None
    debug = True

    def __init__(self):
        self.graph = self.create_graph()
        self._state = State()
        self._app_state = AppState()
        manual_state = self.create_state()
        if isinstance(manual_state, dict):
            self.state.commit(manual_state)
        self._request = None
        self._response = None
        self._status = 'CREATED'
        # 根据 Nodes & Edges 设置 next

    def __str__(self):
        return f'Flow: {self.__class__}'

    def __repr__(self):
        return self.__str__()

    @property
    def status(self):
        return self._status

    @property
    def state(self):
        return self._state

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, request):
        self._request = request

    @property
    def response(self):
        return self.outputs

    def create_graph(self):
        """Returns the node information in JSON form"""
        g = Graph()
        g.graph_nodes = self.create_nodes()
        g.edges = ['']
        return g

    @abc.abstractmethod
    def create_nodes(self):
        raise NotImplemented

    def create_state(self):
        """flow can override this function"""
        return self.state

    def main(self, inputs=None, *args, **kwargs):
        if inputs is not None:
            self.inputs = inputs
            self.outputs = inputs
        self._status = FLOW_RUNNING

        graph_parser = GraphParser(self.graph)
        graph_node = graph_parser.get_entry_node()
        while graph_node:
            # 获取`node`实例
            graph_node = graph_parser.parse_graph_node(graph_node)
            node = graph_node.instance
            # 运行`node`实例
            outputs = start_node(node, self, graph_node, *args, **kwargs)
            if not self.valid_status():
                return self.outputs
            graph_node = graph_node.next_graph_node(outputs)

        return self.outputs

    @classmethod
    def convert_request(cls, request):
        """Convert the framework's Request object to the ArkFBP's Request object"""
        return request

    def shutdown(self, outputs):
        self._status = FLOW_STOPPED
        self.outputs = outputs
        return self.response

    def log_debug(self):
        if not self.debug:
            sys.stdout.write('Flow Debug OFF')
            return
        sys.stdout.write(f'------------- DEBUG BEGIN ({self}) -------------\n\n')
        for node in self._state.nodes:
            sys.stdout.write('****** NODE ******\n')
            sys.stdout.write(f'ID: {node.id}\n')
            sys.stdout.write(f'Inputs: {node.inputs}\n')
            sys.stdout.write(f'Outputs: {node.outputs}\n')
            sys.stdout.write('****** END *******\n\n')
        sys.stdout.write(f'------------- DEBUG END ({self}) -------------\n')

    def before_initialize(self, *args, **kwargs):
        """overridden by user"""

    def init(self, inputs, *args, **kwargs):
        """overridden by user"""

    def initialized(self, inputs, *args, **kwargs):
        """overridden by user"""

    def before_execute(self, inputs, *args, **kwargs):
        """overridden by user"""

    def executed(self, inputs, ret, *args, **kwargs):
        """overridden by user"""

    def before_destroy(self, inputs, ret, *args, **kwargs):
        """overridden by user"""

    def valid_status(self):
        if self.status in [FLOW_STOPPED, FLOW_ERROR]:
            return False

        return True


def start_flow(flow, inputs, *args, **kwargs):

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
