import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from typing import List, Dict
from .embedder import TurkishEmbedder


class HealthVectorStore:
    """Sağlık asistanı için vector database"""

    def __init__(self, db_path="data/chroma_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        print(f"💾 ChromaDB başlatılıyor: {self.db_path}")

        # ChromaDB client
        self.client = chromadb.PersistentClient(path=str(self.db_path))

        # Collection (tablo gibi düşün)
        self.collection_name = "diseases"

        # Embedder
        self.embedder = TurkishEmbedder()

        print(f"✅ Vector store hazır")

    def create_collection(self, reset=False):
        """Collection oluştur veya yükle"""

        if reset:
            try:
                self.client.delete_collection(self.collection_name)
                print("🗑️  Eski collection silindi")
            except:
                pass

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},  # Cosine similarity kullan
        )

        print(
            f"📚 Collection: {self.collection_name} (Döküman sayısı: {self.collection.count()})"
        )

    def add_documents(self, documents: List[Dict], batch_size=100):
        """
        Dökümanları vector DB'ye ekle

        documents: [
            {
                'id': 'migren',
                'text': 'Migren baş ağrısı...',
                'metadata': {'bolum': 'Nöroloji', ...}
            },
            ...
        ]
        """

        print(f"\n📥 {len(documents)} döküman ekleniyor...")

        # Batch'lerle ekle (bellek tasarrufu)
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            # Embedding'leri hesapla
            texts = [doc["text"] for doc in batch]
            embeddings = self.embedder.encode_batch(texts, show_progress=False)

            # ChromaDB'ye ekle
            self.collection.add(
                ids=[doc["id"] for doc in batch],
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=[doc["metadata"] for doc in batch],
            )

            print(f"  ✓ {i+len(batch)}/{len(documents)} eklendi")

        print(f"✅ Tüm dökümanlar eklendi!")
        print(f"📊 Toplam: {self.collection.count()} döküman")

    def search(self, query: str, n_results=5, filter_bolum=None):
        """
        Sorguya en benzer dökümanları bul

        query: "Başım ağrıyor"
        n_results: Kaç sonuç dönsün
        filter_bolum: Sadece belirli bölümden ara
        """

        # Sorguyu embedding'e çeviriyor , sayısal olarak
        query_embedding = self.embedder.encode_text(query)

        # ChromaDB'de ara
        where_filter = None
        
        
        # eğer veriler arasında özel bi arama yapılması gerekiyorsa ona göre ek sorgular da yapılabilir
        if filter_bolum:
            where_filter = {"bolum": filter_bolum}

        # şu an sadece en alakalı gelen ilk 3 tane sonuç üzerinden cevap üretiliyor
        # Bundan sonraki amaç bu sonuçların ilk 10 tanesi ilk olarak toplandıktan sonra 
        # bu 10 tanesinin tekrar filtrelenmesi ile en iyi şekilde sonuçların üretilmesi sağlanacak
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where_filter,
        )

        # Sonuçları formatla
        formatted_results = []

        for i in range(len(results["ids"][0])):
            formatted_results.append(
                {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1
                    - results["distances"][0][i],  # Cosine'dan similarity'ye çevir
                }
            )

        

        return formatted_results

    def get_collection_stats(self):
        """Database istatistikleri"""

        count = self.collection.count()

        # İlk 100 dökümandan bölüm dağılımını al
        sample = self.collection.get(limit=min(100, count))

        bolumler = {}
        for metadata in sample["metadatas"]:
            bolum = str(metadata.get("bolum", "")).strip()
            bolumler[bolum] = bolumler.get(bolum, 0) + 1

        print(f"\n📊 Vector Database İstatistikleri:")
        print(f"   - Toplam döküman: {count}")
        print(f"   - Bölüm çeşitliliği: {len(bolumler)}")
        print(f"\n   Örnek bölümler:")
        for bolum, cnt in list(bolumler.items())[:5]:
            print(f"     • {bolum}: {cnt}")


def build_vector_database():
    """Ana fonksiyon: Veriyi yükle ve vector DB oluştur"""

    print("🚀 VECTOR DATABASE OLUŞTURULUYOR")

    # 1. İşlenmiş veriyi yükle
    processed_data_path = Path("data/processed/diseases_processed.json")

    if not processed_data_path.exists():
        print(f"❌ İşlenmiş veri bulunamadı: {processed_data_path}")
        print("Önce data_loader.py'yi çalıştır!")
        return

    with open(processed_data_path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    print(f"✅ {len(documents)} döküman yüklendi")

    # 2. Vector store oluştur
    vector_store = HealthVectorStore()
    vector_store.create_collection(reset=True)  # Sıfırdan başlasın 

    # 3. Dökümanları ekle
    vector_store.add_documents(documents)

    # 4. İstatistikleri göster
    vector_store.get_collection_stats()

    # 5. Test araması
    test_queries = ["Başım çok ağrıyor", "Göğsümde ağrı var", "Saçlarım dökülüyor"]

    for query in test_queries:
        print(f"\n🔍 Arama: '{query}'")
        results = vector_store.search(query, n_results=3)

        for i, result in enumerate(results, 1):
            print(
                f"\n  {i}. {result['metadata']['hastalik']} "
                f"(Benzerlik: {result['similarity']:.3f})"
            )
            print(f"     Bölüm: {result['metadata']['bolum']}")
            print(f"     Metin: {result['text'][:100]}...")

    print("\n" + "=" * 80)
    print("✅ VECTOR DATABASE HAZIR!")
    print("=" * 80)


if __name__ == "__main__":
    build_vector_database()
