from typing import TextIO, BinaryIO
from io import StringIO, BytesIO
from urllib.parse import quote_plus
import warnings

from xq.algorithms import Encryption
from xq.exceptions import SDKEncryptionException


class OTPEncryption(Encryption):
    """OTP implimented encryption algorithm

    :param Encryption: Inherited Parent class
    :type Encryption: Encryption class
    """

    def __init__(self, key: bytes, max_encryption_chunk_size=2048):
        """Initialize OTPEncryption class with an encryption key

        :param key: encryption key
        :type key: bytes
        :param max_encryption_chunk_size: the maximum byte chunk for encryption, defaults to 2048
        :type max_encryption_chunk_size: int, optional
        """
        self.max_encryption_chunk_size = max_encryption_chunk_size
        key_string = key if isinstance(key, str) else key.decode()
        self.expandedKey = self.expandKey(
            key_string, self.max_encryption_chunk_size
        ).encode()

        Encryption.__init__(self, key)

        if self.expandedKey != self.originalKey:
            warnings.warn(
                "The provided key was expanded!  Make sure you save your reference of `Encryption.key`. i.e. `newKey = EncryptionObj.key`"
            )

    def xor_bytes(self, key: bytes, text: bytes):
        """xor the provided text to key bytes
        * replicated from jssdk-core

        :param key: encryption key
        :type key: bytes
        :param text: text to encrypt
        :type text: bytes
        :return: padded text bytes
        :rtype: bytes
        """
        return bytes([text[i] ^ key[i] for i in range(len(text))])

    def xor_chunker(self, text):
        """break text into maximum sized chunks, encrypt, and join

        :param text: text to encrypt
        :type text: bytes
        :return: encrypted bytes
        :rtype: bytes
        """
        b: bytes = b""
        for textChunk in [
            text[i : i + self.max_encryption_chunk_size]
            for i in range(0, len(text), self.max_encryption_chunk_size)
        ]:
            b = b + self.xor_bytes(self.key, textChunk)
        return b

    def encrypt(self, msg):
        """encryption method for encrypting a string or file

        :param msg: message to encrypt
        :type msg: str OR FileLike
        :raises SDKEncryptionException: unsupported message type
        :return: encrypted message
        :rtype: bytes
        """
        if isinstance(msg, str):
            # string support
            text = msg.encode()
        elif isinstance(msg, TextIO) or isinstance(msg, StringIO):
            # string file
            text = msg.getvalue().encode()
        elif isinstance(msg, BinaryIO) or isinstance(msg, BytesIO):
            # binary file
            text = msg.getvalue()
        else:
            raise SDKEncryptionException(f"Message type {type(msg)} is not supported!")

        return self.xor_chunker(text)

    def decrypt(self, text: bytes):
        """decryption method for decrypting a string or file

        :param text: text to decrypt
        :type text: bytes
        :return: decrypted text
        :rtype: str
        """
        return self.xor_chunker(text).decode()
