import numpy as np

"""Расчет энтропии Шеннона."""
def calculate_entropy(data_bytes):
    if len(data_bytes) == 0:
        return 0.0
    counts = np.bincount(bytearray(data_bytes), minlength=256)
    probabilities = counts / len(data_bytes)
    probabilities = probabilities[probabilities > 0]
    return float(-np.sum(probabilities * np.log2(probabilities)))

"""Расчет коэффициента корреляции Пирсона между соседними пикселями."""
def calculate_correlation(image_array, direction='horizontal', sample_size=5000):
    if direction == 'horizontal':
        x = image_array[:, :-1].flatten()
        y = image_array[:, 1:].flatten()
    else:
        x = image_array[:-1, :].flatten()
        y = image_array[1:, :].flatten()

    if len(x) > sample_size:
        idx = np.random.choice(len(x), sample_size, replace=False)
        x = x[idx]
        y = y[idx]

    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])

"""Расчет метрик NPCR и UACI для оценки чувствительности к ключу."""
def calculate_npcr_uaci(c1_bytes, c2_bytes):
    arr1 = np.frombuffer(c1_bytes, dtype=np.uint8)
    arr2 = np.frombuffer(c2_bytes, dtype=np.uint8)

    not_equal = arr1 != arr2
    npcr = np.sum(not_equal) / len(arr1) * 100.0
    uaci = np.sum(np.abs(arr1.astype(np.float64) - arr2.astype(np.float64))) / (255.0 * len(arr1)) * 100.0

    return float(npcr), float(uaci)