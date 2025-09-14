#!/usr/bin/env python3
"""
Gates module for orchestrator.
Handles validation of artifact manifests and package contracts.
"""

import yaml
import json
import jsonschema
import subprocess
import os
import re
from typing import Dict, Any, Optional, List
import structlog
from app.logging_helpers import log_job, log_http, log_db

# Настройка логгера
log = structlog.get_logger()

class ManifestValidator:
    """Validator for artifact manifests and package contracts."""
    
    def __init__(self, package_contract_schema_path: str = "cortex/docs/package_contract.schema.json",
                 artifact_manifest_schema_path: str = "configs/schemas/artifact_manifest.schema.json"):
        """Initialize validator with schema paths."""
        self.package_contract_schema_path = package_contract_schema_path
        self.artifact_manifest_schema_path = artifact_manifest_schema_path
        self.package_contract_schema = self._load_schema(self.package_contract_schema_path)
        self.artifact_manifest_schema = self._load_schema(self.artifact_manifest_schema_path)

    def _load_schema(self, path: str) -> Dict[str, Any]:
        """Load JSON schema for validation."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            log.error("schema_load_failed", path=path, error=str(e))
            raise

    def validate_artifact_manifest_schema(self, manifest: Dict[str, Any]) -> bool:
        """
        Validate artifact manifest against its schema.
        
        Args:
            manifest (Dict[str, Any]): Parsed artifact manifest
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            jsonschema.validate(instance=manifest, schema=self.artifact_manifest_schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            log.error(
                event="artifact_rejected",
                component="orchestrator",
                agent_role="Gate",
                kv={
                    "reason": f"Artifact manifest schema validation failed: {str(e)}",
                    "validation_error": str(e)
                }
            )
            return False
        except Exception as e:
            log.error(
                event="artifact_rejected",
                component="orchestrator",
                agent_role="Gate",
                kv={
                    "reason": f"Artifact manifest schema validation error: {str(e)}",
                    "error": str(e)
                }
            )
            return False

    def validate_file_paths(self, manifest: Dict[str, Any], run_id: str) -> bool:
        """
        Validate that all file paths in the manifest are within the allowed temporary directory.
        
        Args:
            manifest (Dict[str, Any]): Parsed artifact manifest
            run_id (str): The run ID to construct the allowed temporary directory path
            
        Returns:
            bool: True if all paths are safe, False otherwise
        """
        allowed_dir_prefix = os.path.abspath(f"/opt/feature-factory/tmp/{run_id}/")
        
        for file_path in manifest.get("files", []):
            abs_file_path = os.path.abspath(os.path.join(allowed_dir_prefix, file_path))
            if not abs_file_path.startswith(allowed_dir_prefix):
                log.error(
                    event="artifact_rejected",
                    component="orchestrator",
                    agent_role="Gate",
                    kv={
                        "reason": f"Unsafe file path detected: {file_path}",
                        "unsafe_path": file_path,
                        "allowed_prefix": allowed_dir_prefix
                    }
                )
                return False
        return True

    def scan_for_secrets(self, artifacts_dir: str) -> List[str]:
        """
        Scan all files in the artifacts directory for common secret patterns.
        
        Args:
            artifacts_dir (str): The directory containing the generated artifacts
            
        Returns:
            List[str]: A list of detected secret patterns (e.g., "API_KEY", "PASSWORD")
        """
        detected_secrets = []
        secret_patterns = {
            "API_KEY": r'(api_key|API_KEY|token|TOKEN|secret|SECRET)[\s_=\:\"]*[a-zA-Z0-9_\-]{16,}',
            "PASSWORD": r'(password|PASSWORD|pass)[\s_=\:\"]*[a-zA-Z0-9_\-]{8,}',
            "AWS_ACCESS_KEY": r"AKIA[0-9A-Z]{16}",
            "AWS_SECRET_KEY": r"([A-Za-z0-9+/]{40})",
            "PRIVATE_KEY": r"-----BEGIN (RSA|DSA|EC|PGP) PRIVATE KEY-----",
            "BEARER_TOKEN": r"Bearer [A-Za-z0-9_\-\.]{30,}"
        }
        
        for root, _, files in os.walk(artifacts_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for secret_type, pattern in secret_patterns.items():
                            if re.search(pattern, content):
                                detected_secrets.append(secret_type)
                                log.warning(
                                    event="secret_found",
                                    component="orchestrator",
                                    agent_role="Gate",
                                    kv={
                                        "file": file_path,
                                        "secret_type": secret_type
                                    }
                                )
                except Exception as e:
                    log.error(
                        event="file_read_error",
                        component="orchestrator",
                        agent_role="Gate",
                        kv={
                            "file": file_path,
                            "error": str(e)
                        }
                    )
        return list(set(detected_secrets)) # Return unique secret types

    def validate_manifest(self, manifest_text: str) -> Dict[str, Any]:
        """
        Validate artifact manifest.
        
        Args:
            manifest_text (str): YAML text of artifact manifest
            
        Returns:
            Dict[str, Any]: Parsed manifest
            
        Raises:
            ValueError: If manifest is invalid
        """
        try:
            # Parse YAML
            manifest = yaml.safe_load(manifest_text)

            # Должен быть объект с полями files и package_contract (см. schema)
            if manifest is None:
                raise ValueError("No manifest found in response")
            if isinstance(manifest, list):
                # Некорректный формат для нашего случая
                raise ValueError("Manifest must be an object, not a list")
            if not isinstance(manifest, dict):
                raise ValueError("Manifest must be a dictionary")
            return manifest
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ValueError(f"Manifest validation failed: {e}")
    
    def validate_package_contract(self, manifest: Dict[str, Any]) -> bool:
        """
        Validate package contract in manifest.
        
        Args:
            manifest (Dict[str, Any]): Parsed manifest
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check if package_contract exists
            if "package_contract" not in manifest:
                # Package contract is optional in general, but required for Architect tasks
                # We'll check this in the orchestrator based on the task role
                return True
            
            package_contract = manifest["package_contract"]
            # Validate against schema
            jsonschema.validate(instance=package_contract, schema=self.package_contract_schema)
            
            return True
        except jsonschema.exceptions.ValidationError as e:
            log.error(
                event="artifact_rejected",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "reason": f"Package contract validation failed: {str(e)}",
                    "validation_error": str(e)
                }
            )
            return False
        except Exception as e:
            log.error(
                event="artifact_rejected",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "reason": f"Package contract validation error: {str(e)}",
                    "error": str(e)
                }
            )
            return False
    
    def validate_response(self, response_text: str, task_role: str = None) -> Dict[str, Any]:
        """
        Validate entire response for manifest and package contract.
        
        Args:
            response_text (str): Full response text
            task_role (str): Role of the task (e.g., "Architect", "Dev", "QA", "Scribe")
            
        Returns:
            Dict[str, Any]: Parsed and validated manifest
            
        Raises:
            ValueError: If validation fails
        """
        # Extract run_id if present
        run_id = None
        if response_text.startswith("run_id:"):
            first_line = response_text.split('\n', 1)[0]
            run_id = first_line.replace("run_id:", "").strip()
            response_text = response_text.split('\n', 1)[1] if '\n' in response_text else ""
        
        # Extract manifest from response (assuming it's at the beginning)
        lines = response_text.strip().split('\n')
        manifest_lines = []
        in_manifest = False
        found_yaml_block = False
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped == "```yaml" or line_stripped == "```yml":
                in_manifest = True
                found_yaml_block = True
                continue
            elif line_stripped == "```":
                in_manifest = False
                break
            elif in_manifest:
                manifest_lines.append(line)
        
        # If no YAML block found, try to parse the whole response as YAML
        if not found_yaml_block and not manifest_lines:
            # Try to find manifest in the response
            for i, line in enumerate(lines):
                if line.strip() == "```yaml" or line.strip() == "```yml":
                    in_manifest = True
                    found_yaml_block = True
                    continue
                elif line.strip() == "```":
                    in_manifest = False
                    break
                elif in_manifest:
                    manifest_lines.append(line)
        
        if not manifest_lines:
            error_msg = "No manifest found in response"
            log.error(
                event="artifact_rejected",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "reason": error_msg
                }
            )
            raise ValueError(error_msg)
        
        manifest_text = '\n'.join(manifest_lines)
        
        # Validate manifest
        manifest = self.validate_manifest(manifest_text)

        # Validate artifact manifest against its schema
        if not self.validate_artifact_manifest_schema(manifest):
            raise ValueError("Artifact manifest schema validation failed")
        
        # For Architect tasks, package_contract is required
        if task_role == "Architect" and "package_contract" not in manifest:
            error_msg = "Missing package_contract in Architect task response"
            log.error(
                event="artifact_rejected",
                component="orchestrator",
                agent_role="Orchestrator",
                kv={
                    "reason": error_msg
                }
            )
            raise ValueError(error_msg)
        
        # Validate package contract
        if not self.validate_package_contract(manifest):
            raise ValueError("Package contract validation failed")
        
        # Add run_id to manifest if found
        if run_id:
            manifest["run_id"] = run_id
        
        return manifest
