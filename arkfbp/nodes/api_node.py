import requests
from .base import Node


class APINode(Node):

    name = 'api'
    kind = 'api'

    mode = 'direct' # proxy

    url = ''
    method = 'GET'
    auth = None
    headers = None
    params = None
    json = True

    def run(self):
        if self.mode == 'direct':
            return self._request_direct()

        elif self.mode == 'proxy':
            return self._request_proxy()

    def _get_user_defined_attr(self, name):
        if hasattr(self, 'get_' + name):
            return getattr(self, 'get_' + name)()

        if hasattr(self, name):
            return getattr(self, name)

        return None

    def _request_direct(self):
        kwargs = {}

        url = self._get_user_defined_attr('url')
        auth = self._get_user_defined_attr('auth')
        method = self._get_user_defined_attr('method')
        if method is not None:
            method = method.upper()

        params = self._get_user_defined_attr('params')
        headers = self._get_user_defined_attr('headers')

        if auth is not None:
            kwargs['auth'] = self.auth

        if params is not None:
            if method == 'GET':
                kwargs['params'] = params
            else:
                if self.json is True:
                    kwargs['json'] = params
                else:
                    kwargs['data'] = params

        if headers is not None:
            kwargs['headers'] = headers

        if method == 'GET':
            res = requests.get(url, **kwargs)
            return res.json()

        elif method == 'POST':
            res = requests.post(url, **kwargs)
            return res.json()

    def _request_proxy(self):
        return None