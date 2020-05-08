from .base import Node


class TriggerFlowNode(Node):

    name = 'trigger_flow'
    kind = 'trigger_flow'

    flowname = None

    def run(self):
        from arkfbp import run_flow
        if self.flowname is not None:
            outputs = run_flow(self.flowname, self.get_inputs())
            return outputs

        return None

    def get_inputs(self):
        return None