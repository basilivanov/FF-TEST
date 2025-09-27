#!/usr/bin/env python3
"""
Получение креденшелов для админки
"""
import os
import sys
sys.path.insert(0, '/opt/feature-factory')

try:
    from app.db.session import SessionLocal
    from app.utils.secret_store import decrypt_value
    
    def get_secret(key: str) -> str | None:
        if not key or SessionLocal is None:
            return None
        db = SessionLocal()
        try:
            row = db.execute("SELECT value_enc FROM secrets WHERE key = :k", {"k": key}).fetchone()
            if not row:
                return None
            return decrypt_value(row[0])
        except Exception as e:
            print(f"Error getting secret {key}: {e}")
            return None
        finally:
            db.close()
    
    # Получаем креденшелы
    username = get_secret("admin.ui.username")
    password = get_secret("admin.ui.password")
    
    if username and password:
        print(f"USERNAME: {username}")
        print(f"PASSWORD: {password}")
    else:
        print("Credentials not found in secret store")
        print(f"Username: {username}")
        print(f"Password: {password}")
        
        # Попробуем создать дефолтные если их нет
        if not username or not password:
            print("\nTrying to create default credentials...")
            from app.utils.secret_store import encrypt_value
            
            default_username = "admin"
            default_password = "feature-factory-admin"
            
            db = SessionLocal()
            try:
                if not username:
                    encrypted_username = encrypt_value(default_username)
                    db.execute(
                        "INSERT OR REPLACE INTO secrets(key, value_enc, scope, created_at, updated_at) VALUES (?, ?, 'test', datetime('now'), datetime('now'))",
                        ("admin.ui.username", encrypted_username)
                    )
                    print(f"Created default username: {default_username}")
                
                if not password:
                    encrypted_password = encrypt_value(default_password)
                    db.execute(
                        "INSERT OR REPLACE INTO secrets(key, value_enc, scope, created_at, updated_at) VALUES (?, ?, 'test', datetime('now'), datetime('now'))",
                        ("admin.ui.password", encrypted_password)
                    )
                    print(f"Created default password: {default_password}")
                
                db.commit()
                print(f"\nFinal credentials:")
                print(f"USERNAME: {username or default_username}")
                print(f"PASSWORD: {password or default_password}")
                
            except Exception as e:
                print(f"Error creating defaults: {e}")
            finally:
                db.close()
                
except Exception as e:
    print(f"Error: {e}")
    print("Trying fallback...")
    
    # Fallback - возможно есть переменные окружения
    username = os.getenv("ADMIN_UI_USERNAME", "admin")
    password = os.getenv("ADMIN_UI_PASSWORD", "feature-factory-admin")
    
    print(f"FALLBACK USERNAME: {username}")
    print(f"FALLBACK PASSWORD: {password}")