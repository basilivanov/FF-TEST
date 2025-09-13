#!/usr/bin/env python3
"""
E2E Test Utilities
Безопасные утилиты для тестирования без поломки системы
"""

import os
import json
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests


class SafeE2ETester:
    """Безопасный E2E тестер с автоматической очисткой"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.base_url = self.config.get('base_url', 'http://127.0.0.1:8081')
        self.timeout = int(self.config.get('timeout', '30'))
        self.artifacts_dir = None
        self.test_id = None
        self.created_resources = {
            'features': [],
            'branches': [],
            'files': [],
            'db_records': []
        }
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Загрузка конфигурации"""
        config = {}
        
        # Загружаем из .e2erc если есть
        e2erc_path = config_path or os.path.join(os.getcwd(), '.e2erc')
        if os.path.exists(e2erc_path):
            with open(e2erc_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.startswith('export '):
                            key = key[7:]  # убираем 'export '
                        # Убираем кавычки если есть
                        value = value.strip().strip('"').strip("'")
                        config[key.lower()] = value
        
        # Переопределяем переменными окружения
        env_mapping = {
            'E2E_BASE_URL': 'base_url',
            'E2E_TIMEOUT': 'timeout',
            'E2E_MODE': 'mode',
            'E2E_CLEANUP_ENABLED': 'cleanup_enabled'
        }
        
        for env_var, config_key in env_mapping.items():
            if env_var in os.environ:
                config[config_key] = os.environ[env_var]
                
        return config
    
    def __enter__(self):
        """Context manager вход - создаём тестовое окружение"""
        self.test_id = f"e2e_safe_{int(datetime.now().timestamp())}"
        self.artifacts_dir = tempfile.mkdtemp(prefix=f"{self.test_id}_")
        print(f"🧪 Starting safe E2E test: {self.test_id}")
        print(f"📁 Artifacts dir: {self.artifacts_dir}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager выход - автоматическая очистка"""
        print("🧹 Cleaning up test resources...")
        self._cleanup()
        
        if exc_type is None:
            print("✅ Test completed successfully")
        else:
            print(f"❌ Test failed: {exc_val}")
            
    def _cleanup(self):
        """Очистка созданных ресурсов"""
        # Удаляем созданные git ветки
        for branch in self.created_resources['branches']:
            try:
                subprocess.run(['git', 'checkout', 'main'], 
                             check=False, capture_output=True)
                subprocess.run(['git', 'branch', '-D', branch], 
                             check=False, capture_output=True)
                subprocess.run(['git', 'push', 'origin', '--delete', branch], 
                             check=False, capture_output=True)
                print(f"🗑️ Deleted branch: {branch}")
            except Exception as e:
                print(f"⚠️ Failed to delete branch {branch}: {e}")
        
        # Удаляем тестовые файлы
        for file_path in self.created_resources['files']:
            try:
                os.remove(file_path)
                print(f"🗑️ Deleted file: {file_path}")
            except Exception as e:
                print(f"⚠️ Failed to delete file {file_path}: {e}")
        
        # Удаляем созданные features из БД (опционально)
        if self.config.get('cleanup_enabled', 'true').lower() == 'true':
            self._cleanup_database_records()
    
    def _cleanup_database_records(self):
        """Очистка тестовых записей из базы данных"""
        db_path = "/opt/feature-factory/data/test.db"
        if not os.path.exists(db_path):
            return
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for feature_id in self.created_resources['features']:
                cursor.execute("DELETE FROM features WHERE id = ? AND title LIKE '%E2E%'", (feature_id,))
                print(f"🗑️ Deleted test feature: {feature_id}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to cleanup database: {e}")
    
    def test_health_endpoint(self) -> bool:
        """Тест health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health/live", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    print("✅ Health endpoint OK")
                    return True
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
    
    def test_api_endpoints_readonly(self) -> Dict[str, bool]:
        """Тест API endpoints только для чтения"""
        results = {}
        
        endpoints = {
            'features_list': '/api/v1/orchestrator/features',
            'tasks_list': '/api/v1/orchestrator/tasks',
            'openapi': '/openapi.json'
        }
        
        for name, path in endpoints.items():
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=self.timeout)
                results[name] = response.status_code == 200
                status = "✅" if results[name] else "❌"
                print(f"{status} {name}: {response.status_code}")
            except Exception as e:
                results[name] = False
                print(f"❌ {name}: {e}")
                
        return results
    
    def test_ci_endpoint_safe(self) -> bool:
        """Безопасный тест CI endpoint с фиктивными данными"""
        try:
            # Используем заведомо несуществующий PR
            fake_data = {
                "pr_number": 999999,
                "head_sha": "0" * 40,
                "state": "success", 
                "context": "e2e-safe-test",
                "description": f"Safe E2E test {self.test_id}",
                "target_url": f"{self.base_url}/health/live"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/ci/status",
                json=fake_data,
                auth=('ops', 'ops123'),
                timeout=self.timeout
            )
            
            # Ожидаем либо успех, либо "No feature found" - оба варианта OK
            success = (response.status_code == 200 or 
                      "No feature found" in response.text)
            
            status = "✅" if success else "❌"
            print(f"{status} CI endpoint test: {response.status_code}")
            return success
            
        except Exception as e:
            print(f"❌ CI endpoint error: {e}")
            return False
    
    def create_safe_test_feature(self, title_suffix: str = "") -> Optional[int]:
        """Создание тестовой feature с автоматической регистрацией для очистки"""
        if len(self.created_resources['features']) >= int(self.config.get('max_test_features', '3')):
            print("⚠️ Maximum test features limit reached")
            return None
            
        try:
            feature_data = {
                "title": f"🧪 E2E Safe Test {self.test_id} {title_suffix}".strip(),
                "autostart": False  # не автостартуем для безопасности
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/orchestrator/features",
                json=feature_data,
                headers={"X-Correlation-Id": self.test_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                feature_id = response.json().get('id')
                if feature_id:
                    self.created_resources['features'].append(feature_id)
                    print(f"✅ Created test feature: {feature_id}")
                    return feature_id
            
            print(f"❌ Failed to create feature: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"❌ Feature creation error: {e}")
            return None
    
    def create_safe_test_branch(self, branch_suffix: str = "") -> Optional[str]:
        """Создание тестовой ветки с автоматической регистрацией для очистки"""
        if len(self.created_resources['branches']) >= int(self.config.get('max_test_branches', '2')):
            print("⚠️ Maximum test branches limit reached")
            return None
            
        try:
            branch_name = f"e2e-safe-{self.test_id}-{branch_suffix}".strip('-')
            
            # Проверяем что мы не на защищённой ветке
            current_branch = subprocess.check_output(['git', 'branch', '--show-current'], 
                                                   text=True).strip()
            
            skip_branches = self.config.get('skip_branches', 'main,master').split(',')
            if current_branch in skip_branches:
                print(f"⚠️ Cannot create test branch from protected branch: {current_branch}")
                return None
            
            # Создаём ветку
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            
            # Создаём тестовый файл
            test_file = f"e2e_test_{self.test_id}.md"
            with open(test_file, 'w') as f:
                f.write(f"# E2E Safe Test {self.test_id}\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
                f.write(f"Branch: {branch_name}\n")
            
            subprocess.run(['git', 'add', test_file], check=True)
            subprocess.run(['git', 'commit', '-m', f'E2E Safe Test {self.test_id}'], check=True)
            
            self.created_resources['branches'].append(branch_name)
            self.created_resources['files'].append(test_file)
            
            print(f"✅ Created test branch: {branch_name}")
            return branch_name
            
        except Exception as e:
            print(f"❌ Branch creation error: {e}")
            return None
    
    def generate_report(self) -> str:
        """Генерация отчёта о тестировании"""
        report = {
            "test_id": self.test_id,
            "timestamp": datetime.now().isoformat(),
            "artifacts_dir": self.artifacts_dir,
            "config": self.config,
            "created_resources": self.created_resources,
            "status": "completed"
        }
        
        report_file = os.path.join(self.artifacts_dir, "e2e_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"📄 Report saved: {report_file}")
        return report_file


def main():
    """Пример использования"""
    with SafeE2ETester() as tester:
        # Базовые тесты
        tester.test_health_endpoint()
        api_results = tester.test_api_endpoints_readonly()
        tester.test_ci_endpoint_safe()
        
        # Расширенные тесты (опционально)
        if os.environ.get('E2E_FULL_TEST') == 'true':
            feature_id = tester.create_safe_test_feature("full-test")
            branch_name = tester.create_safe_test_branch("full-test")
            
        # Генерируем отчёт
        tester.generate_report()


if __name__ == "__main__":
    main()