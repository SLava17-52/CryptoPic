import json
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
"""Генератор псевдослучайных чисел xorshift32 для потокового XOR."""
def xorshift32(seed, length):
    # ограничиваем состояние 32 битами
    x = seed & 0xFFFFFFFF
    # нулевое состояние для xorshift всегда дает 0, поэтому заменяем на 1
    if x == 0:
        x = 1
    keystream = bytearray()
    for _ in range(length):
       # три сдвигово xorшага обновляют внутреннее состояние PRNG
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        # берем младший байт как элемент потоковой гаммы
        keystream.append(x & 0xFF)
    return bytes(keystream)

def encrypt_xor(data_bytes, key_int):
    # потоковое шифрование: каждый байт данных складывается по XOR с гаммой
    keystream = xorshift32(key_int, len(data_bytes))
    return bytes(b1 ^ b2 for b1, b2 in zip(data_bytes, keystream))

def decrypt_xor(cipher_bytes, key_int):
    # для xor обратная операция совпадает с прямой: (P ^ K) ^ K = P
    eturn encrypt_xor(cipher_bytes, key_int)

def encrypt_aes_ecb(data_bytes, key_bytes):
   # ecb шифрует каждый 16-байтный блок независимо; нужен PKCS#7 padding до кратности 16 байт
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    padded_data = pad(data_bytes, AES.block_size)
    return cipher.encrypt(padded_data)

def decrypt_aes_ecb(ciphertext_bytes, key_bytes, original_len):
    # расшифровываем блоки, снимаем PKCS#7 padding и при необходимости обрезаем до исходной длины
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    decrypted_padded = cipher.decrypt(ciphertext_bytes)
    return unpad(decrypted_padded, AES.block_size)[:original_len]

def encrypt_aes_ctr(data_bytes, key_bytes):
    # ctr работает как потоковый шифр: шифруется счетчик с nonce, затем идет xor с данными
    cipher = AES.new(key_bytes, AES.MODE_CTR)
    ciphertext = cipher.encrypt(data_bytes)
    return ciphertext, cipher.nonce

def decrypt_aes_ctr(ciphertext_bytes, key_bytes, nonce):
    # передаем тот же nonce и ключ, чтобы сгенерировать идентичную гамму
    cipher = AES.new(key_bytes, AES.MODE_CTR, nonce=nonce)
    return cipher.decrypt(ciphertext_bytes)

def compute_sha256(data_bytes):
    # криптографический хэш для проверки целостности после расшифрования
    return hashlib.sha256(data_bytes).hexdigest()
