"""
Permission Core Nodes
"""
from arkfbp.node import FunctionNode


class InitRequestCore(FunctionNode):
    """
    permission core node.
    """
    def run(self, *args, **kwargs):
        req = self.flow.request
        request = self.flow.initialize_request(req, *args, **kwargs)
        self.flow.request = request
        self.flow.headers = self.flow.default_response_headers
        return None

