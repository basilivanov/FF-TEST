# Gate Validation Examples for FeatureFactory

import json
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class GateDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"

class RejectCode(Enum):
    ROL_MISMATCH = "ROL_MISMATCH"
    PROMPT_SIG_MISSING = "PROMPT_SIG_MISSING" 
    CONTRACT_MISSING = "CONTRACT_MISSING"
    INVALID_CONTRACT_SCHEMA = "INVALID_CONTRACT_SCHEMA"
    INVALID_PROMPT_HASH = "INVALID_PROMPT_HASH"

@dataclass
class GateResponse:
    decision: GateDecision
    confidence: float  # 0.0 to 1.0
    reasons: List[str]
    reject_code: Optional[RejectCode] = None

# Example Gate Validation Functions
class GateValidator:
    """Gate validation examples for different scenarios"""
    
    def __init__(self):
        self.expected_prompt_hashes = {
            "agents/prompts/architect.md": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
            "agents/prompts/dev.md": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7",
            "agents/prompts/qa.md": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
        }
    
    def validate_architect_response(self, response: Dict[str, Any]) -> GateResponse:
        """Validate Architect role response"""
        reasons = []
        confidence = 1.0
        
        # Check role match
        if response.get("role") != "Architect":
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.99,
                reasons=["Role mismatch: expected Architect"],
                reject_code=RejectCode.ROL_MISMATCH
            )
        
        # Check prompt signature
        prompt_id = response.get("prompt_id")
        prompt_sha256 = response.get("prompt_sha256")
        
        if not prompt_id or not prompt_sha256:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.98,
                reasons=["Missing prompt signature fields"],
                reject_code=RejectCode.PROMPT_SIG_MISSING
            )
        
        # Validate prompt hash
        expected_hash = self.expected_prompt_hashes.get(prompt_id)
        if expected_hash and prompt_sha256 != expected_hash:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.97,
                reasons=[f"Invalid prompt hash for {prompt_id}"],
                reject_code=RejectCode.INVALID_PROMPT_HASH
            )
        
        # Check package_contract presence
        package_contract = response.get("package_contract")
        if not package_contract:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.95,
                reasons=["Missing package_contract"],
                reject_code=RejectCode.CONTRACT_MISSING
            )
        
        # Validate package_contract schema
        contract_validation = self._validate_package_contract(package_contract)
        if not contract_validation["valid"]:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.90,
                reasons=[f"Invalid package_contract: {contract_validation['error']}"],
                reject_code=RejectCode.INVALID_CONTRACT_SCHEMA
            )
        
        # All validations passed
        reasons.append("Role matches expected: Architect")
        reasons.append("Valid prompt signature")
        reasons.append("Package contract present and valid")
        
        return GateResponse(
            decision=GateDecision.ALLOW,
            confidence=confidence,
            reasons=reasons
        )
    
    def validate_dev_response(self, response: Dict[str, Any]) -> GateResponse:
        """Validate Dev role response"""
        reasons = []
        
        # Check role match
        if response.get("role") != "Dev":
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.99,
                reasons=["Role mismatch: expected Dev"],
                reject_code=RejectCode.ROL_MISMATCH
            )
        
        # Check artifact_manifest
        artifact_manifest = response.get("artifact_manifest")
        if not artifact_manifest:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.95,
                reasons=["Missing artifact_manifest"],
                reject_code=RejectCode.CONTRACT_MISSING
            )
        
        # Validate artifact_manifest schema
        manifest_validation = self._validate_artifact_manifest(artifact_manifest)
        if not manifest_validation["valid"]:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.85,
                reasons=[f"Invalid artifact_manifest: {manifest_validation['error']}"],
                reject_code=RejectCode.INVALID_CONTRACT_SCHEMA
            )
        
        # Check for secrets in files
        secret_check = self._check_for_secrets(artifact_manifest.get("files", []))
        if secret_check["found_secrets"]:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.80,
                reasons=[f"Found secrets in code: {secret_check['locations']}"],
                reject_code=RejectCode.INVALID_CONTRACT_SCHEMA
            )
        
        reasons.extend([
            "Role matches expected: Dev",
            "Artifact manifest present and valid",
            "No secrets detected in code"
        ])
        
        return GateResponse(
            decision=GateDecision.ALLOW,
            confidence=0.92,
            reasons=reasons
        )
    
    def validate_qa_response(self, response: Dict[str, Any]) -> GateResponse:
        """Validate QA role response"""
        reasons = []
        
        # Check role match
        if response.get("role") != "QA":
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.99,
                reasons=["Role mismatch: expected QA"],
                reject_code=RejectCode.ROL_MISMATCH
            )
        
        # Check QA report
        qa_report = response.get("qa_report")
        if not qa_report:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.95,
                reasons=["Missing qa_report"],
                reject_code=RejectCode.CONTRACT_MISSING
            )
        
        # Validate QA report structure
        report_validation = self._validate_qa_report(qa_report)
        if not report_validation["valid"]:
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.88,
                reasons=[f"Invalid qa_report: {report_validation['error']}"],
                reject_code=RejectCode.INVALID_CONTRACT_SCHEMA
            )
        
        # Check for actual testing evidence
        if qa_report.get("result") == "PASS" and not qa_report.get("test_protocols"):
            return GateResponse(
                decision=GateDecision.DENY,
                confidence=0.75,
                reasons=["PASS result without test protocols - insufficient evidence"],
                reject_code=RejectCode.INVALID_CONTRACT_SCHEMA
            )
        
        reasons.extend([
            "Role matches expected: QA",
            "QA report present and valid",
            "Sufficient testing evidence provided"
        ])
        
        return GateResponse(
            decision=GateDecision.ALLOW,
            confidence=0.89,
            reasons=reasons
        )
    
    def _validate_package_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Validate package_contract schema"""
        required_fields = ["package_id", "summary", "files_layout"]
        
        for field in required_fields:
            if field not in contract:
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # Validate package_id format
        package_id = contract["package_id"]
        if not isinstance(package_id, str) or not package_id.strip():
            return {"valid": False, "error": "package_id must be non-empty string"}
        
        # Validate summary
        summary = contract["summary"]
        if not isinstance(summary, str) or len(summary) < 10:
            return {"valid": False, "error": "summary must be at least 10 characters"}
        
        return {"valid": True}
    
    def _validate_artifact_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Validate artifact_manifest schema"""
        required_fields = ["package_id", "files"]
        
        for field in required_fields:
            if field not in manifest:
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # Validate files list
        files = manifest["files"]
        if not isinstance(files, list):
            return {"valid": False, "error": "files must be a list"}
        
        if len(files) == 0:
            return {"valid": False, "error": "files list cannot be empty"}
        
        # Validate file paths
        for file_path in files:
            if not isinstance(file_path, str):
                return {"valid": False, "error": "All file paths must be strings"}
            
            if not file_path.startswith("/opt/feature-factory/"):
                return {"valid": False, "error": f"Invalid file path: {file_path}"}
        
        return {"valid": True}
    
    def _validate_qa_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Validate qa_report schema"""
        required_fields = ["result", "checks"]
        
        for field in required_fields:
            if field not in report:
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # Validate result
        result = report["result"]
        if result not in ["PASS", "FAIL"]:
            return {"valid": False, "error": "result must be PASS or FAIL"}
        
        # Validate checks
        checks = report["checks"]
        if not isinstance(checks, list):
            return {"valid": False, "error": "checks must be a list"}
        
        if len(checks) == 0:
            return {"valid": False, "error": "checks list cannot be empty"}
        
        return {"valid": True}
    
    def _check_for_secrets(self, files: List[str]) -> Dict[str, Any]:
        """Check for potential secrets in file paths/names"""
        secret_patterns = [
            "password", "secret", "key", "token", "api_key",
            "private", "credential", "auth", "oauth"
        ]
        
        found_secrets = []
        for file_path in files:
            file_name = file_path.lower()
            for pattern in secret_patterns:
                if pattern in file_name:
                    found_secrets.append(f"{file_path} (contains '{pattern}')")
        
        return {
            "found_secrets": len(found_secrets) > 0,
            "locations": found_secrets
        }

# Example Usage and Test Cases
def example_gate_validations():
    """Example gate validation scenarios"""
    validator = GateValidator()
    
    # Valid Architect response
    architect_response = {
        "role": "Architect",
        "prompt_id": "agents/prompts/architect.md",
        "prompt_sha256": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
        "package_contract": {
            "package_id": "FEAT_001_health_endpoint",
            "summary": "Implementation of health check endpoint with database status",
            "files_layout": ["app/api/health.py", "tests/test_health.py"]
        }
    }
    
    result = validator.validate_architect_response(architect_response)
    print(f"Architect validation: {result.decision.value} (confidence: {result.confidence})")
    
    # Invalid Dev response (missing manifest)
    dev_response_invalid = {
        "role": "Dev",
        "prompt_id": "agents/prompts/dev.md",
        "prompt_sha256": "f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7"
        # Missing artifact_manifest
    }
    
    result = validator.validate_dev_response(dev_response_invalid)
    print(f"Dev validation (invalid): {result.decision.value}, {result.reject_code.value}")
    
    # Valid QA response
    qa_response = {
        "role": "QA",
        "prompt_id": "agents/prompts/qa.md", 
        "prompt_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
        "qa_report": {
            "result": "PASS",
            "checks": [
                {"name": "API endpoint test", "status": "PASS"},
                {"name": "Database connectivity", "status": "PASS"}
            ],
            "test_protocols": "/opt/feature-factory/artifacts/test_results.json"
        }
    }
    
    result = validator.validate_qa_response(qa_response)
    print(f"QA validation: {result.decision.value} (confidence: {result.confidence})")

# Confidence Calculation Examples
def calculate_confidence(checks_passed: int, total_checks: int, severity_weights: List[float]) -> float:
    """Calculate confidence score based on validation results"""
    if total_checks == 0:
        return 0.0
    
    base_score = checks_passed / total_checks
    
    # Apply severity weighting
    if severity_weights:
        weighted_score = sum(severity_weights) / len(severity_weights)
        return min(1.0, base_score * weighted_score)
    
    return base_score

# Decision Tree Examples
def gate_decision_tree(response: Dict[str, Any]) -> GateResponse:
    """Example decision tree for gate validation"""
    
    # Level 1: Role validation (critical)
    role = response.get("role")
    if not role:
        return GateResponse(GateDecision.DENY, 0.99, ["Missing role"], RejectCode.ROL_MISMATCH)
    
    # Level 2: Signature validation (high priority)  
    if not response.get("prompt_id") or not response.get("prompt_sha256"):
        return GateResponse(GateDecision.DENY, 0.95, ["Missing signature"], RejectCode.PROMPT_SIG_MISSING)
    
    # Level 3: Role-specific validation (medium priority)
    validator = GateValidator()
    
    if role == "Architect":
        return validator.validate_architect_response(response)
    elif role == "Dev":
        return validator.validate_dev_response(response)
    elif role == "QA":
        return validator.validate_qa_response(response)
    else:
        return GateResponse(GateDecision.DENY, 0.70, [f"Unknown role: {role}"], RejectCode.ROL_MISMATCH)

if __name__ == "__main__":
    example_gate_validations()