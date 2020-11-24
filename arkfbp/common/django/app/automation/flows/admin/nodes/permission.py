"""
Permission Core Nodes
"""
from arkfbp.executer import Executer
from arkfbp.node import FunctionNode
from ...modeling import get_api_config, get_permission, API_PERMISSION, set_flow_debug

# Editor your node here.


class PermissionCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        _, api_detail = get_api_config(self.inputs.method, self.flow.api_config)
        permissions = get_permission(api_detail.get(API_PERMISSION, []), self.flow.config)

        for flow in permissions:
            _flow = flow()
            set_flow_debug(_flow, api_detail)

            ret = Executer.start_flow(_flow, self.inputs, *args, **kwargs)
            if not ret:
                return self.flow.shutdown({'error': 'permission denied'}, response_status=403)

        return self.inputs
