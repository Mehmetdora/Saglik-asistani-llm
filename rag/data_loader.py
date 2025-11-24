import pandas as pd
import json
from pathlib import Path
from typing import List, Dict


class DiseaseDataLoader:

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.processed_data = []
        
        
        """
        
        Hazırlanan CSV dosyası alınır , RAG sisteminin kullanabileceği şekilde
        döküman + metadata + chunk olarak parçalar. 
        Sonrasında bu her bir chunk parçasını bir json dosyasına kaydeder. 
        
        """

    def load_csv(self):
        """
        csv yi oku , 
        self.df e kaydet. 
        """
        print(f"📂 CSV yükleniyor: {self.csv_path}")

        try:
            self.df = pd.read_csv(self.csv_path, encoding="utf-8")
            print(f"✅ {len(self.df)} satır yüklendi")
            return True
        except Exception as e:
            print(f"❌ Hata: {e}")
            return False
    
    """
    self.df içindeki her satırı döner,
    her satırdan get() ile istenen bilgileri alır(eğer yoksa diye -> get("fdf", get()) kullanıldı)
    her bir satırdaki veriler bir fonksiyon ile paketlenerek bir array'de tutuldu 
    """
    def process_diseases(self):
        self.processed_data = []

        for idx, row in self.df.iterrows():
            hastalik = str(row.get("hastalik", row.get("Hastalık", ""))).strip()
            bolum = str(row.get("bolum", "")).strip()
            link = str(row.get("link", row.get("Link", ""))).strip()

            if not hastalik:
                continue


            # her chunk'da ortak olacak metadata
            base_metadata = {
                "hastalik": hastalik,
                "bolum": bolum,
                "link": link,
                "doc_type": "disease",
            }

            sections = [
                ("nedir",       row.get("nedir", row.get("Nedir", "")),       "NEDİR"),
                ("belirtiler",  row.get("belirtiler", row.get("Belirtiler", "")), "BELİRTİLER"),
                ("turler",      row.get("türleri", row.get("Türler", "")),   "TÜRLER"),
                ("teshis",      row.get("teshis", row.get("Teşhis", "")),    "TEŞHİS"),
                ("tedavi",      row.get("tedavi", row.get("Tedavi", "")),    "TEDAVİ"),
                ("soru_cevap",  row.get("soru_cevap", row.get("Soru-Cevap", "")), "SORU-CEVAP"),
            ]

            # Her section için farklı bir chunk oluşturma
            for section_key, content, title in sections:
                content = str(content).strip()
                
                # eğer section boşsa atla(nedir,belirtiler vs.)
                if not content:
                    continue

                #chunk metni
                text = f"""
                    HASTALIK: {hastalik}
                    BÖLÜM: {bolum}
                    KISIM: {title}

                    {content}
                """.strip()

                # tam chunk yapısı
                doc = {
                    "id": f"{hastalik.lower().replace(' ', '_')}__{section_key}",
                    "text": text,
                    "metadata": {
                        **base_metadata,
                        "section": section_key,
                        "section_title": title,
                    },
                }
                self.processed_data.append(doc)

        print(f"✅ Toplam {len(self.processed_data)} RAG dokümanı oluşturuldu")
        return self.processed_data

    
    def _create_disease_document(self, **kwargs):
        hastalik_adi = kwargs.get("hastalik", "").strip()

        # Ana döküman metni - RAG'ın arayacağı text
        # Sorulacak sorulara cevap için kullanılacak verileri burada ekle
        document_text = f"""
            HASTALIK: {hastalik_adi}

            NEDİR: {kwargs.get('nedir', '')}

            BELİRTİLER: {kwargs.get('belirtiler', '')}

            TÜRLER: {kwargs.get('türleri', '')}

            TEŞHİS: {kwargs.get('teshis', '')}

            TEDAVİ: {kwargs.get('tedavi', '')}

            SORU-CEVAP: {kwargs.get('soru_cevap', '')}
        
        """.strip()

        # Metadata - Filtreleme için kullanılacak
        metadata = {
            "hastalik": hastalik_adi,
            "bolum": kwargs.get("bolum", "").strip(),
            "link": kwargs.get("link", "").strip(),
            "doc_type": "disease",
        }

        return {
            "id": hastalik_adi.lower().replace(" ", "_"),
            "text": document_text,
            "metadata": metadata,
        }
   
    # eğer bir section uzun ise alt parçalara bölme
    def chunk_large_documents(self, max_chunk_size=1000):
       
        """
        Uzun dökümanları parçala
        
        İşlenen her bir section şeklindeki chunk , eğer uzun bir text içeriyorsa
        cümle bazlı olarak parçalara ayrılıyor.      
        """
    
        print("✂️  Uzun dokümanlar parçalanıyor (section bazlı)...")

        chunked_data = []

        for doc in self.processed_data:
            text = doc["text"]

            # Küçükse olduğu gibi ekle
            if len(text) <= max_chunk_size:
                chunked_data.append(doc)
                continue
            
            lines = text.split("\n")
            header_lines = []
            content_start_idx = 0
            
            
            # HEADER + CONTENT OLARA PARÇALAMA(her section için) 
            # Header satırlarını bul (HASTALIK:, BÖLÜM:, KISIM: ile başlayanlar)
            # Bu header kısmı her parçalı seciton'ın text kısmının başına eklenecek
            # bu sayede semantic olarak embedding sırasında çok daha iyi eşleşme olacak
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if line_stripped.startswith(("HASTALIK:", "BÖLÜM:", "KISIM:")):
                    header_lines.append(line)
                elif line_stripped and header_lines:
                    # İlk içerik satırına geldi, header bitti
                    content_start_idx = i
                    break
            
            # Header'ı birleştir
            header = "\n".join(header_lines)
            if header:
                header += "\n\n"  #header sonu boşluk
            
            # İçeriği al , header'dan sonraki text
            content = "\n".join(lines[content_start_idx:]).strip()
            

            # İçeriği cümlelere böl, uzun olanları parçala(chunking)
            sentences = content.split(". ")
            current_chunk_content = ""
            chunk_index = 0

            for sent in sentences:
                if not sent.strip():
                    continue

                tentative = (current_chunk_content + " " + sent).strip()
                
                # Header boyutunu da hesaba katıyor
                chunk_and_header = header + tentative
                
                if len(chunk_and_header) > max_chunk_size and current_chunk_content:
                    # Mevcut chunk'ı kaydet (HEADER + içerik)
                    chunked_data.append({
                        "id": f"{doc['id']}_chunk_{chunk_index}",
                        "text": (header + current_chunk_content).strip(),
                        "metadata": {
                            **doc["metadata"],
                            "chunk_index": chunk_index,
                            "is_sub_chunk": True,
                        },
                    })
                    chunk_index += 1
                    current_chunk_content = sent
                else:
                    current_chunk_content = tentative

            # Son chunk'ı ekle (HEADER + içerik)
            if current_chunk_content.strip():
                chunked_data.append({
                    "id": f"{doc['id']}_chunk_{chunk_index}",
                    "text": (header + current_chunk_content).strip(),
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": chunk_index,
                        "is_sub_chunk": True,
                    },
                })

        print(f"✅ {len(self.processed_data)} doküman → {len(chunked_data)} chunk")
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


# Test için 
if __name__ == "__main__":
    loader = DiseaseDataLoader("data/raw/hastaliklar_detayli_listesi.csv")

    if loader.load_csv():
        loader.process_diseases()
        loader.chunk_large_documents(max_chunk_size=1000)
        loader.save_processed_data("data/processed/diseases_processed.json")
        loader.get_statistics()
