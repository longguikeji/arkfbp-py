from executer import Executer

from .base import Node

# FunctionNode metadata
_NODE_NAME = 'flow'
_NODE_KIND = 'flow'


class FlowNode(Node):
    name = _NODE_NAME
    kind = _NODE_KIND
    child_flow = None

    def get_child_flow(self, *args, **kwargs):
        if not self.child_flow:
            raise NotImplemented('You must assign flow for a flow node')
        return self.child_flow

    def run(self, *args, **kwargs):
        _flow = self.get_child_flow(*args, **kwargs)
        ret = self.flow.run_sub_flow(_flow, self.inputs, *args, **kwargs)
        return ret