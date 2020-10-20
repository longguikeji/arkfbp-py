"""
Auth Node
"""
import binascii
import os

from passlib.hash import (
    ldap_md5,
    ldap_sha1,
    ldap_salted_md5,
    ldap_salted_sha1,
)
from ..function_node import FunctionNode

# AuthTokenNode metadata
_NODE_NAME = 'auth_token'
_NODE_KIND = 'auth_token'
_USERNAME = 'username'
_PASSWORD = 'password'
_ENCRYPTION = ('SSHA', 'SMD5', 'MD5', 'SHA')


class AuthTokenNode(FunctionNode):
    """
    Auth Token Node.
    Used for authentication of WEB projects.
    """
    name = _NODE_NAME
    kind = _NODE_KIND
    username_field = None
    password_field = None
    encryption = _ENCRYPTION[0]

    def run(self, *args, **kwargs):
        """
        run node.
        """
        # pylint: disable=unused-variable
        username, password = self.get_credentials(
            self.username_field or _USERNAME,
            self.password_field or _PASSWORD,
        )
        ciphertext = self.get_ciphertext()
        if not self.verify_password(password, ciphertext):
            return self.flow.shutdown({'detail': '身份认证信息无效'}, response_status=400)
        return self.get_key()

    def get_credentials(self, username_field=None, password_field=None):
        """
        get credentials.
        """
        username = self.inputs.ds.get(username_field or 'username', None)
        password = self.inputs.ds.get(password_field or 'password', None)
        if username is None or password is None:
            self.flow.shutdown({'detail': '身份认证信息缺失'}, response_status=400)
        return username, password

    def verify_password(self, plaintext, ciphertext):
        """
        verify password.
        """
        if plaintext is None or ciphertext is None:
            return False

        self.valid_encryption()
        if ciphertext.startswith('{SSHA}'):
            return ldap_salted_sha1.verify(plaintext, ciphertext)

        if ciphertext.startswith('{SMD5}'):
            return ldap_salted_md5.verify(plaintext, ciphertext)

        if ciphertext.startswith('{MD5}'):
            return ldap_md5.verify(plaintext, ciphertext)

        if ciphertext.startswith('{SHA}'):
            return ldap_sha1.verify(plaintext, ciphertext)

        return False

    def encrypt_password(self, plaintext):
        """
        encrypt password.
        """
        self.valid_encryption()
        # 加密密码
        if self.encryption == 'SSHA':
            return ldap_salted_sha1.hash(plaintext)

        if self.encryption == 'SMD5':
            return ldap_salted_md5.hash(plaintext)

        if self.encryption == 'MD5':
            return ldap_md5.hash(plaintext)

        if self.encryption == 'SHA':
            return ldap_sha1.hash(plaintext)

        raise ValueError("encryption must be one of 'SSHA', 'SMD5', 'SHA', 'MD5'")

    def valid_encryption(self):
        """
        valid AuthTokenNode encryption.
        """
        if self.encryption not in _ENCRYPTION:
            raise ValueError("encryption must be one of 'SSHA', 'SMD5', 'SHA', 'MD5'")

    def get_key(self):
        """
        override by subclass.
        """
        return self.generate_key()

    @staticmethod
    def generate_key():
        """
        it can be overridden by subclass.
        """
        return binascii.hexlify(os.urandom(20)).decode()

    # pylint: disable=no-self-use
    def get_ciphertext(self):
        """
        override by subclass.
        """
        raise NotImplementedError
