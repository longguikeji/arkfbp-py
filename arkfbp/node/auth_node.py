"""
Auth Node
"""
from .function_node import FunctionNode

# AuthTokenNode metadata
_NODE_NAME = 'auth_token'
_NODE_KIND = 'auth_token'


class AuthTokenNode(FunctionNode):
    """
    Auth Token Node
    """
    name = _NODE_NAME
    kind = _NODE_KIND
    web_framework = 'django'

    def run(self, *args, **kwargs):
        """
        run node
        """
        # pylint: disable=unused-variable
        username, password = self.get_credentials(kwargs.get('username_field', None),
                                                  kwargs.get('password_field', None))
        cipher = self.get_cipher()
        self.verify_password(password, cipher)

    def get_credentials(self, username_field=None, password_field=None):
        """
        get credentials
        """
        # 获取request的框架信息
        web_framework = self.web_framework
        # 获取username和password
        if web_framework.lower() == 'django':
            username = self.inputs.ds.get(username_field or 'username', None)
            password = self.inputs.ds.get(password_field or 'password', None)
            if username is None or password is None:
                self.flow.shutdown({'detail': '身份认证信息无效'}, response_status=400)
            return username, password
        self.flow.shutdown({'detail': '无法获取身份认证信息'}, response_status=400)

    def verify_password(self, plaintext, cipher):
        """
        verify password
        """
        # 通过配置的加密方式验证密码

    # pylint: disable=no-self-use
    def get_cipher(self):
        """override by subclass"""
        raise NotImplementedError
