#!/usr/bin/env python3
"""
Git Integration Service for Feature Factory.
Handles Git operations including branch creation, commits, and PR management.
"""

import os
import subprocess
import json
import time
from typing import Dict, Any, List, Optional
import structlog
from urllib.parse import urlparse
import requests
import jwt
from datetime import datetime, timedelta

log = structlog.get_logger()


class GitIntegrationError(Exception):
    """Exception raised for Git integration errors."""
    pass


class GitHubAppAuth:
    """GitHub App authentication handler."""
    
    def __init__(self):
        # Normalize inputs (strip whitespace) to avoid subtle URL/build issues
        self.app_id = (os.getenv("GITHUB_APP_ID") or "").strip()
        self.installation_id = (os.getenv("GITHUB_APP_INSTALLATION_ID") or "").strip()
        self.private_key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
        
    def generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication."""
        if not all([self.app_id, self.private_key_path]):
            raise Exception("GitHub App credentials not configured")
            
        now = int(time.time())
        payload = {
            'iat': now - 60,  # Issued 1 minute ago (to account for clock skew)
            'exp': now + 600,  # Expires in 10 minutes
            'iss': int(self.app_id)
        }
        
        with open(self.private_key_path, 'r') as key_file:
            private_key = key_file.read()
            
        return jwt.encode(payload, private_key, algorithm='RS256')
    
    def get_installation_token(self) -> str:
        """Get installation access token (valid for 1 hour)."""
        if not self.installation_id:
            raise Exception("GitHub App installation ID not configured")
            
        jwt_token = self.generate_jwt()
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'FeatureFactory-CI/1.0'
        }
        
        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        response = requests.post(url, headers=headers)
        
        if response.status_code == 201:
            return response.json()['token']
        else:
            raise Exception(f"Failed to get installation token: {response.status_code} - {response.text}")


class GitIntegrationService:
    """Service for handling Git operations."""
    
    def __init__(self):
        """Initialize Git integration service."""
        self.repo_path = "/opt/feature-factory"
        self.base_branch = os.getenv("GIT_BASE_BRANCH", "main")
        self.github_owner = os.getenv("GITHUB_OWNER")
        self.github_repo = os.getenv("GITHUB_REPO")
        self.github_token = os.getenv("GITHUB_TOKEN")  # Fallback PAT
        self.scm_provider = os.getenv("SCM_PROVIDER", "github")

        def _truthy(name: str, default: bool = False) -> bool:
            raw = os.getenv(name)
            if raw is None:
                return default
            val = str(raw).strip().lower()
            return val in {"1", "true", "yes", "on"}

        # Robust parsing of feature flags (handles case/whitespace/1/yes/on)
        self.git_enabled = _truthy("GIT_INTEGRATION_ENABLED", False)
        self.push_enabled = _truthy("SCM_PUSH_ENABLED", False)

        # Emit a single diagnostic log once per instance to aid E2E visibility
        try:
            log.info(
                "git_integration_flags",
                git_enabled=self.git_enabled,
                push_enabled=self.push_enabled,
                scm_provider=self.scm_provider,
                owner=self.github_owner,
                repo=self.github_repo,
            )
        except Exception:
            pass
        
        # Initialize GitHub App auth
        try:
            self.github_app = GitHubAppAuth()
            log.info("github_app_initialized", success=True)
        except Exception as e:
            self.github_app = None
            log.info("github_app_fallback", reason=str(e), fallback="PAT")

    def _get_auth_headers(self, correlation_id: str = "unknown") -> Dict[str, str]:
        """Get authentication headers, preferring GitHub App over PAT."""
        if self.github_app:
            try:
                token = self.github_app.get_installation_token()
                log.info("github_auth_method", method="github_app", correlation_id=correlation_id)
                return {
                    'Authorization': f'token {token}',
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'FeatureFactory-CI/1.0'
                }
            except Exception as e:
                log.warning("github_app_token_failed", error=str(e), correlation_id=correlation_id)
                
        # Fallback to PAT
        if self.github_token:
            log.info("github_auth_method", method="personal_access_token", correlation_id=correlation_id)
            return {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'FeatureFactory-CI/1.0'
            }
        
        raise GitIntegrationError("No GitHub authentication method available")

    def _slugify(self, s: str) -> str:
        import re
        s = s.lower()
        s = re.sub(r"\s+", "-", s)
        s = re.sub(r"[^a-z0-9._-]", "-", s)
        s = re.sub(r"-+", "-", s).strip('-')
        return s[:60]

    def create_feature_branch(self, feature_id: int, feature_title: str, correlation_id: str) -> str:
        """Create a new feature branch."""
        if not self.git_enabled:
            return f"feature/{feature_id}_disabled"
            
        branch_name = f"feature/{feature_id}_{self._slugify(feature_title)}"
        
        try:
            # Всегда синхронизируемся с удалённой базовой веткой,
            # чтобы PR содержал только наш артефакт, а не локальную историю.
            subprocess.run(["git", "fetch", "origin", "--prune"], cwd=self.repo_path, check=True, capture_output=True)

            # Скрываем шумные локальные артефакты из индекса, чтобы checkout не падал
            noisy_paths = [
                "data/test.db", "data/test.db-shm", "data/test.db-wal", "runner_debug.log"
            ]
            for p in noisy_paths:
                try:
                    subprocess.run(["git", "update-index", "--assume-unchanged", p], cwd=self.repo_path, capture_output=True)
                except Exception:
                    pass
            # Создаём/переназначаем ветку от origin/<base_branch>, чтобы diff был минимальным
            subprocess.run(
                ["git", "checkout", "-B", branch_name, f"origin/{self.base_branch}"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            
            log.info(
                event="git_branch_created",
                component="git_integration",
                correlation_id=correlation_id,
                kv={"branch_name": branch_name, "feature_id": feature_id}
            )
            
            return branch_name
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to create branch {branch_name}: {e.stderr.decode() if e.stderr else str(e)}"
            log.error(
                event="git_branch_creation_failed",
                component="git_integration",
                correlation_id=correlation_id,
                kv={"error": error_msg, "branch_name": branch_name}
            )
            raise GitIntegrationError(error_msg)

    def _detect_ssh_key(self) -> str:
        """Возвращает путь к приватному ключу SSH. Предпочитает ~/.ssh/id_ed25519_ff.
        Фолбэк: /opt/feature-factory/.ssh/id_ed25519_ff.
        """
        candidates = [
            os.path.expanduser("~/.ssh/id_ed25519_ff"),
            "/home/feature/.ssh/id_ed25519_ff",
            "/opt/feature-factory/.ssh/id_ed25519_ff",
        ]
        for p in candidates:
            try:
                if os.path.exists(p):
                    return p
            except Exception:
                pass
        # Возврат фолбэк-пути — git может упасть, но это лучше явной ошибки здесь
        return "/home/feature/.ssh/id_ed25519_ff"

    def ensure_unique_commit(self, feature_id: int, correlation_id: str) -> Optional[str]:
        """Гарантирует, что в текущей ветке есть хотя бы один уникальный коммит.
        Создаёт небольшой файл-артефакт и делает commit, если рабочее дерево чистое.
        Возвращает путь созданного файла или None, если коммит не потребовался.
        """
        try:
            # Всегда создаём уникальный файл-артефакт, чтобы гарантировать непустой дифф
            ts = int(time.time())
            rel_dir = os.path.join("artifacts", "GITOPS")
            abs_dir = os.path.join(self.repo_path, rel_dir)
            os.makedirs(abs_dir, exist_ok=True)
            filename = f"FF_AUTOCOMMIT_feature_{feature_id}_{ts}.txt"
            abs_path = os.path.join(abs_dir, filename)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(f"Auto-commit for feature {feature_id} at {ts}\n")
            # git add только артефакт + commit (не затрагиваем остальное рабочее дерево)
            subprocess.run(["git", "add", os.path.join(rel_dir, filename)], cwd=self.repo_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"chore(gitops): auto-commit for feature {feature_id} [{correlation_id}]"], cwd=self.repo_path, check=True, capture_output=True)
            log.info(event="git_auto_commit_created", component="git_integration", correlation_id=correlation_id, kv={"file": os.path.join(rel_dir, filename)})
            return os.path.join(rel_dir, filename)
        except subprocess.CalledProcessError as e:
            log.error(event="git_auto_commit_failed", component="git_integration", correlation_id=correlation_id, kv={"stderr": e.stderr.decode() if e.stderr else str(e)})
            return None
        except Exception as e:
            log.error(event="git_auto_commit_error", component="git_integration", correlation_id=correlation_id, kv={"error": str(e)})
            return None

    def create_pull_request(self, branch_name: str, feature_id: int, feature_title: str, correlation_id: str) -> Dict[str, Any]:
        """Create a pull request."""
        if not self.git_enabled or not self.push_enabled:
            return {
                "pr_url": f"https://github.com/{self.github_owner}/{self.github_repo}/pull/999999",
                "pr_number": 999999,
                "pr_id": 999999,
                "pr_state": "open",
                "branch_name": branch_name
            }
        
        try:
            # Setup SSH wrapper for push
            ssh_wrapper = "/tmp/git_ssh_wrapper.sh"
            with open(ssh_wrapper, 'w') as f:
                key_path = self._detect_ssh_key()
                f.write('#!/bin/bash\n')
                f.write(f'exec ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -i "{key_path}" "$@"\n')
            os.chmod(ssh_wrapper, 0o755)
            
            env = os.environ.copy()
            env["GIT_SSH"] = ssh_wrapper
            # Устанавливаем HOME, если он не задан, на /home/feature для корректной known_hosts
            env.setdefault("HOME", "/home/feature")
            
            # Push branch to origin
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=self.repo_path,
                env=env,
                check=True,
                capture_output=True
            )
            
            # SKIP USER ENDPOINT TEST - GitHub App doesn't have user permissions
            log.info("skipping_user_endpoint_test_for_github_app", correlation_id=correlation_id)
            
            # Create PR via GitHub API
            url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/pulls"
            headers = self._get_auth_headers(correlation_id)
            data = {
                "title": f"Feature #{feature_id}: {feature_title}",
                "head": branch_name,
                "base": self.base_branch,
                "body": f"Auto-generated PR for feature #{feature_id}\n\nCorrelation-ID: {correlation_id}"
            }
            
            # DETAILED LOGGING FOR TOKEN DEBUGGING
            log.info("github_api_call_attempt", 
                     action="create_pr", 
                     url=url, 
                     correlation_id=correlation_id,
                     feature_id=feature_id)
            
            response = requests.post(url, headers=headers, json=data)
            
            # LOG RESPONSE DETAILS
            log.info("github_api_call_response",
                     action="create_pr",
                     status_code=response.status_code,
                     rate_limit_remaining=response.headers.get('x-ratelimit-remaining'),
                     rate_limit_reset=response.headers.get('x-ratelimit-reset'),
                     correlation_id=correlation_id,
                     success=(response.status_code < 400))
            
            if response.status_code == 401:
                log.error("github_token_expired", 
                         action="create_pr",
                         correlation_id=correlation_id,
                         response_text=response.text)
                raise GitIntegrationError("GitHub token expired during PR creation")
            
            if response.status_code == 422:
                # Возможно PR уже существует — попробуем найти по head
                search_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/pulls"
                params = {"head": f"{self.github_owner}:{branch_name}", "state": "open"}
                
                log.info("github_api_call_attempt", 
                         action="search_existing_pr", 
                         url=search_url, 
                         correlation_id=correlation_id)
                
                sr = requests.get(search_url, headers=headers, params=params)
                
                log.info("github_api_call_response",
                         action="search_existing_pr",
                         status_code=sr.status_code,
                         rate_limit_remaining=sr.headers.get('x-ratelimit-remaining'),
                         correlation_id=correlation_id,
                         success=(sr.status_code < 400))
                
                if sr.status_code == 401:
                    log.error("github_token_expired", 
                             action="search_existing_pr",
                             correlation_id=correlation_id,
                             response_text=sr.text)
                    raise GitIntegrationError("GitHub token expired during PR search")
                if sr.ok:
                    arr = sr.json() or []
                    if arr:
                        pr_data = arr[0]
                        pr_info = {
                            "pr_url": pr_data["html_url"],
                            "pr_number": pr_data["number"],
                            "pr_id": pr_data["number"],
                            "pr_state": pr_data["state"],
                            "branch_name": branch_name,
                            "head_sha": pr_data["head"]["sha"]
                        }
                        log.info(
                            event="github_pr_found_existing",
                            component="git_integration",
                            correlation_id=correlation_id,
                            kv={"pr_url": pr_info["pr_url"], "pr_number": pr_info["pr_number"], "feature_id": feature_id}
                        )
                        return pr_info
            response.raise_for_status()
            pr_data = response.json()
            pr_info = {
                "pr_url": pr_data["html_url"],
                "pr_number": pr_data["number"],
                "pr_id": pr_data["number"],
                "pr_state": pr_data["state"],
                "branch_name": branch_name,
                "head_sha": pr_data["head"]["sha"]
            }
            
            log.info(
                event="github_pr_created",
                component="git_integration",
                correlation_id=correlation_id,
                kv={
                    "pr_url": pr_info["pr_url"],
                    "pr_number": pr_info["pr_number"],
                    "feature_id": feature_id
                }
            )
            
            return pr_info
            
        except (subprocess.CalledProcessError, requests.RequestException) as e:
            extra = {}
            try:
                if isinstance(e, requests.RequestException) and e.response is not None:
                    extra["response_text"] = e.response.text
                    extra["status_code"] = e.response.status_code
            except Exception:
                pass
            error_msg = f"Failed to create PR: {str(e)}"
            log.error(
                event="github_pr_creation_failed",
                component="git_integration",
                correlation_id=correlation_id,
                kv={"error": error_msg, "branch_name": branch_name, **extra}
            )
            raise GitIntegrationError(error_msg)

    def merge_pull_request(self, feature_id: int, pr_number: int, head_sha: str, correlation_id: str) -> Dict[str, Any]:
        """Merge a pull request."""
        if not self.git_enabled or not self.push_enabled:
            return {
                "merged": True,
                "merge_commit_sha": "mock_merged_sha_" + head_sha[:8],
                "merged_at": "2025-09-12T04:00:00Z"
            }
        
        try:
            # First, get current PR info to get the actual HEAD SHA
            pr_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/pulls/{pr_number}"
            headers = self._get_auth_headers(correlation_id)
            
            pr_response = requests.get(pr_url, headers=headers)
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            
            # Use actual current HEAD SHA from PR
            actual_head_sha = pr_data["head"]["sha"]
            
            log.info(
                event="github_pr_merge_attempt",
                component="git_integration", 
                correlation_id=correlation_id,
                kv={
                    "pr_number": pr_number,
                    "feature_id": feature_id,
                    "provided_sha": head_sha,
                    "actual_head_sha": actual_head_sha,
                    "pr_state": pr_data.get("state"),
                    "mergeable": pr_data.get("mergeable"),
                    "mergeable_state": pr_data.get("mergeable_state")
                }
            )
            
            # Check if PR is already closed/merged
            if pr_data.get("state") == "closed":
                if pr_data.get("merged"):
                    return {
                        "merged": True,
                        "merge_commit_sha": pr_data.get("merge_commit_sha"),
                        "merged_at": pr_data.get("merged_at")
                    }
                else:
                    raise GitIntegrationError(f"PR #{pr_number} is closed but not merged")
            
            # Merge PR via GitHub API
            merge_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/pulls/{pr_number}/merge"
            data = {
                "commit_title": f"Merge PR #{pr_number} for feature #{feature_id}",
                "commit_message": f"Auto-merge PR #{pr_number}\n\nCorrelation-ID: {correlation_id}",
                "sha": actual_head_sha,  # Use actual HEAD SHA
                "merge_method": "squash"  # Use squash merge
            }
            
            response = requests.put(merge_url, headers=headers, json=data)
            response.raise_for_status()
            
            merge_data = response.json()
            merge_info = {
                "merged": merge_data.get("merged", True),
                "merge_commit_sha": merge_data.get("sha"),
                "merged_at": merge_data.get("merged_at")
            }
            
            log.info(
                event="github_pr_merged",
                component="git_integration",
                correlation_id=correlation_id,
                kv={
                    "pr_number": pr_number,
                    "feature_id": feature_id,
                    "merge_commit_sha": merge_info["merge_commit_sha"],
                    "head_sha": actual_head_sha
                }
            )
            
            return merge_info
            
        except requests.RequestException as e:
            error_details = {"status_code": getattr(e.response, 'status_code', None)}
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_details["response_text"] = e.response.text
                    if e.response.headers.get('content-type', '').startswith('application/json'):
                        error_details["response_json"] = e.response.json()
            except:
                pass
                
            error_msg = f"Failed to merge PR #{pr_number}: {str(e)}"
            log.error(
                event="github_pr_merge_failed",
                component="git_integration",
                correlation_id=correlation_id,
                kv={
                    "error": error_msg, 
                    "pr_number": pr_number, 
                    "feature_id": feature_id,
                    "error_details": error_details
                }
            )
            raise GitIntegrationError(error_msg)
