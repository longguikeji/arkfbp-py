from .base import Node


# TriggerFlowNode metadata
_NODE_NAME = 'trigger_flow'
_NODE_KIND = 'trigger_flow'


class TriggerFlowNode(Node):

    name = _NODE_NAME
    kind = _NODE_KIND
    flow_name = None

    def run(self, *args, **kwargs):
        from arkfbp import run_flow
        if self.flow_name is not None:
            outputs = run_flow(self.flow_name, self.get_inputs())
            return outputs

        return None

    def get_inputs(self):
        return None
