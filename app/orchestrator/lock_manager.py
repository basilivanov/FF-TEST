#!/usr/bin/env python3
"""
Диспетчер Блокировок для управления конкурентностью выполнения фич.

Для MVP обеспечивает строго последовательное выполнение фич, 
но заложена архитектура для будущего интеллектуального параллелизма.
"""

import json
import os
import time
from threading import Lock
from typing import Dict, List, Optional, Set, Tuple
import structlog

logger = structlog.get_logger()


class LockManager:
    """
    Менеджер блокировок ресурсов для контроля конкурентности.
    
    Для MVP поддерживает эксклюзивные блокировки в памяти.
    В будущем может быть расширен для:
    - Блокировок чтения/записи
    - Персистентного хранения блокировок
    - Таймаутов и автоматического освобождения
    """
    
    def __init__(self):
        self._locks: Dict[str, int] = {}  # { 'resource_name': feature_id_locking_it }
        self._mutex = Lock()
        self._feature_locks: Dict[int, Set[str]] = {}  # { feature_id: set_of_locked_resources }
        
    def acquire(self, resource: str, feature_id: int) -> bool:
        """
        Пытается захватить эксклюзивную блокировку ресурса.
        
        Args:
            resource: Название ресурса для блокировки
            feature_id: ID фичи, запрашивающей блокировку
            
        Returns:
            True если блокировка успешно захвачена, False если ресурс уже заблокирован
        """
        with self._mutex:
            if resource in self._locks:
                current_holder = self._locks[resource]
                logger.info(
                    "resource_already_locked",
                    resource=resource,
                    requested_by=feature_id,
                    current_holder=current_holder
                )
                return False
                
            # Захватываем блокировку
            self._locks[resource] = feature_id
            
            # Отслеживаем для этой фичи
            if feature_id not in self._feature_locks:
                self._feature_locks[feature_id] = set()
            self._feature_locks[feature_id].add(resource)
            
            logger.info(
                "resource_locked",
                resource=resource,
                feature_id=feature_id,
                total_locks_for_feature=len(self._feature_locks[feature_id])
            )
            return True
    
    def acquire_multiple(self, resources: List[str], feature_id: int) -> Tuple[bool, List[str]]:
        """
        Пытается захватить несколько блокировок атомарно.
        
        Args:
            resources: Список ресурсов для блокировки
            feature_id: ID фичи, запрашивающей блокировки
            
        Returns:
            Tuple (success, failed_resources):
            - success: True если все блокировки захвачены
            - failed_resources: список ресурсов, которые не удалось заблокировать
        """
        failed_resources = []
        acquired_resources = []
        
        with self._mutex:
            # Сначала проверяем все ресурсы
            for resource in resources:
                if resource in self._locks and self._locks[resource] != feature_id:
                    failed_resources.append(resource)
            
            if failed_resources:
                logger.info(
                    "multiple_acquire_failed",
                    feature_id=feature_id,
                    requested_resources=resources,
                    failed_resources=failed_resources
                )
                return False, failed_resources
            
            # Захватываем все ресурсы
            if feature_id not in self._feature_locks:
                self._feature_locks[feature_id] = set()
                
            for resource in resources:
                self._locks[resource] = feature_id
                self._feature_locks[feature_id].add(resource)
                acquired_resources.append(resource)
            
            logger.info(
                "multiple_acquire_success",
                feature_id=feature_id,
                acquired_resources=acquired_resources,
                total_locks_for_feature=len(self._feature_locks[feature_id])
            )
            return True, []
    
    def release(self, resource: str, feature_id: int) -> bool:
        """
        Освобождает блокировку ресурса.
        
        Args:
            resource: Название ресурса для освобождения
            feature_id: ID фичи, освобождающей блокировку
            
        Returns:
            True если блокировка была освобождена, False если фича не владела ресурсом
        """
        with self._mutex:
            current_holder = self._locks.get(resource)
            if current_holder != feature_id:
                logger.warning(
                    "release_failed_not_owner",
                    resource=resource,
                    feature_id=feature_id,
                    current_holder=current_holder
                )
                return False
            
            # Освобождаем блокировку
            del self._locks[resource]
            
            # Убираем из отслеживания фичи
            if feature_id in self._feature_locks:
                self._feature_locks[feature_id].discard(resource)
                if not self._feature_locks[feature_id]:
                    del self._feature_locks[feature_id]
            
            logger.info(
                "resource_released",
                resource=resource,
                feature_id=feature_id
            )
            return True
    
    def release_all_for_feature(self, feature_id: int) -> List[str]:
        """
        Освобождает все блокировки, принадлежащие указанной фиче.
        
        Args:
            feature_id: ID фичи для освобождения всех её блокировок
            
        Returns:
            Список освобожденных ресурсов
        """
        released_resources = []
        
        with self._mutex:
            if feature_id not in self._feature_locks:
                logger.info(
                    "no_locks_to_release",
                    feature_id=feature_id
                )
                return released_resources
            
            # Освобождаем все ресурсы фичи
            for resource in self._feature_locks[feature_id].copy():
                if resource in self._locks and self._locks[resource] == feature_id:
                    del self._locks[resource]
                    released_resources.append(resource)
            
            # Очищаем отслеживание фичи
            del self._feature_locks[feature_id]
            
            logger.info(
                "all_locks_released_for_feature",
                feature_id=feature_id,
                released_resources=released_resources
            )
            
        return released_resources
    
    def get_status(self) -> Dict[str, any]:
        """
        Возвращает текущий статус всех блокировок.
        
        Returns:
            Словарь с информацией о текущих блокировках
        """
        with self._mutex:
            return {
                "active_locks": dict(self._locks),
                "features_with_locks": {
                    fid: list(resources) 
                    for fid, resources in self._feature_locks.items()
                },
                "total_locked_resources": len(self._locks),
                "total_features_with_locks": len(self._feature_locks)
            }
    
    def is_resource_locked(self, resource: str) -> Optional[int]:
        """
        Проверяет, заблокирован ли ресурс.
        
        Args:
            resource: Название ресурса
            
        Returns:
            ID фичи, которая заблокировала ресурс, или None если ресурс свободен
        """
        with self._mutex:
            return self._locks.get(resource)
    
    def get_feature_locks(self, feature_id: int) -> List[str]:
        """
        Возвращает список ресурсов, заблокированных указанной фичей.
        
        Args:
            feature_id: ID фичи
            
        Returns:
            Список заблокированных ресурсов
        """
        with self._mutex:
            return list(self._feature_locks.get(feature_id, set()))


def load_resource_manifest(manifest_path: str = "/opt/feature-factory/configs/resource_manifest.yaml") -> Dict:
    """
    Загружает манифест ресурсов из YAML файла.
    
    Args:
        manifest_path: Путь к файлу манифеста
        
    Returns:
        Словарь с описанием ресурсов
    """
    try:
        import yaml
        
        if not os.path.exists(manifest_path):
            logger.warning(
                "resource_manifest_not_found",
                path=manifest_path
            )
            return {"resources": []}
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
            
        logger.info(
            "resource_manifest_loaded",
            path=manifest_path,
            resources_count=len(manifest.get("resources", []))
        )
        
        return manifest
        
    except Exception as e:
        logger.error(
            "resource_manifest_load_failed",
            path=manifest_path,
            error=str(e)
        )
        return {"resources": []}


def parse_resource_locks_from_plan(plan_data: Dict) -> List[Dict[str, str]]:
    """
    Извлекает требования к блокировкам ресурсов из плана фичи.
    
    Args:
        plan_data: Данные плана фичи из plan.dsl.json
        
    Returns:
        Список требований к блокировкам в формате [{"resource": "name", "mode": "exclusive"}]
    """
    return plan_data.get("resource_locks", [])


# Создаем единый экземпляр для всего приложения
lock_manager = LockManager()