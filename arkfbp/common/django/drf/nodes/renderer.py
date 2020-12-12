"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode
from rest_framework.response import Response


class RendererCore(FunctionNode):
    """Render response to HttpResponse

    The input is a Drf Response instance here.
    And the output will be an HttpResponse
    """
    def run(self, *args, **kwargs):
        # the inputs is an Drf Response Here.
        #
        assert isinstance(self.inputs, Response), 'Require Response instance as inputs'
        request = self.flow.request

        response = self.flow.finalize_response(request, self.inputs, *args, **kwargs)

        return response
