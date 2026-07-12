import os
import shutil

print("🧹 Wiping the AI Database clean...")

if os.path.exists("chroma_db"):
    try:
        shutil.rmtree("chroma_db")
        print("✅ Deleted ChromaDB Vector Database.")
    except Exception as e:
        print(f"⚠️ Could not delete chroma_db: {e} (Make sure the app is closed)")

if os.path.exists("repo_cache.json"):
    try:
        os.remove("repo_cache.json")
        print("✅ Deleted GitHub Repository Cache.")
    except Exception as e:
        print(f"⚠️ Could not delete repo_cache.json: {e}")

print("✨ System is completely clean! You can now run the pipeline on a fresh candidate.")
