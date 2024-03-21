import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

class AES_cipher:
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode())).decode('utf-8')

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]

# Example usage:
#crypto = AESCipher("9cecc06621b370151c78f667543ae01e1b20285611425197f6e3449f8a056b60")
#encrypted_text = crypto.encrypt('Hello, World!')
#print("Encrypted:", encrypted_text)
#decrypted_text = crypto.decrypt(encrypted_text)
#print("Decrypted:", decrypted_text)
