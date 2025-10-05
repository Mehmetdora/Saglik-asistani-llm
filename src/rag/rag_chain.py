import ollama
from vector_store import HealthVectorStore
from typing import List, Dict


class HealthRAGAssistant:
    """Sağlık asistanı RAG sistemi"""

    def __init__(self, model_name="mistral:7b"):
        print("🤖 Sağlık RAG Asistanı başlatılıyor...")

        self.model_name = model_name
        self.vector_store = HealthVectorStore()
        self.vector_store.create_collection(reset=False)  # Mevcut DB'yi kullan

        # System prompt
        self.system_prompt = """Sen Türkiye'deki hastaneler için bir sağlık yönlendirme asistanısın.

GÖREVİN:
- Hastalara hangi hastane bölümüne gitmeleri gerektiğini söylemek
- Verilen tıbbi bilgilere dayanarak cevap vermek
- Kesinlikle teşhis koymamak, sadece yönlendirme yapmak

KURALLAR:
1. Sadece sana verilen bilgilere dayanarak cevap ver
2. Bilmediğin bir şey için "Emin değilim, doktora danışın" de
3. Acil durumlarda 112'yi aramalarını söyle
4. Cevapların kısa ve anlaşılır olsun (3-4 cümle)
5. Her zaman "Bu bir tıbbi tavsiye değildir" uyarısı ekle

ÖRNEK:
Kullanıcı: "Başım çok ağrıyor ne yapmalıyım?"
Sen: "Baş ağrısı için Nöroloji bölümüne başvurmanızı öneririm. Nöroloji beyin ve sinir sistemi hastalıklarıyla ilgilenir. Eğer ağrı çok şiddetliyse veya ani başladıysa, acil servise gitmelisiniz. Bu bir tıbbi tavsiye değildir, mutlaka doktora danışın."
"""

        print("✅ RAG Asistanı hazır!\n")

    def retrieve_context(self, query: str, n_results=3) -> List[Dict]:
        """Sorguya en alakalı dökümanları bul"""

        print(f"🔍 Aranıyor: '{query}'")
        results = self.vector_store.search(query, n_results=n_results)

        print(f"📚 {len(results)} alakalı döküman bulundu:")
        for i, res in enumerate(results, 1):
            print(
                f"   {i}. {res['metadata']['hastalık']} "
                f"(Benzerlik: {res['similarity']:.2f})"
            )

        return results

    def build_context(self, retrieved_docs: List[Dict]) -> str:
        """Bulunan dökümanları LLM için context'e çevir"""

        context_parts = []

        for doc in retrieved_docs:
            context_parts.append(
                f"""
                HASTALIK: {doc['metadata']['hastalık']}
                BÖLÜM: {doc['metadata']['bolum']}
                BİLGİ: {doc['text'][:500]}  
                ---
                """
            )

        return "\n".join(context_parts)

    def generate_answer(self, query: str, context: str) -> str:
        """LLM ile cevap üret"""

        prompt = f"""{self.system_prompt}

KULLANICIYA VERİLEN TIBBİ BİLGİLER:
{context}

KULLANICI SORUSU:
{query}

CEVAP (Kısa ve net, 3-4 cümle):"""

        print("\n💬 Cevap üretiliyor...")

        response = ollama.chat(
            model=self.model_name, messages=[{"role": "user", "content": prompt}]
        )

        return response["message"]["content"]

    def ask(self, query: str, n_context=3, verbose=True) -> Dict:
        """
        Ana fonksiyon: Soru sor, cevap al

        Returns:
            {
                'query': kullanıcı sorusu,
                'answer': LLM cevabı,
                'sources': kullanılan kaynaklar,
                'retrieved_docs': bulunan dökümanlar
            }
        """

        if verbose:
            print("\n" + "=" * 80)
            print(f"❓ SORU: {query}")
            print("=" * 80)

        # 1. Retrieval - Alakalı dökümanları bul
        retrieved_docs = self.retrieve_context(query, n_results=n_context)

        # 2. Context oluştur
        context = self.build_context(retrieved_docs)

        # 3. Generation - Cevap üret
        answer = self.generate_answer(query, context)

        if verbose:
            print("\n" + "=" * 80)
            print("✅ CEVAP:")
            print("=" * 80)
            print(answer)
            print
            print("\n📖 KAYNAKLAR:")
            for i, doc in enumerate(retrieved_docs, 1):
                print(
                    f"   {i}. {doc['metadata']['hastalık']} "
                    f"({doc['metadata']['bolum']})"
                )
                if doc["metadata"].get("link"):
                    print(f"Link: {doc['metadata']['link']}")
            print("=" * 80)

        return {
            "query": query,
            "answer": answer,
            "sources": [doc["metadata"]["hastalık"] for doc in retrieved_docs],
            "retrieved_docs": retrieved_docs,
        }

    def interactive_session(self):
        """Interaktif soru-cevap oturumu"""

        print("\n" + "=" * 80)
        print("🏥 SAĞLIK ASİSTANI - İNTERAKTİF OTURUM")
        print("=" * 80)
        print("Soru sorun veya 'çıkış' yazın\n")

        while True:
            try:
                query = input("👤 Siz: ").strip()

                if query.lower() in ["çıkış", "exit", "quit", "q"]:
                    print("\n👋 Görüşmek üzere!")
                    break

                if not query:
                    continue

                self.ask(query, verbose=True)
                print("\n")

            except KeyboardInterrupt:
                print("\n\n👋 Görüşmek üzere!")
                break
            except Exception as e:
                print(f"\n❌ Hata: {e}\n")


# Test ve demo
def demo():
    """RAG sistemini test et"""

    assistant = HealthRAGAssistant()

    # Test soruları
    test_queries = ["Başım çok ağrıyor ve bulantım var, hangi bölüme gitmeliyim?"]

    """ 
     "Göğsümde ağrı var ve nefes almakta zorlanıyorum",
        "20'lik dişim çıkıyor ve çok acıyor, ne yapmalıyım?",
        "Dizim şişti ve hareket ettirmekte zorlanıyorum",
        "Sürekli yorgunum ve kilo veriyorum", 
    """

    print("\n" + "=" * 80)
    print("🧪 TEST SORULARI")
    print("=" * 80)

    for query in test_queries:
        result = assistant.ask(query, verbose=True)
        input("\n[Enter tuşuna basarak devam edin...]")

    # İnteraktif moda geç
    print("\n\nŞimdi kendi sorularınızı sorabilirsiniz:")
    assistant.interactive_session()


if __name__ == "__main__":
    demo()
