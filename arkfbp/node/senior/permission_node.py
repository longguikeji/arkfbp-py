"""
Permission Node.
"""
from arkfbp.node import FunctionNode

_NODE_NAME = 'permission'
_NODE_KIND = 'permission'


class PermissionNode(FunctionNode):
    """
    Permission Node.
    """
    name = _NODE_NAME
    kind = _NODE_KIND

    def run(self, *args, **kwargs):
        if self.has_permission():
            return self.inputs
        return self.flow.shutdown({'error': 'permission denied'}, response_status=403)

    # pylint: disable=unused-argument, no-self-use
    def has_permission(self, *args, **kwargs):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True
