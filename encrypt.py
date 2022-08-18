import base64
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def random_seq(len):
    res = ''
    chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
    for i in range(len):
        res += random.choice(chars)
    return res.encode('utf-8')

def AESencrypt(password, salt):
    # salt = salt.encode('utf-8')
    iv = random_seq(16)
    plain_text = pad(random_seq(64) + password.encode('utf-8'), 16, 'pkcs7')
    aes = AES.new(salt.encode('utf-8'), AES.MODE_CBC, iv)
    cipher_text = aes.encrypt(plain_text)
    res = base64.b64encode(cipher_text).decode('utf-8')
    print("加密后: " , res)
    return res
