"""
Permission Core Nodes
"""
from arkfbp.executer import Executer
from arkfbp.node import FunctionNode
from common.django.app.automation.flows.modeling import get_api_config, get_permission, API_PERMISSION, set_flow_debug

# Editor your node here.


class QuerysetCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        queryset = self.flow.get_queryset()
        return queryset
