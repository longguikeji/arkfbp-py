"""
Base flow.
"""
import abc
import sys

from cachetools import cached
from cachetools.keys import hashkey

from arkfbp.executer import Executer
from ..graph import Graph, GraphParser
from ..state import AppState, FlowState

FLOW_RUNNING = 'RUNNING'
FLOW_CREATED = 'CREATED'
FLOW_ERROR = 'ERROR'
FLOW_STOPPED = 'STOPPED'
FLOW_FROZEN = 'FROZEN'
FLOW_STATUS = (FLOW_CREATED, FLOW_RUNNING, FLOW_ERROR, FLOW_STOPPED, FLOW_FROZEN)


class Flow:
    """
    base flow.
    """
    inputs = None
    outputs = None
    debug = True

    def __init__(self):
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
        # 根据 Nodes & Edges 设置 next

    # pylint: disable=missing-function-docstring
    def __str__(self):
        return f'Flow: {self.__class__}'

    # pylint: disable=missing-function-docstring
    def __repr__(self):
        return self.__str__()

    @property
    def status(self):
        """
        status of flow.
        """
        return self._status

    @property
    def state(self):
        """
        state of flow.
        """
        return self._state

    @property
    def request(self):
        """
        request of flow,it always in a view flow.
        """
        return self._request

    @request.setter
    def request(self, request):
        self._request = request

    @property
    def response(self):
        """
        response of flow,it always in a view flow.
        """
        return self.outputs

    @cached(cache={}, key=lambda self: hashkey(self.__str__()))
    def create_graph(self):
        """
        Returns the node information in JSON form.
        """
        graph = Graph()
        graph.graph_nodes = self.create_nodes()
        graph.edges = ['']
        return graph

    @abc.abstractmethod
    def create_nodes(self):
        """
        override by subclass.
        """
        raise NotImplementedError

    def create_state(self):
        """
        flow can override this function.
        """
        return self.state

    def main(self, inputs, *args, **kwargs):
        """
        main function of a flow.
        """
        if inputs is not None:
            self.inputs = inputs
            self.outputs = inputs
        self._status = FLOW_RUNNING
        try:
            graph_parser = GraphParser(self.graph)
            graph_node = graph_parser.get_entry_node()
            while graph_node:
                # 获取`node`实例
                graph_node = graph_parser.parse_graph_node(graph_node)
                node = graph_node.instance
                # 运行`node`实例
                outputs = Executer.start_node(node, self, graph_node, *args, **kwargs)
                if not self.valid_status():
                    return self.outputs
                graph_node = graph_node.next_graph_node(outputs)
        # pylint:disable=broad-except
        except Exception as exception:
            self.terminate(exception)

        return self.outputs

    def shutdown(self, outputs):
        """
        Manually stop a workflow.
        """
        self._status = FLOW_FROZEN
        self.outputs = outputs
        return self.response

    def terminate(self, exception):
        """
        when a exception raises in a flow,it will be called.
        """
        self._status = FLOW_ERROR
        self.error = exception

    def die(self):
        """
        a flow ends normally.
        """
        self._status = FLOW_STOPPED
        return self.response

    def log_debug(self):
        """
        debug for a flow info when it runs.
        """
        if not self.debug:
            return

        sys.stdout.write(f'------------- DEBUG BEGIN ({self}) -------------\n\n')
        for node in self._state.nodes:
            sys.stdout.write(f'****** {node} ******\n')
            sys.stdout.write(f'ID: {node.id}\n')
            sys.stdout.write(f'Inputs: {node.inputs}\n')
            sys.stdout.write(f'Outputs: {node.outputs}\n')
            sys.stdout.write('****** END *******\n\n')
        #if self.valid_status(target=FLOW_ERROR):
        #    raise self.error
        sys.stdout.write(f'------------- DEBUG END ({self}) -------------\n')

    def before_initialize(self, *args, **kwargs):
        """
        overridden by user.
        """

    def init(self, inputs, *args, **kwargs):
        """
        overridden by user.
        """

    def initialized(self, inputs, *args, **kwargs):
        """
        overridden by user.
        """

    def before_execute(self, inputs, *args, **kwargs):
        """
        overridden by user.
        """

    def executed(self, inputs, ret, *args, **kwargs):
        """
        overridden by user.
        """

    def before_destroy(self, inputs, ret, *args, **kwargs):
        """
        overridden by user.
        """

    def valid_status(self, target=None):
        """
        Verify the state of a flow to determine whether to continue running.
        """
        if target in FLOW_STATUS:
            return target == self._status

        if self._status in [FLOW_STOPPED, FLOW_ERROR, FLOW_FROZEN]:
            return False

        return True
