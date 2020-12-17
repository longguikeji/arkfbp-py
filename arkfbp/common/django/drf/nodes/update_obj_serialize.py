"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode
from rest_framework.response import Response


class UpdateObjSerializerCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        obj = self.inputs
        serializer_cls = self.flow.get_serializer_class()
        srl = serializer_cls(obj, data=self.flow.request.data, partial=True)
        srl.is_valid(raise_exception=True)
        srl.save()
        return Response(srl.data)
