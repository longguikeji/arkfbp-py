import requests
from .base import Node

# api mode for requests
DIRECT_MODE = 'direct'
PROXY_MODE = 'proxy'

# request method
GET_METHOD = 'GET'
POST_METHOD = 'POST'
PUT_METHOD = 'PUT'
PATCH_METHOD = 'PATCH'
DELETE_METHOD = 'DELETE'
REQUEST_METHOD = [GET_METHOD, POST_METHOD, PUT_METHOD, PATCH_METHOD, DELETE_METHOD]

# APINode metadata
_NODE_NAME = 'api'
_NODE_KIND = 'api'


class APINode(Node):

    name = _NODE_NAME
    kind = _NODE_KIND
    url = ''
    mode = DIRECT_MODE
    method = GET_METHOD
    auth = None
    headers = None
    params = None
    json = True

    def __init__(self, *args, **kwargs):
        super(Node).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        if self.mode == DIRECT_MODE:
            return self._request_direct()

        elif self.mode == PROXY_MODE:
            return self._request_proxy()

    def _get_request_attr(self, name):
        if hasattr(self, 'get_' + name):
            return getattr(self, 'get_' + name)()
        if hasattr(self, name):
            return getattr(self, name)
        return exec(f'self.{name}')

    def _init_request_kwargs(self):
        kwargs = {}
        self.url = self._get_request_attr('url')
        self.auth = self._get_request_attr('auth')
        self.method = self._get_request_attr('method').upper()
        if self.method not in REQUEST_METHOD:
            raise Exception(f'Unknown request method,Please choose one in {REQUEST_METHOD}')
        self.params = self._get_request_attr('params')
        self.headers = self._get_request_attr('headers')

        if self.auth is not None:
            kwargs['auth'] = self.auth

        if self.params is not None:
            if self.method == GET_METHOD:
                kwargs['params'] = self.params
            else:
                if self.json is True:
                    kwargs['json'] = self.params
                else:
                    kwargs['data'] = self.params

        if self.headers is not None:
            kwargs['headers'] = self.headers
        return kwargs

    def _request_direct(self):
        response = None
        kwargs = self._init_request_kwargs()

        if self.method == GET_METHOD:
            response = requests.get(self.url, **kwargs)

        if self.method == POST_METHOD:
            response = requests.post(self.url, **kwargs)

        if self.method == PUT_METHOD:
            response = requests.put(self.url, **kwargs)

        if self.method == PATCH_METHOD:
            response = requests.patch(self.url, **kwargs)

        if self.method == DELETE_METHOD:
            response = requests.delete(self.url, **kwargs)

        response_content = response.content.decode()
        return response_content

    def _request_proxy(self):
        return None
