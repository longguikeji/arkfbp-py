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
        self.flow.format_kwarg = self.flow.get_format_suffix(**kwargs)

        # Perform content negotiation and store the accepted info on the request
        neg = self.flow.perform_content_negotiation(request)
        request.accepted_renderer, request.accepted_media_type = neg

        # Determine the API version, if versioning is in use.
        version, scheme = self.flow.determine_version(request, *args, **kwargs)
        request.version, request.versioning_scheme = version, scheme
        return None

