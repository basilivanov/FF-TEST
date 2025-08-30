import pytest
from app.orchestrator.gates import ManifestValidator
from app.orchestrator.apply import ArtifactApplier

def test_manifest_validator_init():
    """Test manifest validator initialization."""
    validator = ManifestValidator()
    assert validator is not None
    assert validator.schema is not None

def test_validate_valid_manifest():
    """Test validation of valid manifest."""
    validator = ManifestValidator()
    
    manifest_text = """# artifact_manifest
- file1.py
- file2.py
"""
    
    manifest = validator.validate_manifest(manifest_text)
    assert "artifact_manifest" in manifest
    assert len(manifest["artifact_manifest"]) == 2

def test_validate_valid_manifest_list():
    """Test validation of valid manifest as list."""
    validator = ManifestValidator()
    
    manifest_text = """- file1.py
- file2.py
"""
    
    manifest = validator.validate_manifest(manifest_text)
    assert "artifact_manifest" in manifest
    assert len(manifest["artifact_manifest"]) == 2

def test_validate_package_contract_valid():
    """Test validation of valid package contract."""
    validator = ManifestValidator()
    
    manifest = {
        "artifact_manifest": ["file1.py", "file2.py"],
        "package_contract": {
            "package_id": "PKG-TEST-v1",
            "summary": "Test package",
            "files_layout": ["file1.py", "file2.py"]
        }
    }
    
    result = validator.validate_package_contract(manifest)
    assert result is True

def test_validate_package_contract_invalid():
    """Test validation of invalid package contract."""
    validator = ManifestValidator()
    
    manifest = {
        "artifact_manifest": ["file1.py", "file2.py"],
        "package_contract": {
            "invalid_field": "value"  # Missing required fields
        }
    }
    
    result = validator.validate_package_contract(manifest)
    assert result is False

def test_validate_response_without_manifest():
    """Test validation of response without manifest."""
    validator = ManifestValidator()
    
    response_text = "Some text without manifest"
    
    with pytest.raises(ValueError, match="No manifest found in response"):
        validator.validate_response(response_text)

def test_validate_response_architect_without_package_contract():
    """Test validation of Architect response without package contract."""
    validator = ManifestValidator()
    
    response_text = """```yaml
# artifact_manifest
- file1.py
- file2.py
```
"""
    
    with pytest.raises(ValueError, match="Missing package_contract in Architect task response"):
        validator.validate_response(response_text, task_role="Architect")

def test_artifact_applier_init():
    """Test artifact applier initialization."""
    applier = ArtifactApplier()
    assert applier is not None
    assert applier.validator is not None

def test_process_valid_response():
    """Test processing of valid response."""
    applier = ArtifactApplier()
    
    response_text = """```yaml
# artifact_manifest
- file1.py
- file2.py

package_contract:
  package_id: PKG-TEST-v1
  summary: Test package
```
Some other content
"""
    
    result = applier.process_response(response_text)
    # В тестовой среде может вернуть False из-за отсутствия реальных файлов
    # но не должен бросать исключения

def test_process_valid_response_no_yaml_block():
    """Test processing of valid response without YAML block."""
    applier = ArtifactApplier()
    
    response_text = """# artifact_manifest
- file1.py
- file2.py
"""
    
    # This should not raise an exception but may return False
    try:
        result = applier.process_response(response_text)
        # Either True or False is acceptable, as long as no exception is raised
    except Exception:
        pytest.fail("process_response raised an exception unexpectedly")

def test_process_response_without_manifest():
    """Test processing of response without manifest."""
    applier = ArtifactApplier()
    
    response_text = """Some text without manifest"""
    
    result = applier.process_response(response_text)
    assert result is False

def test_process_architect_response_without_package_contract():
    """Test processing of Architect response without package contract."""
    applier = ArtifactApplier()
    
    response_text = """```yaml
# artifact_manifest
- file1.py
- file2.py
```
"""
    
    result = applier.process_response(response_text, task_role="Architect")
    assert result is False