from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List


class TurkishEmbedder:

    def __init__(
        self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Türkçe için en iyi modeller:
        - emrecan/bert-base-turkish-cased-mean-nli-stsb-tr
        - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
        """
        print(f"🧠 Embedding modeli yükleniyor: {model_name}")

        try:
            self.model = SentenceTransformer(model_name)
            print(f"✅ Model yüklendi")

            # Embedding boyutunu test et
            test_embedding = self.model.encode("test")
            print(f"📐 Embedding boyutu: {len(test_embedding)}")

        except Exception as e:
            print(f"❌ Model yükleme hatası: {e}")
            print("📥 İlk kullanımda model indirilecek, 5-10 dakika sürebilir")
            raise

    def encode_text(self, text: str) -> np.ndarray:
        """Tek bir metni embedding'e çevir"""
        return self.model.encode(text, convert_to_numpy=True)

    def encode_batch(
        self, texts: List[str], batch_size=32, show_progress=True
    ) -> np.ndarray:
        """Birden fazla metni toplu encode et"""

        print(f"🔄 {len(texts)} metin encode ediliyor...")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        print(f"✅ Encoding tamamlandı: {embeddings.shape}")
        return embeddings

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
