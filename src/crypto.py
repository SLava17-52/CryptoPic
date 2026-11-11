import json
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
"""Генератор псевдослучайных чисел xorshift32 для потокового XOR."""
def xorshift32(seed, length):
    x = seed & 0xFFFFFFFF
    if x == 0:
        x = 1
    keystream = bytearray()
    for _ in range(length):
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        keystream.append(x & 0xFF)
    return bytes(keystream)

def encrypt_xor(data_bytes, key_int):
    keystream = xorshift32(key_int, len(data_bytes))
    return bytes(b1 ^ b2 for b1, b2 in zip(data_bytes, keystream))

def decrypt_xor(cipher_bytes, key_int):
    return encrypt_xor(cipher_bytes, key_int)

def encrypt_aes_ecb(data_bytes, key_bytes):
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    padded_data = pad(data_bytes, AES.block_size)
    return cipher.encrypt(padded_data)

def decrypt_aes_ecb(ciphertext_bytes, key_bytes, original_len):
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    decrypted_padded = cipher.decrypt(ciphertext_bytes)
    return unpad(decrypted_padded, AES.block_size)[:original_len]

def encrypt_aes_ctr(data_bytes, key_bytes):
    cipher = AES.new(key_bytes, AES.MODE_CTR)
    ciphertext = cipher.encrypt(data_bytes)
    return ciphertext, cipher.nonce

def decrypt_aes_ctr(ciphertext_bytes, key_bytes, nonce):
    cipher = AES.new(key_bytes, AES.MODE_CTR, nonce=nonce)
    return cipher.decrypt(ciphertext_bytes)

def compute_sha256(data_bytes):
    return hashlib.sha256(data_bytes).hexdigest()