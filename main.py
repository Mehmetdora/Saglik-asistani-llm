import sys
from pathlib import Path

# src klasörünü Python path'e ekle
sys.path.insert(0, str(Path(__file__).parent / "src"))
from rag.rag_chain import HealthRAGAssistant


def main():

    print(
        """


                  SAĞLIK ASİSTANI - RAG SİSTEMİ               
                                                               
               Hastane bölümü yönlendirme asistanı                     
       626 hastalık verisi ile sorulara yanıt verebilmektedir. 
                                                               

    """
    )

    try:
        assistant = HealthRAGAssistant()
        assistant.interactive_session()

    except KeyboardInterrupt:
        print("\n\n Program sonlandırıldı")
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        print("\nSorun giderme:")
        print("1. Vector database oluşturuldu mu? → python src/rag/vector_store.py")
        print("2. Ollama çalışıyor mu? → ollama serve")
        print("3. Model indirildi mi? → ollama pull llama3.2:3b")


if __name__ == "__main__":
    main()
