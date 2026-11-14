import os
import json
import csv
import hashlib
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

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

    # Замечание 3 список изображений разного типа для эксперимента
    image_names = ["akashi.png", "gradient.png"]

    for img_name in image_names:
        img_path = os.path.join(IMG_DIR, img_name)
        if not os.path.exists(img_path):
            print(f"⚠️ Файл {img_path} не найден, пропускаем...")
            continue

        print(f"\n==========================================")
        print(f"📁 Обработка изображения: {img_name}")
        print(f"==========================================\n")

        # Загрузка и подготовка (256x256, оттенки серого)
        orig_pil = Image.open(img_path).convert("L").resize((256, 256))
        orig_arr = np.array(orig_pil, dtype=np.uint8)
        orig_bytes = orig_arr.tobytes()

        # Замечание 4 проверка SHA-256
        orig_sha = compute_sha256(orig_bytes)
        print(f"🔒 SHA-256 исходного файла: {orig_sha}")

        xor_key = 135792468
        aes_key = b'0123456789abcdef'

        # 1. Потоковый XOR (шифрование и расшифрование)
        enc_xor = encrypt_xor(orig_bytes, xor_key)
        dec_xor = decrypt_xor(enc_xor, xor_key)
        dec_xor_sha = compute_sha256(dec_xor)
        assert dec_xor == orig_bytes and dec_xor_sha == orig_sha, "Ошибка обратимости XOR!"

        # 2. AES-ECB (шифрование и расшифрование)
        enc_ecb = encrypt_aes_ecb(orig_bytes, aes_key)
        dec_ecb = decrypt_aes_ecb(enc_ecb, aes_key, len(orig_bytes))
        dec_ecb_sha = compute_sha256(dec_ecb)
        assert dec_ecb == orig_bytes and dec_ecb_sha == orig_sha, "Ошибка обратимости AES-ECB!"

        # 3. AES-CTR (шифрование и расшифрование)
        enc_ctr, nonce = encrypt_aes_ctr(orig_bytes, aes_key)
        dec_ctr = decrypt_aes_ctr(enc_ctr, aes_key, nonce)
        dec_ctr_sha = compute_sha256(dec_ctr)
        assert dec_ctr == orig_bytes and dec_ctr_sha == orig_sha, "Ошибка обратимости AES-CTR!"

        print(f"✓ Обратимость подтверждена через SHA-256 (хэш совпал: {dec_ctr_sha[:16]}...)")

        # Корректное сохранение зашифрованных изображений с учетом padding для ECB
        h, w = orig_arr.shape
        base_prefix = os.path.splitext(img_name)[0]

        def save_encrypted_img(b_data, width, height, filename):
            target_size = width * height
            # Если байтов больше (из-за padding в ECB) берем ровно target_size
            # или дополняем нулями если меньше
            if len(b_data) >= target_size:
                arr_bytes = b_data[:target_size]
            else:
                arr_bytes = b_data + b'\x00' * (target_size - len(b_data))

            arr = np.frombuffer(arr_bytes, dtype=np.uint8).reshape((height, width))
            Image.fromarray(arr).save(os.path.join(IMG_DIR, f"{base_prefix}_{filename}"))

        # Сохраняем зашифрованные
        save_encrypted_img(enc_xor, w, h, "enc_xor.png")
        save_encrypted_img(enc_ecb, w, h, "enc_ecb.png")  # Теперь ECB сохраняется корректно
        save_encrypted_img(enc_ctr, w, h, "enc_ctr.png")

        # Расшифрованные сохраняем стандартно по исходной длине
        def save_decrypted_img(b_data, width, height, filename):
            arr = np.frombuffer(b_data[:width * height], dtype=np.uint8).reshape((height, width))
            Image.fromarray(arr).save(os.path.join(IMG_DIR, f"{base_prefix}_{filename}"))

        save_decrypted_img(dec_xor, w, h, "dec_xor.png")
        save_decrypted_img(dec_ecb, w, h, "dec_ecb.png")
        save_decrypted_img(dec_ctr, w, h, "dec_ctr.png")

        methods_data = {
            "Исходное": orig_bytes,
            "Потоковый XOR": enc_xor,
            "AES-ECB": enc_ecb,
            "AES-CTR": enc_ctr
        }

        # Расчет метрик
        print(f"\n--- Метрики для {img_name} ---")
        print(f"{'Метод':<15} | {'Энтропия':<10} | {'Corr H':<10} | {'Corr V':<10}")
        print("-" * 53)

        metrics_rows = []
        for name, data in methods_data.items():
            entropy = calculate_entropy(data)
            arr_corr = np.frombuffer(data[:w * h], dtype=np.uint8).reshape((h, w))
            corr_h = calculate_correlation(arr_corr, 'horizontal')
            corr_v = calculate_correlation(arr_corr, 'vertical')
            metrics_rows.append((name, entropy, corr_h, corr_v))
            print(f"{name:<15} | {entropy:<10.4f} | {corr_h:<10.4f} | {corr_v:<10.4f}")

        # Сохранение сводной таблицы для gradient.png в results/
        if img_name == "akashi.png":
            with open(os.path.join(RESULTS_DIR, "metrics.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Метод", "Энтропия", "Corr H", "Corr V"])
                writer.writerows(metrics_rows)

            # Гистограммы
            plt.figure(figsize=(12, 8))
            for i, (name, data) in enumerate(methods_data.items(), 1):
                plt.subplot(2, 2, i)
                arr = np.frombuffer(data[:w * h], dtype=np.uint8)
                plt.hist(arr, bins=256, range=(0, 256), color='skyblue', edgecolor='none', alpha=0.9)
                plt.title(f"Гистограмма: {name}")
                plt.xlabel("Значение байта")
                plt.ylabel("Частота")
            plt.tight_layout()
            plt.savefig(os.path.join(RESULTS_DIR, "histograms.png"))
            plt.close()

        # Замечание 1 корректный тест лавинного эффекта с фиксированным nonce
        aes_key_changed = aes_key[:-1] + b'X'
        cipher1 = AES.new(aes_key, AES.MODE_CTR, nonce=nonce)
        c1 = cipher1.encrypt(orig_bytes)

        cipher2 = AES.new(aes_key_changed, AES.MODE_CTR, nonce=nonce)
        c2 = cipher2.encrypt(orig_bytes)

        npcr, uaci = calculate_npcr_uaci(c1, c2)
        print(f"\nЛавинный тест (AES-CTR с фиксированным nonce):")
        print(f"NPCR = {npcr:.2f}%")
        print(f"UACI = {uaci:.2f}%")

        meta = {
            "algorithm": "aes-ctr",
            "source": img_name,
            "nonce": nonce.hex(),
            "npcr": npcr,
            "uaci": uaci
        }
        with open(os.path.join(RESULTS_DIR, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)

    print("\n🎉 Все эксперименты завершены.")


if __name__ == "__main__":
    run_experiment()
