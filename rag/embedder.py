from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import torch


class TurkishEmbedder:
    
    """
        Bu custom embedder class ile sorulan soru istenilen cevapların ne olacağı 
        eşleştiriliyor. Yani soruyu sayısal formata çevirip hangi cevaba en yakın olacağı
        bulunmak için cosine karşılaştırması yapılıyor. 
    
        Amaç ise;
        - Soruyu embedding e çevirmek 
        - Soru embedding i üzerinden en alakalı hastalıkları seçmek
        
        yani sorulan soruya cevap vermek için gerekli olan bilgilerin bulunması kısmı burada yapılıyor. 
    
        * Burada embedding boyutu her cümlenin ne kadar detaylı bir şekilde sayısal
        olarak temsil edildiğidir. 
        metin → [0.12, -0.34, 0.91, ..., 0.07]  (ör: 384 boyut)

        Az olması hız ve ram olarak avantaj sağlar,
        ama fazla olursa daha doğru anlam karşılaştırması yapılabilir. Çok daha tutarlı olur. 
        Fakat daha yavaş çalışır, ram e bağlı olarak. 
        
        Eğer embedding modeli zayıfsa , boyutu arttırmak kaliteyi arttırmaz,
        Eğer veri seti küçükse , büyük embedding gereksiz olur. 
        
        - Embedding modeli sabit bir boyutta hazırlanmıştır. Bunu sonradan kod içinde 
        düzenlenemez. İlk başta proje için embedding seçimi yapılırken istenen embedding 
        boyutuna göre model seçimi yapılmalıdır. 
        Yani embedding i 385 olan bir modeli hadi 760 yapayım diyemezsin. 
    
    """
    
    
    

    def __init__(
        self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device: str = None
    ):
        print(f"🧠 Embedding modeli yükleniyor: {model_name}")

        try:
            
            if torch.backends.mps.is_available():
                device = "mps"
                # apple için 
            elif torch.cuda.is_available():
                device = "cuda" # NVIDIA GPU varsa (Windows/Linux)
            else:
                device = "cpu"
    
            self.model = SentenceTransformer(model_name,device=device)
            print(f"✅ Model yüklendi")
            print("Model hakkında detaylı bilgiler: " , self.model._first_module().auto_model.config)

            # Embedding boyutunu test et
            test_embedding = self.model.encode("test")
            print(f"📐 Embedding boyutu: {len(test_embedding)}")

        except Exception as e:
            print(f"❌ Model yükleme hatası: {e}")
            print("📥 İlk kullanımda model indirilecek, 5-10 dakika sürebilir")
            raise

    #Tek bir metni embedding'e çevir
    def encode_text(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)

    # birden fazla text i embedding yapmak için 
    def encode_batch(
        self, texts: List[str], batch_size=32, show_progress=True
    ) -> np.ndarray:

        print(f"🔄 {len(texts)} metin encode ediliyor...")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        print(f"✅ Encoding tamamlandı: {embeddings.shape}")
        return embeddings

    # 2 metin arasındaki cosine benzerliğini bulmak için 
    def similarity(self, text1: str, text2: str) -> float:
        """İki metin arasındaki benzerlik (0-1)"""

        emb1 = self.encode_text(text1)
        emb2 = self.encode_text(text2)

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)


# Test
if __name__ == "__main__":
    embedder = TurkishEmbedder()

    # Benzerlik testi
    text1 = "Başım çok ağrıyor"
    text2 = "Migren hastasıyım"
    text3 = "Dizim şişti"

    sim1 = embedder.similarity(text1, text2)
    sim2 = embedder.similarity(text1, text3)

    print(f"\n🧪 Benzerlik Testi:")
    print(f"   '{text1}' vs '{text2}': {sim1:.3f}")
    print(f"   '{text1}' vs '{text3}': {sim2:.3f}")
    print(f"\n   ✅ İlki daha benzer olmalı: {sim1 > sim2}")
