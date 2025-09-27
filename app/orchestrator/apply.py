#!/usr/bin/env python3
"""
Apply module for orchestrator.
Handles application of validated artifacts.
"""

import os
import yaml
import subprocess
import json
import sqlite3
import re
import shutil
from typing import Dict, Any, List
import structlog
from app.logging_helpers import log_job, log_http, log_db
from app.orchestrator.gates import ManifestValidator
from app.db.guard import get_db_connection_string

# Настройка логгера
log = structlog.get_logger()

class ArtifactApplier:
    """Applier for validated artifacts."""
    
    def __init__(self):
        """Initialize applier."""
        self.validator = ManifestValidator()
    
    def apply_artifact(self, manifest: Dict[str, Any], artifacts_dir: str) -> bool:
        """
        Apply validated artifact.
        
        Args:
            manifest (Dict[str, Any]): Validated manifest
            artifacts_dir (str): The temporary directory containing the generated artifacts
            
        Returns:
            bool: True if applied successfully
        """
        try:
            package_id = manifest.get("package_contract", {}).get("package_id", "unknown")
            files_to_apply = manifest.get("files", [])
            
            log.info(
                event="artifact_apply_started",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "package_id": package_id,
                    "files_count": len(files_to_apply),
                    "artifacts_dir": artifacts_dir
                }
            )
            
            # Копируем файлы из временного каталога в постоянные местоположения
            for file_name in files_to_apply:
                source_path = os.path.join(artifacts_dir, file_name)
                
                # Определяем целевой путь
                # Предполагаем, что file_name уже является относительным путем к корню проекта
                target_path = os.path.join("/opt/feature-factory/", file_name)
                
                # Создаем необходимые директории
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # Копируем файл
                shutil.copy2(source_path, target_path)
                
                log.info(
                    event="file_applied",
                    component="orchestrator",
                    agent_role="Orchestrator",
                    kv={
                        "source": source_path,
                        "target": target_path
                    }
                )
            
            # Auto-register new API routers
            self._register_api_routers(files_to_apply)
            
            # Save package to database
            self._save_package_to_db(manifest)
            
            # Trigger AutoIndex
            self._trigger_autoindex()
            
            log.info(
                event="artifact_apply_finished",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "package_id": package_id,
                    "status": "SUCCESS"
                }
            )
            
            return True
        except Exception as e:
            log.error(
                event="artifact_apply_failed",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "error": str(e)
                },
                stack=True
            )
            return False
    
    def _save_package_to_db(self, manifest: Dict[str, Any]):
        """
        Сохраняет пакет в базу данных.
        
        Args:
            manifest (Dict[str, Any]): Валидированный манифест
        """
        try:
            package_contract = manifest.get("package_contract", {})
            package_id = package_contract.get("package_id", "unknown")
            
            # Получаем строку подключения к БД
            db_url = get_db_connection_string()
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
                
                with sqlite3.connect(db_path) as conn:
                    # Сохраняем пакет
                    file_paths = json.dumps(manifest.get("files", []))
                    conn.execute(
                        "INSERT OR REPLACE INTO packages (package_id, package_contract, file_paths) VALUES (?, ?, ?)",
                        (package_id, json.dumps(package_contract), file_paths)
                    )
                    
                    # Создаем запись в doc_index для документации
                    doc_id = f"doc-{package_id}"
                    title = f"Documentation for {package_id}"
                    content = f"Package {package_id} documentation"
                    
                    conn.execute(
                        "INSERT OR REPLACE INTO doc_index (doc_id, package_id, title, content) VALUES (?, ?, ?, ?)",
                        (doc_id, package_id, title, content)
                    )
                    
                    conn.commit()
                    
                    log.info(
                        event="package_saved",
                        component="orchestrator",
                        agent_role="Orchestrator",
                        kv={
                            "package_id": package_id,
                            "files_count": len(manifest.get("files", []))
                        }
                    )
        except Exception as e:
            log.error(
                event="package_save_failed",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "error": str(e)
                }
            )
    
    def _trigger_autoindex(self):
        """
        Trigger auto indexing process.
        """
        try:
            log.info(
                event="autoindex_triggered",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "action": "make index"
                }
            )
            subprocess.run(["make", "index"], cwd="/opt/feature-factory", check=True)
        except Exception as e:
            log.error(
                event="index_update_failed",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "error": str(e)
                },
                stack=True
            )
    
    def _register_api_routers(self, files_to_apply: List[str]):
        """
        Automatically register new API routers in main.py
        
        Args:
            files_to_apply: List of files being applied
        """
        try:
            # Find API router files
            api_files = [f for f in files_to_apply if f.startswith('app/api/') and f.endswith('.py') and 'schema' not in f]
            
            if not api_files:
                return
                
            main_py_path = "/opt/feature-factory/app/main.py"
            
            # Read current main.py
            with open(main_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Track if we made changes
            changes_made = False
            
            for api_file in api_files:
                # Extract module name (e.g., app/api/hello.py -> hello)
                module_name = os.path.splitext(os.path.basename(api_file))[0]
                import_name = f"app.api.{module_name}"
                router_var = f"{module_name}_router"
                
                # Skip if already imported
                if f"from {import_name} import router as {router_var}" in content:
                    continue
                    
                # Add import after existing API imports
                import_line = f"    from {import_name} import router as {router_var}"
                include_line = f"    app.include_router({router_var})"
                
                # Find the ping router section and add after it
                ping_section = "try:\n    from app.api.ping import router as ping_router\n    app.include_router(ping_router)\nexcept Exception:\n    # Нет ping-роутера — ничего страшного, он может появиться как артефакт\n    pass"
                
                if ping_section in content:
                    # Add new router after ping section
                    new_section = f"{ping_section}\n\n# Auto-generated router for {module_name}\ntry:\n{import_line}\n{include_line}\nexcept Exception:\n    # {module_name} router not available yet\n    pass"
                    content = content.replace(ping_section, new_section)
                    changes_made = True
                    
                    log.info(
                        event="router_registered",
                        component="orchestrator",
                        agent_role="Orchestrator",
                        kv={
                            "module": module_name,
                            "router": router_var
                        }
                    )
            
            # Write back if changes were made
            if changes_made:
                with open(main_py_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                log.info(
                    event="main_py_updated",
                    component="orchestrator", 
                    agent_role="Orchestrator",
                    kv={
                        "routers_added": len([f for f in api_files if f"app.api.{os.path.splitext(os.path.basename(f))[0]}" not in content])
                    }
                )
                
        except Exception as e:
            log.error(
                event="router_registration_failed",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "error": str(e)
                },
                stack=True
            )
    
    def process_response(self, manifest: Dict[str, Any], artifacts_dir: str, task_role: str = None) -> bool:
        """
        Process response from agent.
        
        Args:
            manifest (Dict[str, Any]): Validated manifest
            artifacts_dir (str): The temporary directory containing the generated artifacts
            task_role (str): Role of the task (e.g., "Architect", "Dev", "QA", "Scribe")
            
        Returns:
            bool: True if processed successfully
        """
        try:
            # Log successful validation
            package_id = manifest.get("package_contract", {}).get("package_id", "unknown")
            
            log.info(
                event="artifact_validated",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "package_id": package_id
                }
            )
            
            # Apply artifact
            return self.apply_artifact(manifest, artifacts_dir)
        except ValueError as e:
            # Log rejected artifact
            log.error(
                event="artifact_rejected",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "reason": str(e)
                }
            )
            return False
        except Exception as e:
            # Log unexpected error
            log.error(
                event="artifact_process_failed",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "error": str(e)
                },
                stack=True
            )
            return False
    
    