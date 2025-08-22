import hashlib
import os
from datetime import datetime

def get_file_hash(filepath):
    \"\"\"Получить хеш файла\"\"\"
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def update_doc_registry():
    \"\"\"Обновить реестр документов\"\"\"
    docs = [
        \"docs/Schema-000-base-tables.md\",
        \"docs/Architecture.md\",
        \"CHANGELOG.md\",
        \"app/db/migrations/README.md\"
    ]
    
    registry_lines = []
    for doc in docs:
        if os.path.exists(doc):
            hash_value = get_file_hash(doc)
            updated_at = datetime.now().isoformat()
            registry_lines.append(f\"{doc},v1.0,{hash_value},{updated_at}\\n\")
    
    with open(\"doc_registry.csv\", \"w\") as f:
        f.writelines(registry_lines)

if __name__ == \"__main__\":
    update_doc_registry()