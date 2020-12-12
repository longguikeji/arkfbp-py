"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode
from rest_framework.response import Response


class GetObjectCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        """获取该请求指向的数据实体。
        inputs: None
        outputs: Model instance
        """
        return self.flow.get_object()

