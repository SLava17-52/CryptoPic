# CryptoPic — Шифрование изображений и статистическое сравнение

Лабораторная работа по исследованию и статистическому сравнению методов симметричного шифрования изображений.

## Зависимости
Для запуска проекта требуются следующие библиотеки Python:
- `Python` 3.8+
- `Pillow` (работа с изображениями)
- `numpy` (математические и матричные операции)
- `matplotlib` (построение гистограмм)
- `pycryptodome` (реализация криптографических алгоритмов AES)

Установка зависимостей:
```bash
pip install -r requirements.txt
```

# Какие алгоритмы реализованы:

1)Потоковый XOR на базе псевдослучайного генератора xorshift32.

2)AES-ECB .

3)AES-CTR .


# Команда запуска
```
python src/main.py
```
# Пример шифрования

```
from crypto import encrypt_xor, encrypt_aes_ecb, encrypt_aes_ctr

with open("imgs/akashi.png", "rb") as f:
    image_bytes = f.read()

# 1. Потоковый XOR
cipher_xor = encrypt_xor(image_bytes, key_int=135792468)

# 2. AES-ECB
aes_key = b'0123456789abcdef'
cipher_ecb = encrypt_aes_ecb(image_bytes, aes_key)

# 3. AES-CTR
cipher_ctr, nonce = encrypt_aes_ctr(image_bytes, aes_key)
```
# Пример расшифрования
```
from crypto import decrypt_xor, decrypt_aes_ecb, decrypt_aes_ctr, compute_sha256

# 1. Расшифрование XOR
plain_xor = decrypt_xor(cipher_xor, key_int=135792468)

# 2. Расшифрование AES-ECB 
plain_ecb = decrypt_aes_ecb(cipher_ecb, aes_key, original_len=len(image_bytes))

# 3. Расшифрование AES-CTR 
plain_ctr = decrypt_aes_ctr(cipher_ctr, aes_key, nonce=nonce)

```
