
import os
import sys
from rag.rag_pipeline import rag_pipeline

def test_rag():
    print("--- Testing RAG System ---")

    # 1. Create a dummy document
    test_file = "test_doc.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("The secret code for the vault is 998877. The project name is Project Chimera.")
    print(f"Created {test_file}")

    # 2. Ingest Document
    print("Ingesting document...")
    rag_pipeline.ingest_documents([test_file])

    # 3. Ask Question
    query = "What is the secret code for the vault?"
    print(f"Query: {query}")
    answer = rag_pipeline.answer_from_docs(query)
    print(f"Answer: {answer}")

    # 4. Verify Answer
    if "998877" in answer:
        print("✅ RAG Test Passed: Found the secret code.")
    else:
        print("❌ RAG Test Failed: Did not find the secret code.")
        sys.exit(1)
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    try:
        test_rag()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
