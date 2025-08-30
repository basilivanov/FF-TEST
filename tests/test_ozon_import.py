import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
import os

from app.jobs.import_ozon_range import import_ozon_range, save_postings_batch, update_watermark

@pytest.fixture
def sample_postings():
    """Sample postings data."""
    return [
        {
            "source": "ozon",
            "posting_id": "12345",
            "payload_json": '{"posting_number": "12345", "status": "awaiting_deliver"}',
            "fetched_at": "2023-01-01T00:00:00Z",
            "period_from": "2023-01-01",
            "period_to": "2023-01-02"
        },
        {
            "source": "ozon",
            "posting_id": "67890",
            "payload_json": '{"posting_number": "67890", "status": "awaiting_deliver"}',
            "fetched_at": "2023-01-01T00:00:00Z",
            "period_from": "2023-01-01",
            "period_to": "2023-01-02"
        }
    ]

@pytest.mark.asyncio
async def test_save_postings_batch_success(sample_postings):
    """Test successful saving of postings batch."""
    # Мокируем engine и connection
    mock_engine = Mock()
    mock_conn = Mock()
    mock_transaction = Mock()
    
    mock_conn.begin.return_value = mock_transaction
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_engine.connect.return_value.__exit__.return_value = None
    
    with patch('app.jobs.import_ozon_range.create_engine', return_value=mock_engine):
        await save_postings_batch(sample_postings)
        
        # Проверяем, что транзакция была начата
        mock_conn.begin.assert_called_once()
        
        # Проверяем, что были выполнены вставки
        assert mock_conn.execute.call_count == len(sample_postings)
        
        # Проверяем, что транзакция была закоммичена
        mock_transaction.commit.assert_called_once()

@pytest.mark.asyncio
async def test_save_postings_batch_db_error(sample_postings):
    """Test database error handling."""
    # Мокируем engine и connection
    mock_engine = Mock()
    mock_conn = Mock()
    mock_transaction = Mock()
    
    mock_conn.begin.return_value = mock_transaction
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_engine.connect.return_value.__exit__.return_value = None
    
    # Мокируем execute для возврата ошибки
    mock_conn.execute.side_effect = Exception("Database error")
    
    with patch('app.jobs.import_ozon_range.create_engine', return_value=mock_engine):
        with pytest.raises(Exception, match="Database error"):
            await save_postings_batch(sample_postings)
        
        # Проверяем, что транзакция была откачена
        mock_transaction.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_update_watermark_success():
    """Test successful watermark update."""
    # Мокируем engine и connection
    mock_engine = Mock()
    mock_conn = Mock()
    
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_engine.connect.return_value.__exit__.return_value = None
    
    with patch('app.jobs.import_ozon_range.create_engine', return_value=mock_engine):
        watermark = datetime(2023, 1, 1)
        await update_watermark("ozon", watermark)
        
        # Проверяем, что был выполнен upsert
        mock_conn.execute.assert_called_once()

@pytest.mark.asyncio
async def test_import_ozon_range_success():
    """Test successful import of Ozon range."""
    # Мокируем OzonClient
    mock_client = AsyncMock()
    
    # Мокируем постинги
    postings = [
        {
            "source": "ozon",
            "posting_id": "12345",
            "payload_json": '{"posting_number": "12345", "status": "awaiting_deliver"}',
            "fetched_at": "2023-01-01T00:00:00Z",
            "period_from": "2023-01-01",
            "period_to": "2023-01-02"
        }
    ]
    
    # Мокируем асинхронный генератор
    async def mock_import_postings(date_from, date_to):
        for posting in postings:
            yield posting
    
    mock_client.import_postings = mock_import_postings
    
    with patch('app.jobs.import_ozon_range.create_ozon_client', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client))):
        with patch('app.jobs.import_ozon_range.save_postings_batch') as mock_save_batch:
            with patch('app.jobs.import_ozon_range.update_watermark') as mock_update_watermark:
                result = await import_ozon_range(
                    "2023-01-01",
                    "2023-01-02",
                    "test_key",
                    "test_secret"
                )
                
                # Проверяем результат
                assert result["status"] == "success"
                assert result["imported_count"] == 1
                assert result["date_from"] == "2023-01-01"
                assert result["date_to"] == "2023-01-02"
                
                # Проверяем, что была вызвана функция сохранения
                mock_save_batch.assert_called_once()
                
                # Проверяем, что был обновлен watermark
                mock_update_watermark.assert_called_once()

@pytest.mark.asyncio
async def test_import_ozon_range_error():
    """Test error handling during import."""
    # Мокируем OzonClient для возврата ошибки
    mock_client = AsyncMock()
    mock_client.import_postings.side_effect = Exception("Import error")
    
    with patch('app.jobs.import_ozon_range.create_ozon_client', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client))):
        with pytest.raises(Exception, match="Import error"):
            await import_ozon_range(
                "2023-01-01",
                "2023-01-02",
                "test_key",
                "test_secret"
            )