import pandas as pd
import json
from pathlib import Path
from typing import List, Dict

import os
import sys
import csv

class DiseaseDataLoader:

    def __init__(self, csv_path: str):
        print(f"Ana dosya yolu : {os.getcwd()}")
        current_path = os.getcwd()
        project_path = os.chdir('..')
        csv_path = os.path.abspath(csv_path)

        if not os.path.exists(csv_path):
            print(f"------>  Hatalı dosya yolu girilmiştir, girilen dosya yolu : 'f{csv_path}'")
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
            # CSV dosyasındaki bazı verilerin uzunluğundan ötürü veri okumak için max ayarlar seçildi
            csv.field_size_limit(sys.maxsize)

            # Pandas ile BOM-safe okuma, bazı sütun isimleri farklı gelebiliyor
            self.df = pd.read_csv(
                self.csv_path,
                encoding='utf-8-sig',  # BOM'u otomatik kaldırır
                engine='python',
                quoting=csv.QUOTE_ALL
            )

            # Yine de sütun isimlerini temizle
            self.df.columns = self.df.columns.str.strip()

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

            """
            Eğer veri içindeki bir hastalığın herhangi bir alt başlığı null ise o başlığı 
            bir chunk olarak oluşturmamalı.
            """


            # Her section için farklı bir chunk oluşturma
            for section_key, content, title in sections:

                content = str(content).strip()
                
                # eğer section boşsa atla(nedir,belirtiler vs.), bu bilgiler de doldurulmalı aslında
                if pd.isnull(content) or content == '' or content == 'nan':
                    print(f"Sorunlu içerik : \n{content}")
                    continue

                # hastalık modeli
                data = {
                    "hastalik": hastalik,
                    "bolum": bolum,
                    "section": title,
                    "content": content, # ana içerik burada , sadece ilgili alt başlığın içeriği
                    "text_content": f"""HASTALIK: {hastalik}, BÖLÜM: {bolum}, SECTİON: {title}, CONTENT: {content}""".strip(),
                }

                # tam chunk yapısı
                doc = {
                    "id": f"{hastalik.lower().replace(' ', '_')}__{section_key}",
                    "data": data,
                    "metadata": {
                        **base_metadata,
                        "section": section_key,
                        "section_title": title,
                    },
                }

                self.processed_data.append(doc)

        print(f"---> Toplam {len(self.processed_data)} hastalık alt başlığı oluşturuldu")
        return self.processed_data


    # eğer bir section uzun ise alt parçalara bölme
    # yani her hastalığın her bir alt başlığı(nedir, belirtiler vs.) başlığı kendi içinde chunklanıyor
    """
    Sonda tek cümle kalmamasını sağlama: Çoğu normal durumda evet; son küçük chunk’ı bir öncekiyle birleştiriyor.
    Chunk’ların cümle sayısının aşağı yukarı dengeli : Greedy + son merge ile cümle sayıları birbirine yakın chunklar oluşturuldu, tam eşit değil.
    """
    """
    Bu chunking ile cümle sayısına göre metin baştan sonra doğru max karakter sayısını geçmeyecek şekilde cümlelere göre gruplanıyor.
    Ama chunklar arasında oluşabilecek karater sayısı farkı kontrol edilmiyor, özellikle sonuncu chunkda.
    """
    def chunk_large_documents(self, max_chunk_size=1000):
       
        """
        Uzun dökümanları parçala
        
        İşlenen her bir section şeklindeki chunk , eğer uzun bir text içeriyorsa
        cümle bazlı olarak parçalara ayrılıyor.      
        """
    
        print("---> Uzun hastalık alt başlıkları parçalanıyor (section bazlı)...")

        chunked_data = []

        for doc in self.processed_data:

            data = doc["data"]  # ana içerik

            # Asıl content alanın hangisiyse onu kullan:
            # content = data["text_content"]
            content = data.get("content") or data.get("text_content") or ""

            header = f"HASTALIK: {data['hastalik']}, BÖLÜM: {data['bolum']}, SECTİON: {data['section']}, CONTENT: "

            # Küçükse olduğu gibi ekle
            if len(header) + len(content) <= max_chunk_size:
                chunked_data.append(
                    {
                        "id": f"{doc['id']}_chunk_0",
                        "text": header + content.strip(),
                        "metadata": {
                            **doc["metadata"],
                            "chunk_index": 0,
                            "is_sub_chunk": False,
                        },
                    }
                )
                continue


            raw_sentences = content.split(". ")
            sentences = [s.strip() for s in raw_sentences if s.strip()]


            temp_chunks = []
            current_chunk_sents = []

            for i, sent in enumerate(sentences):

                # Bu cümleyi eklersek oluşacak text (header + cümleler)
                tentative_sents = current_chunk_sents + [sent]
                tentative_text = ". ".join(tentative_sents)
                tentative_full = header + tentative_text

                if len(tentative_full) > max_chunk_size and current_chunk_sents:
                    temp_chunks.append(current_chunk_sents)
                    current_chunk_sents = [sent]  # yeni chunk bu cümle ile başlasın
                else:
                    current_chunk_sents.append(sent)

            # Döngü bitince elde kalan cümleler
            if current_chunk_sents:
                temp_chunks.append(current_chunk_sents)

            # 3) En sondaki chunk çok küçükse (örneğin tek cümle) → bir öncekiyle birleştir
            if len(temp_chunks) >= 2:
                last_chunk = temp_chunks[-1]
                prev_chunk = temp_chunks[-2]

                last_text = ". ".join(last_chunk)
                prev_text = ". ".join(prev_chunk)

                # Karakter uzunluğu ve cümle sayısına göre "çok küçük" kontrolü
                # Örneğin: tek cümle VE toplam uzunluğun %30'undan az ise
                if (
                        len(last_chunk) < 2
                        or len(header) + len(last_text) < int(0.3 * max_chunk_size)
                ):
                    merged_text = prev_text + ". " + last_text
                    if len(header) + len(merged_text) <= max_chunk_size:
                        # Birleştirmeyi güvenle yapabiliyorsak:
                        temp_chunks[-2] = prev_chunk + last_chunk
                        temp_chunks.pop()  # son chunk'ı listeden çıkar

            # 4) Artık temp_chunks içinde düzgün, dengeli gruplar var → gerçek chunk objeleri üret
            chunk_index = 0
            for sents in temp_chunks:
                chunk_text = ". ".join(sents).strip()
                full_text = header + chunk_text

                chunked_data.append({
                    "id": f"{doc['id']}_chunk_{chunk_index}",
                    "text": full_text,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": chunk_index,
                        "is_sub_chunk": True,
                    },
                })
                chunk_index += 1

        print(f"--->  {len(self.processed_data)} doküman → {len(chunked_data)} chunk")
        self.processed_data = chunked_data
        return chunked_data

    """
    Metindeki cümleler karakter sayılarına göre gruplanır. Eğer bir chunk içinde az karakter varsa ve komşu chunkları ile 
    arasında çok fark varsa onlardan cümleler az olana kaydırılarak olabildiğince karakter farkı azaltılır
    """
    def chunk_large_documents2(self, max_chunk_size=1000):
        """
        Uzun dökümanları parçala

        - komşu chunklar arasında cümle kaydırarak boyutları dengelenir
        """

        chunked_data = []

        # chunk uzunluğunu karakter bazlı hesapla
        def chunk_len(header: str, sents: list[str]) -> int:
            if not sents:
                return len(header)
            return len(header) + len(". ".join(sents))

        # Yardımcı: greedy chunk + balancing
        def split_and_balance(content: str, header: str, max_size: int) -> list[list[str]]:

            raw_sentences = content.split(". ")
            sentences = [s.strip() for s in raw_sentences if s.strip()]
            if not sentences:
                return []

            # 2) greedy chunking , limiti doldurana kadar baştan başlayarak cümleler gruplanır
            temp_chunks: list[list[str]] = []
            current: list[str] = []

            for sent in sentences:
                tentative_sents = current + [sent]
                tentative_len = chunk_len(header, tentative_sents)

                if tentative_len > max_size and current:
                    temp_chunks.append(current)
                    current = [sent]
                else:
                    current = tentative_sents

            if current:
                temp_chunks.append(current)

            # dengeleme
            # amaç: iki chunk arasındaki karakter sayısı çok fazla ise aradaki farkı kapatmak için az olana cümle kaydırılır
            max_loops = 50  # max döngü denemesi
            loop = 0

            def effective_len(sents: list[str]) -> int:
                return chunk_len(header, sents)

            while loop < max_loops:
                loop += 1
                changed = False

                # Boş chunk varsa kaldır
                temp_chunks = [c for c in temp_chunks if c]

                if len(temp_chunks) <= 1:
                    break

                for i in range(len(temp_chunks) - 1):
                    a = temp_chunks[i]
                    b = temp_chunks[i + 1]

                    len_a = effective_len(a)
                    len_b = effective_len(b)
                    diff = abs(len_a - len_b)

                    # Fark max karakter sayısının %30 undan az ise yeterli
                    if diff < int(max_size * 0.3):
                        continue

                    # a büyük, b küçük ise: a nın son cümlesini b ye kaydırma
                    if len_a > len_b and len(a) > 1:
                        candidate = a[-1]
                        new_a = a[:-1]
                        new_b = [candidate] + b

                        if effective_len(new_a) <= max_size and effective_len(new_b) <= max_size:
                            temp_chunks[i] = new_a
                            temp_chunks[i + 1] = new_b
                            changed = True

                    # b büyük, a küçük ise: b nin ilk cümleyi a ya kaydırma
                    elif len_b > len_a and len(b) > 1:
                        candidate = b[0]
                        new_a = a + [candidate]
                        new_b = b[1:]

                        if effective_len(new_a) <= max_size and effective_len(new_b) <= max_size:
                            temp_chunks[i] = new_a
                            temp_chunks[i + 1] = new_b
                            changed = True

                if not changed:
                    break  # tüm chunklar kontrol edilmişse bitir

            # boş chunk kontrolü
            temp_chunks = [c for c in temp_chunks if c]
            return temp_chunks


        for doc in self.processed_data:
            data = doc["data"]  # ana metinler

            content = data.get("content") or data.get("text_content") or ""
            header = (
                f"HASTALIK: {data['hastalik']}, "
                f"BÖLÜM: {data['bolum']}, "
                f"SECTİON: {data['section']}, CONTENT: "
            )

            # zaten geçmiyorsa direkt ekle
            if len(header) + len(content) <= max_chunk_size:
                chunked_data.append(
                    {
                        "id": f"{doc['id']}_chunk_0",
                        "text": header + content.strip(),
                        "metadata": {
                            **doc["metadata"],
                            "chunk_index": 0,
                            "is_sub_chunk": False,
                        },
                    }
                )
                continue

            # içeriği böl ve dengele
            balanced_chunks_sents = split_and_balance(content, header, max_chunk_size)


            chunk_index = 0
            for sents in balanced_chunks_sents:
                chunk_text = ". ".join(sents).strip()
                full_text = header + chunk_text

                chunked_data.append(
                    {
                        "id": f"{doc['id']}_chunk_{chunk_index}",
                        "text": full_text,
                        "metadata": {
                            **doc["metadata"],
                            "chunk_index": chunk_index,
                            "is_sub_chunk": True,
                        },
                    }
                )
                chunk_index += 1

        print(f"--->  {len(self.processed_data)} doküman → {len(chunked_data)} chunk")
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
            print("---> Henüz veri işlenmedi")
            return

        bolumler = {}
        for doc in self.processed_data:
            bolum = doc["metadata"].get("bolum", "Bilinmiyor")
            bolumler[bolum] = bolumler.get(bolum, 0) + 1

        print("\n===> Veri İstatistikleri:")
        print(f"   - Toplam döküman: {len(self.processed_data)}")
        print(f"   - Bölüm sayısı: {len(bolumler)}")
        print("\n   En çok chunk içeren bölümler:")

        sorted_bolumler = sorted(bolumler.items(), key=lambda x: x[1], reverse=True)
        for bolum, count in sorted_bolumler[:10]:
            print(f"     • {bolum}: {count} chunk")





# Test için 
if __name__ == "__main__":
    loader = DiseaseDataLoader("data/raw/hastaliklar_detayli_listesi.csv")
    if loader.load_csv():
        loader.process_diseases()
        loader.chunk_large_documents2(max_chunk_size=1000)
        loader.save_processed_data("data/processed/diseases_processed.json")
        loader.get_statistics()
