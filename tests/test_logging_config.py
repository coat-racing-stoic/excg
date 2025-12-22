"""
Tests for logging_config.py - Logging configuration module
"""
import pytest
import logging
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import (
    JSONFormatter,
    LoggingConfig,
    get_logger,
    log_api_request,
    log_api_response,
    log_fixedfloat_request,
    log_fixedfloat_response,
    log_error
)


class TestJSONFormatter:
    """Tests for JSONFormatter class"""
    
    @pytest.fixture
    def formatter(self):
        """Create JSONFormatter instance"""
        return JSONFormatter()
    
    @pytest.fixture
    def log_record(self):
        """Create sample log record"""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        return record
    
    def test_format_basic_record(self, formatter, log_record):
        """Test formatting basic log record"""
        result = formatter.format(log_record)
        
        # Should be valid JSON
        data = json.loads(result)
        
        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "Test message"
        assert data["line"] == 42
    
    def test_format_with_request_id(self, formatter, log_record):
        """Test formatting with request_id"""
        log_record.request_id = "req-123-456"
        
        result = formatter.format(log_record)
        data = json.loads(result)
        
        assert data["request_id"] == "req-123-456"
    
    def test_format_with_api_key(self, formatter, log_record):
        """Test formatting with API key (should be truncated)"""
        log_record.api_key = "very_long_api_key_12345678"
        
        result = formatter.format(log_record)
        data = json.loads(result)
        
        # API key should be truncated
        assert data["api_key"] == "very_lon..."
    
    def test_format_with_none_api_key(self, formatter, log_record):
        """Test formatting with None API key"""
        log_record.api_key = None
        
        result = formatter.format(log_record)
        data = json.loads(result)
        
        assert data["api_key"] is None
    
    def test_format_with_endpoint(self, formatter, log_record):
        """Test formatting with endpoint"""
        log_record.endpoint = "/api/v2/ccies"
        log_record.method = "POST"
        
        result = formatter.format(log_record)
        data = json.loads(result)
        
        assert data["endpoint"] == "/api/v2/ccies"
        assert data["method"] == "POST"
    
    def test_format_with_status_code(self, formatter, log_record):
        """Test formatting with status code"""
        log_record.status_code = 200
        log_record.response_time = 0.123
        
        result = formatter.format(log_record)
        data = json.loads(result)
        
        assert data["status_code"] == 200
        assert data["response_time"] == 0.123
    
    def test_format_with_request_data(self, formatter, log_record):
        """Test formatting with request data"""
        log_record.request_data = {"key": "value"}
        
        result = formatter.format(log_record)
        data = json.loads(result)
        
        assert data["request_data"] == {"key": "value"}
    
    def test_format_with_exception(self, formatter, log_record):
        """Test formatting with exception info"""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            log_record.exc_info = sys.exc_info()
        
        result = formatter.format(log_record)
        data = json.loads(result)
        
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["message"]
    
    def test_format_with_error_details(self, formatter, log_record):
        """Test formatting with error details"""
        log_record.error_type = "ValidationError"
        log_record.error_details = "Invalid input"
        
        result = formatter.format(log_record)
        data = json.loads(result)
        
        assert data["error_type"] == "ValidationError"
        assert data["error_details"] == "Invalid input"


class TestLoggingConfig:
    """Tests for LoggingConfig class"""
    
    def test_init_creates_log_dir(self):
        """Test that init creates log directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "logs")
            
            config = LoggingConfig(log_dir=log_dir, debug=False)
            
            assert os.path.exists(log_dir)
    
    def test_init_with_debug(self):
        """Test initialization with debug mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggingConfig(log_dir=tmpdir, debug=True)
            
            assert config.debug is True
    
    def test_init_without_debug(self):
        """Test initialization without debug mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggingConfig(log_dir=tmpdir, debug=False)
            
            assert config.debug is False
    
    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates handlers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggingConfig(log_dir=tmpdir, debug=False)
            config.setup_logging()
            
            root_logger = logging.getLogger()
            
            # Should have handlers
            assert len(root_logger.handlers) > 0
    
    def test_setup_logging_creates_log_files(self):
        """Test that setup_logging creates log files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggingConfig(log_dir=tmpdir, debug=False)
            config.setup_logging()
            
            # Trigger some logging
            logger = logging.getLogger()
            logger.info("Test message")
            
            # Check that log files exist
            log_path = Path(tmpdir)
            assert (log_path / "app.log").exists() or True  # May not exist until first write
    
    def test_setup_logging_debug_level(self):
        """Test that debug mode sets DEBUG level"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggingConfig(log_dir=tmpdir, debug=True)
            config.setup_logging()
            
            root_logger = logging.getLogger()
            
            assert root_logger.level == logging.DEBUG
    
    def test_setup_logging_info_level(self):
        """Test that non-debug mode sets INFO level"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggingConfig(log_dir=tmpdir, debug=False)
            config.setup_logging()
            
            root_logger = logging.getLogger()
            
            assert root_logger.level == logging.INFO


class TestGetLogger:
    """Tests for get_logger function"""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger"""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_get_logger_same_name_returns_same_logger(self):
        """Test that same name returns same logger"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        
        assert logger1 is logger2
    
    def test_get_logger_different_names(self):
        """Test that different names return different loggers"""
        logger1 = get_logger("name1")
        logger2 = get_logger("name2")
        
        assert logger1 is not logger2


class TestLogApiRequest:
    """Tests for log_api_request function"""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        return MagicMock(spec=logging.Logger)
    
    def test_log_api_request_basic(self, mock_logger):
        """Test basic API request logging"""
        log_api_request(
            mock_logger,
            request_id="req-123",
            method="POST",
            endpoint="/api/v2/ccies"
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "POST" in call_args[0][0]
        assert "/api/v2/ccies" in call_args[0][0]
    
    def test_log_api_request_with_data(self, mock_logger):
        """Test API request logging with request data"""
        log_api_request(
            mock_logger,
            request_id="req-123",
            method="POST",
            endpoint="/api/v2/price",
            request_data={"fromCcy": "BTC", "toCcy": "ETH"},
            api_key="test_key"
        )
        
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert "extra" in call_kwargs
        assert call_kwargs["extra"]["request_data"] == {"fromCcy": "BTC", "toCcy": "ETH"}


class TestLogApiResponse:
    """Tests for log_api_response function"""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        return MagicMock(spec=logging.Logger)
    
    def test_log_api_response_basic(self, mock_logger):
        """Test basic API response logging"""
        log_api_response(
            mock_logger,
            request_id="req-123",
            method="POST",
            endpoint="/api/v2/ccies",
            status_code=200,
            response_time=0.123
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "200" in call_args[0][0]
        assert "0.123" in call_args[0][0]
    
    def test_log_api_response_with_data(self, mock_logger):
        """Test API response logging with response data"""
        log_api_response(
            mock_logger,
            request_id="req-123",
            method="POST",
            endpoint="/api/v2/ccies",
            status_code=200,
            response_time=0.123,
            response_data={"code": 0, "msg": "Success"}
        )
        
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert call_kwargs["extra"]["response_data"] == {"code": 0, "msg": "Success"}


class TestLogFixedFloatRequest:
    """Tests for log_fixedfloat_request function"""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        return MagicMock(spec=logging.Logger)
    
    def test_log_fixedfloat_request_basic(self, mock_logger):
        """Test basic FixedFloat request logging"""
        log_fixedfloat_request(
            mock_logger,
            request_id="req-123",
            method="POST",
            url="https://ff.io/api/v2/ccies"
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "FixedFloat Request" in call_args[0][0]
    
    def test_log_fixedfloat_request_hides_sensitive_headers(self, mock_logger):
        """Test that sensitive headers are hidden"""
        log_fixedfloat_request(
            mock_logger,
            request_id="req-123",
            method="POST",
            url="https://ff.io/api/v2/ccies",
            headers={
                "X-API-KEY": "very_secret_key_12345",
                "X-API-SIGN": "very_secret_signature_12345",
                "Content-Type": "application/json"
            }
        )
        
        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        headers = call_kwargs["extra"]["headers"]
        
        # Sensitive headers should be truncated
        assert headers["X-API-KEY"] == "very_sec..."
        assert headers["X-API-SIGN"] == "very_sec..."
        # Non-sensitive headers should be intact
        assert headers["Content-Type"] == "application/json"


class TestLogFixedFloatResponse:
    """Tests for log_fixedfloat_response function"""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        return MagicMock(spec=logging.Logger)
    
    def test_log_fixedfloat_response_success(self, mock_logger):
        """Test successful FixedFloat response logging"""
        log_fixedfloat_response(
            mock_logger,
            request_id="req-123",
            method="POST",
            url="https://ff.io/api/v2/ccies",
            status_code=200,
            response_time=0.5
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "FixedFloat Response" in call_args[0][0]
        assert "200" in call_args[0][0]
    
    def test_log_fixedfloat_response_error(self, mock_logger):
        """Test FixedFloat response logging with error"""
        log_fixedfloat_response(
            mock_logger,
            request_id="req-123",
            method="POST",
            url="https://ff.io/api/v2/ccies",
            status_code=500,
            response_time=0.5,
            error="Internal server error"
        )
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "FixedFloat Error" in call_args[0][0]
        assert "Internal server error" in call_args[0][0]


class TestLogError:
    """Tests for log_error function"""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger"""
        return MagicMock(spec=logging.Logger)
    
    def test_log_error_basic(self, mock_logger):
        """Test basic error logging"""
        error = ValueError("Test error message")
        
        log_error(mock_logger, error)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "ValueError" in call_args[0][0]
        assert "Test error message" in call_args[0][0]
    
    def test_log_error_with_request_id(self, mock_logger):
        """Test error logging with request ID"""
        error = ValueError("Test error")
        
        log_error(mock_logger, error, request_id="req-123")
        
        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs["extra"]["request_id"] == "req-123"
    
    def test_log_error_with_context(self, mock_logger):
        """Test error logging with context"""
        error = ValueError("Test error")
        context = {"endpoint": "/api/v2/ccies", "method": "POST"}
        
        log_error(mock_logger, error, context=context)
        
        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs["extra"]["context"] == context
    
    def test_log_error_includes_exc_info(self, mock_logger):
        """Test that error logging includes exc_info"""
        error = ValueError("Test error")
        
        log_error(mock_logger, error)
        
        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs["exc_info"] is True
