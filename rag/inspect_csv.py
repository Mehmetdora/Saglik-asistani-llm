import pandas as pd
from pathlib import Path


def inspect_csv(csv_path):

    # CSV'yi oku
    df = pd.read_csv(csv_path, encoding="utf-8")

    print(f"✅ Toplam satır: {len(df)}")
    print(f"📋 Sütunlar: {list(df.columns)}\n")

    # Her sütunun ilk değerini göster
    print("=" * 80)
    print("SÜTUN ÖRNEKLERİ:")
    print("=" * 80)

    for col in df.columns:
        sample = df[col].iloc[0] if not df[col].isna().all() else "BOŞ"
        # Uzun metinleri kısalt
        if isinstance(sample, str) and len(sample) > 100:
            sample = sample[:100] + "..."
        print(f"\n[{col}]:")
        print(f"  {sample}")

    print("\n" + "=" * 80)

    # Eksik veri analizi
    print("\n📉 Eksik Veri Analizi:")
    missing = df.isnull().sum()
    for col, count in missing.items():
        if count > 0:
            percentage = (count / len(df)) * 100
            print(f"  - {col}: {count} ({percentage:.1f}%)")

    # İlk 3 satırı göster
    print("\n" + "=" * 80)
    print("İLK 3 SATIR:")
    print("=" * 80)
    print(df.head(3).to_string())

    return df


if __name__ == "__main__":
    csv_path = Path("data/raw/hastaliklar_detayli_listesi.csv")

    if not csv_path.exists():
        print(f"❌ CSV bulunamadı: {csv_path}")
        print("Lütfen CSV dosyasını data/raw/ klasörüne koy")
    else:
        df = inspect_csv(csv_path)
