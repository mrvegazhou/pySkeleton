# -*- coding: utf-8 -*-
from Crypto.Cipher import AES
from Crypto import Random
import base64
class MyCrypt():

    def __init__(self, key):
        self.bs = 32
        if len(key) >= 32:
            self.key = key[:32]
        else:
            self.key = self._pad(key)

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]

if __name__ == '__main__':
    import sys
    key = '1234567890abcdef'
    data = '{"a": "123中文", sss} '
    ec = MyCrypt(key)
    encrpt_data = ec.encrypt(data)
    decrpt_data = ec.decrypt(encrpt_data)
    print encrpt_data, decrpt_data, decrpt_data == data

    from base64 import b64encode, b64decode
    print b64encode(encrpt_data)