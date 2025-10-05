"""
CSV verisini yükle ve RAG için hazırla
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict


class DiseaseDataLoader:

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.processed_data = []

    def load_csv(self):
        """CSV'yi oku"""
        print(f"📂 CSV yükleniyor: {self.csv_path}")

        try:
            self.df = pd.read_csv(self.csv_path, encoding="utf-8")
            print(f"✅ {len(self.df)} satır yüklendi")
            return True
        except Exception as e:
            print(f"❌ Hata: {e}")
            return False

    def process_diseases(self):
        """Her hastalığı RAG için uygun formata çevir"""

        print("🔄 Veriler işleniyor...")

        for idx, row in self.df.iterrows():
            # Sütun isimlerini kendi CSV'ne göre değiştir!
            # Örnek varsayılan isimler:
            print(row.get("bolum"))
            disease_doc = self._create_disease_document(
                hastalık=row.get("hastalık", row.get("Hastalık", "")),
                nedir=row.get("nedir", row.get("Nedir", "")),
                belirtiler=row.get("belirtiler", row.get("Belirtiler", "")),
                teshis=row.get("teshis", row.get("Teşhis", "")),
                tedavi=row.get("tedavi", row.get("Tedavi", "")),
                bolum=str(row.get("bolum", "")).strip(),
                turler=row.get("türleri", row.get("Türler", "")),
                soru_cevap=row.get("soru_cevap", row.get("Soru-Cevap", "")),
                link=row.get("link", row.get("Link", "")),
            )

            self.processed_data.append(disease_doc)

        print(f"✅ {len(self.processed_data)} hastalık işlendi")
        return self.processed_data

    def _create_disease_document(self, **kwargs):
        """
        Her hastalık için RAG'a uygun döküman oluştur

        ÖNEMLİ: Her hastalık birden fazla "chunk"a bölünebilir
        """

        hastalik_adi = kwargs.get("hastalık", "").strip()

        # Ana döküman metni - RAG'ın arayacağı text
        # Bu metni düzenlerken kullanıcının soracağı soruları düşün

        document_text = f"""
            HASTALIK: {hastalik_adi}

            NE: {kwargs.get('nedir', '')}

            BELİRTİLER: {kwargs.get('belirtiler', '')}

            TÜRLER: {kwargs.get('türleri', '')}

            TEŞHİS: {kwargs.get('teshis', '')}

            TEDAVİ: {kwargs.get('tedavi', '')}

            SORU-CEVAP: {kwargs.get('soru_cevap', '')}
        
        """.strip()

        # Metadata - Filtreleme için kullanılacak
        metadata = {
            "hastalık": hastalik_adi,
            "bolum": kwargs.get("bolum", "").strip(),
            "link": kwargs.get("link", "").strip(),
            "doc_type": "disease",
        }

        return {
            "id": hastalik_adi.lower().replace(" ", "_"),
            "text": document_text,
            "metadata": metadata,
        }

    def chunk_large_documents(self, max_chunk_size=1000):
        """
        Uzun dökümanları parçala

        RAG için optimal chunk boyutu: 500-1500 karakter
        """
        print("✂️  Uzun dökümanlar parçalanıyor...")

        chunked_data = []

        for doc in self.processed_data:
            text = doc["text"]

            # Eğer metin çok uzunsa, paragraflara böl
            if len(text) > max_chunk_size:
                paragraphs = text.split("\n\n")

                for i, para in enumerate(paragraphs):
                    if para.strip():
                        chunk_doc = {
                            "id": f"{doc['id']}_chunk_{i}",
                            "text": para.strip(),
                            "metadata": {
                                **doc["metadata"],
                                "chunk_index": i,
                                "is_chunk": True,
                            },
                        }
                        chunked_data.append(chunk_doc)
            else:
                chunked_data.append(doc)

        print(f"✅ {len(self.processed_data)} döküman → {len(chunked_data)} chunk")
        self.processed_data = chunked_data
        return chunked_data

    def save_processed_data(self, output_path):
        """İşlenmiş veriyi JSON olarak kaydet"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.processed_data, f, ensure_ascii=False, indent=2)

        print(f"💾 İşlenmiş veri kaydedildi: {output_file}")

    def get_statistics(self):
        """Veri istatistiklerini göster"""

        if not self.processed_data:
            print("⚠️  Henüz veri işlenmedi")
            return

        bolumler = {}
        for doc in self.processed_data:
            bolum = doc["metadata"].get("bolum", "Bilinmiyor")
            bolumler[bolum] = bolumler.get(bolum, 0) + 1

        print("\n📊 Veri İstatistikleri:")
        print(f"   - Toplam döküman: {len(self.processed_data)}")
        print(f"   - Bölüm sayısı: {len(bolumler)}")
        print("\n   En çok hastalık olan bölümler:")

        sorted_bolumler = sorted(bolumler.items(), key=lambda x: x[1], reverse=True)
        for bolum, count in sorted_bolumler[:10]:
            print(f"     • {bolum}: {count} hastalık")


# Test için main
if __name__ == "__main__":
    loader = DiseaseDataLoader("data/raw/hastaliklar_detayli_listesi.csv")

    if loader.load_csv():
        loader.process_diseases()
        loader.chunk_large_documents(max_chunk_size=1000)
        loader.save_processed_data("data/processed/diseases_processed.json")
        loader.get_statistics()
