import pytest
import subprocess
import time
import os

def test_nginx_config_syntax():
    """Test nginx configuration syntax."""
    # Проверяем синтаксис конфигурационных файлов
    try:
        result = subprocess.run(['nginx', '-t'], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, f"Nginx config test failed: {result.stderr}"
    except FileNotFoundError:
        # Если nginx не установлен, пропускаем тест
        pytest.skip("Nginx not installed")

def test_domains_config_files_exist():
    """Test that domain config files exist."""
    # Проверяем, что конфигурационные файлы существуют
    test_config = "/opt/feature-factory/tmp/etl-tst.chococraft.ru"
    prod_config = "/opt/feature-factory/tmp/etl.chococraft.ru"
    
    assert os.path.exists(test_config), f"Test domain config file {test_config} does not exist"
    assert os.path.exists(prod_config), f"Prod domain config file {prod_config} does not exist"

def test_config_file_contents():
    """Test config file contents."""
    # Проверяем содержимое конфигурационных файлов
    test_config = "/opt/feature-factory/tmp/etl-tst.chococraft.ru"
    prod_config = "/opt/feature-factory/tmp/etl.chococraft.ru"
    
    with open(test_config, 'r') as f:
        test_content = f.read()
        assert "etl-tst.chococraft.ru" in test_content
        assert "proxy_pass http://127.0.0.1:8081" in test_content
        assert "listen 443 ssl" in test_content
    
    with open(prod_config, 'r') as f:
        prod_content = f.read()
        assert "etl.chococraft.ru" in prod_content
        assert "proxy_pass http://127.0.0.1:8080" in prod_content
        assert "listen 443 ssl" in prod_content

def test_default_config_file_exists():
    """Test that default config file exists."""
    default_config = "/opt/feature-factory/tmp/feature-factory-prod"
    assert os.path.exists(default_config), f"Default config file {default_config} does not exist"

def test_default_config_contents():
    """Test default config file contents."""
    default_config = "/opt/feature-factory/tmp/feature-factory-prod"
    
    with open(default_config, 'r') as f:
        content = f.read()
        assert "ENV=prod" in content
        assert "PORT=8080" in content
        assert "DRY_RUN=false" in content