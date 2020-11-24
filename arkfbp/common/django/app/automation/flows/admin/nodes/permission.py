"""
Permission Core Nodes
"""
from arkfbp.common.django.app.automation.flows.modeling import get_api_config
from arkfbp.executer import Executer
from arkfbp.node import FunctionNode
from arkfbp.utils.util import get_class_from_path

# Editor your node here.


class PermissionCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        _, api_detail = get_api_config(self.inputs.method, self.flow.api_config)
        roles = self.flow.config.get('role')
        permissions = api_detail.get('permission', [])
        for permission in permissions:
            detail = roles.get(permission)
            flow = get_class_from_path(f"{detail.get('flow')}.main.Main")
            ret = Executer.start_flow(flow(), self.inputs, *args, **kwargs)
            if not ret:
                return self.flow.shutdown({'error': 'permission denied'}, response_status=403)

        return self.inputs
