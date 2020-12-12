"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode


class RendererCore(FunctionNode):
    """Render response to HttpResponse

    The input is a Drf Response instance here.
    And the output will be an HttpResponse
    """
    def run(self, *args, **kwargs):
        # the inputs is an Drf Response Here.
        #
        request = self.flow.request
        response = self.flow.finalize_response(request, self.inputs, *args, **kwargs)

        return response
