import os
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import json
import csv

from crypto import (
    encrypt_xor, decrypt_xor,
    encrypt_aes_ecb, decrypt_aes_ecb,
    encrypt_aes_ctr, decrypt_aes_ctr,
    compute_sha256
)
from metrics import calculate_entropy, calculate_correlation, calculate_npcr_uaci


def run_experiment():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RESULTS_DIR = os.path.join(BASE_DIR, "results")
    IMG_DIR = os.path.join(BASE_DIR, "imgs")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)

    # изображение для статистического анализа
    img_name = "akashi.png"
    img_path = os.path.join(IMG_DIR, img_name)

    if not os.path.exists(img_path):
        print(f"Ошибка: файл {img_path} не найден! Поместите изображения в папку imgs/")
        return

    orig_pil = Image.open(img_path).convert("L").resize((256, 256))
    orig_arr = np.array(orig_pil, dtype=np.uint8)
    orig_bytes = orig_arr.tobytes()
    orig_sha = compute_sha256(orig_bytes)

    print(f"=== Анализ изображения: {img_name} ===")
    print(f"SHA-256 исходного файла: {orig_sha}")

    xor_key = 135792468
    aes_key = b'0123456789abcdef'  # 16 байт

    # Потоковый XOR (шифрование и расшифрование)
    enc_xor = encrypt_xor(orig_bytes, xor_key)
    dec_xor = decrypt_xor(enc_xor, xor_key)
    assert dec_xor == orig_bytes, "Ошибка обратимости XOR!"

    # 2. AES-ECB (шифрование и расшифрование)
    enc_ecb = encrypt_aes_ecb(orig_bytes, aes_key)
    dec_ecb = decrypt_aes_ecb(enc_ecb, aes_key, len(orig_bytes))
    assert dec_ecb == orig_bytes, "Ошибка обратимости AES-ECB!"

    # 3. AES-CTR (шифрование и расшифрование)
    enc_ctr, nonce = encrypt_aes_ctr(orig_bytes, aes_key)
    dec_ctr = decrypt_aes_ctr(enc_ctr, aes_key, nonce)
    assert dec_ctr == orig_bytes, "Ошибка обратимости AES-CTR!"

    print("✓ Обратимость всех методов успешно подтверждена (SHA-256 совпадает).")

    # Сохранение зашифрованных и расшифрованных картинок
    h, w = orig_arr.shape

    def save_bytes_as_img(b_data, width, height, filename):
        arr = np.frombuffer(b_data[:width * height], dtype=np.uint8).reshape((height, width))
        Image.fromarray(arr).save(os.path.join(IMG_DIR, filename))

    # Сохраняем зашифрованные
    save_bytes_as_img(enc_xor, w, h, "enc_xor.png")
    save_bytes_as_img(enc_ecb, w, h, "enc_ecb.png")
    save_bytes_as_img(enc_ctr, w, h, "enc_ctr.png")

    # Сохраняем расшифрованные
    save_bytes_as_img(dec_xor, w, h, "dec_xor.png")
    save_bytes_as_img(dec_ecb, w, h, "dec_ecb.png")
    save_bytes_as_img(dec_ctr, w, h, "dec_ctr.png")

    print("✓ Зашифрованные и расшифрованные (dec) изображения успешно сохранены в папку imgs/")

    methods_data = {
        "Исходное": orig_bytes,
        "Потоковый XOR": enc_xor,
        "AES-ECB": enc_ecb,
        "AES-CTR": enc_ctr
    }

    # Расчет метрик
    print("\n--- Сводные метрики ---")
    print(f"{'Метод':<15} | {'Энтропия':<10} | {'Corr H':<10} | {'Corr V':<10}")
    print("-" * 53)

    metrics_rows = []
    for name, data in methods_data.items():
        entropy = calculate_entropy(data)
        arr_for_corr = np.frombuffer(data[:w * h], dtype=np.uint8).reshape((h, w))
        corr_h = calculate_correlation(arr_for_corr, 'horizontal')
        corr_v = calculate_correlation(arr_for_corr, 'vertical')

        metrics_rows.append((name, entropy, corr_h, corr_v))
        print(f"{name:<15} | {entropy:<10.4f} | {corr_h:<10.4f} | {corr_v:<10.4f}")

    # Сохранение таблицы в CSV
    csv_path = os.path.join(RESULTS_DIR, "metrics.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Метод", "Энтропия", "Corr H", "Corr V"])
        writer.writerows(metrics_rows)

    # Построение гистограмм
    plt.figure(figsize=(12, 8))
    for i, (name, data) in enumerate(methods_data.items(), 1):
        plt.subplot(2, 2, i)
        arr = np.frombuffer(data[:w * h], dtype=np.uint8)
        plt.hist(arr, bins=256, range=(0, 256), color='blue', edgecolor='none', alpha=0.9)
        plt.title(f"Гистограмма: {name}")
        plt.xlabel("Значение байта")
        plt.ylabel("Частота")
    plt.tight_layout()

    hist_path = os.path.join(RESULTS_DIR, "histograms.png")
    plt.savefig(hist_path)
    plt.close()
    print(f"✓ Гистограммы сохранены в {hist_path}")

    # Лавинный эффект (NPCR / UACI)
    aes_key_changed = aes_key[:-1] + b'X'
    enc_ctr_2, _ = encrypt_aes_ctr(orig_bytes, aes_key_changed)
    npcr, uaci = calculate_npcr_uaci(enc_ctr, enc_ctr_2)

    print(f"\nЛавинный эффект (AES-CTR при изменении 1 байта ключа):")
    print(f"NPCR = {npcr:.2f}%")
    print(f"UACI = {uaci:.2f}%")

    # Сохранение meta.json
    meta = {
        "algorithm": "aes-ctr",
        "source": img_name,
        "nonce": nonce.hex(),
        "npcr": npcr,
        "uaci": uaci
    }
    meta_path = os.path.join(RESULTS_DIR, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
    print(f"✓ Метаданные сохранены в {meta_path}")


if __name__ == "__main__":
    run_experiment()