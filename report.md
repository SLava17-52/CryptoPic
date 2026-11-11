# Отчет

## 1. Постановка задачи

## Какие методы реализованы:

1)Потоковый XOR

2)Блочный шифр AES-ECB

3)Режим AES-CTR
    
## Какие изображения использовались: 
`gradient.png` , `checkerboard.png` и пользовательское изображение `akashi.png` (разрешение 256×256, оттенки серого).

## Что именно сравнивалось: 
энтропия распределения байтов, коэффициенты корреляции соседних пикселей (по горизонтали и вертикали), гистограммы распределения яркостей, а также чувствительность к изменению ключа (метрики NPCR и UACI).

## 2. Реализация

- Потоковый XOR: Ключ (`int`) инициализирует внутреннее состояние генератора `xorshift32`, который выдает гамму. Наложение происходит побайтово через операцию `XOR`:
  ```
  def xorshift32(seed, length):
      x = seed & 0xFFFFFFFF
      if x == 0: x = 1
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
  ```

- Как выполняется AES: Для режима ECB используется PKCS7-паддинг, для режима CTR — динамический счетчик:

```
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def encrypt_aes_ecb(data_bytes, key_bytes):
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    return cipher.encrypt(pad(data_bytes, AES.block_size))

def encrypt_aes_ctr(data_bytes, key_bytes):
    cipher = AES.new(key_bytes, AES.MODE_CTR)
    ciphertext = cipher.encrypt(data_bytes)
    return ciphertext, cipher.nonce  
```

Как хранятся IV/nonce: Уникальный вектор nonce сохраняется в файл метаданных results/meta.json в формате hex:
```
meta = {
    "algorithm": "aes-ctr",
    "source": "gradient.png",
    "nonce": nonce.hex(),
    "npcr": npcr,
    "uaci": uaci
}
```
Как проверяется обратимость: Сравнение исходных и расшифрованных байтов через криптографический хэш SHA-256:
```
import hashlib

def compute_sha256(data_bytes):
    return hashlib.sha256(data_bytes).hexdigest()

# Проверка:
assert compute_sha256(decrypted_bytes) == compute_sha256(original_bytes)
```

## 3. Методика эксперимента 
- Основное изображение: 
akashi.png

- Рассчитываемые метрики: 
энтропия Шеннона (H), коэффициент корреляции Пирсона для соседних пикселей.

- Объем выборки для корреляции: 
случайная выборка из N = 5000 пар соседних пикселей для горизонтального и вертикального направлений.

- Эксперимент с ключом: 
изменение одного байта в ключе AES-CTR с последующим расчетом метрик лавинного эффекта NPCR (процент изменившихся пикселей) и UACI (средняя интенсивность изменения).

```
import numpy as np

Вычисление энтропии Шеннона 

def calculate_entropy(data_bytes):
    if len(data_bytes) == 0:
        return 0.0
    counts = np.bincount(bytearray(data_bytes), minlength=256)
    probabilities = counts / len(data_bytes)
    probabilities = probabilities[probabilities > 0]
    return float(-np.sum(probabilities * np.log2(probabilities)))

Расчет коэффициента корреляции Пирсона 

def calculate_correlation(image_array, direction='horizontal', sample_size=5000):
    if direction == 'horizontal':
        x = image_array[:, :-1].flatten()
        y = image_array[:, 1:].flatten()
    else:  # vertical
        x = image_array[:-1, :].flatten()
        y = image_array[1:, :].flatten()
    
    if len(x) > sample_size:
        idx = np.random.choice(len(x), sample_size, replace=False)
        x = x[idx]
        y = y[idx]
        
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])

Расчет метрик NPCR и UACI для оценки чувствительности к изменению ключа

def calculate_npcr_uaci(c1_bytes, c2_bytes):
    arr1 = np.frombuffer(c1_bytes, dtype=np.uint8)
    arr2 = np.frombuffer(c2_bytes, dtype=np.uint8)
    
    # NPCR 
    not_equal = arr1 != arr2
    npcr = np.sum(not_equal) / len(arr1) * 100.0
    
    # UACI 
    uaci = np.sum(np.abs(arr1.astype(np.float64) - arr2.astype(np.float64))) / (255.0 * len(arr1)) * 100.0
    
    return float(npcr), float(uaci)
```

4. Результаты
