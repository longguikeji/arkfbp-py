"""
Permission Core Nodes
"""
from arkfbp.executer import Executer
from arkfbp.node import FunctionNode
from ...modeling import get_api_config, get_permission, API_PERMISSION, set_flow_debug

# Editor your node here.


class QuerysetCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        print()
        print('Hello this is the new line!!!')
        print()
        return self.inputs
