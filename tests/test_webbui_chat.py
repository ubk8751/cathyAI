"""Test suite for cathyAI Chainlit application.

Tests chat UI, character loading, and API integration.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
import sys
import os

REPO_ROOT = Path(__file__).parent.parent


class TestWebbuiChat:
    """Test suite for Chainlit chat application."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, monkeypatch):
        """Setup and teardown for each test to ensure clean imports."""
        # Setup
        original_path = sys.path.copy()
        original_modules = set(sys.modules.keys())
        
        os.chdir(REPO_ROOT)
        sys.path.insert(0, str(REPO_ROOT))
        sys.modules['chainlit'] = Mock()
        
        import app
        self.app = app
        
        yield
        
        # Teardown
        sys.path = original_path
        new_modules = set(sys.modules.keys()) - original_modules
        for mod in new_modules:
            if mod.startswith('app') or mod == 'chainlit':
                sys.modules.pop(mod, None)

    def test_app_imports(self):
        """Test that app.py can be imported without errors."""
        assert hasattr(self.app, 'start'), "app.py missing start function"
        assert hasattr(self.app, 'main'), "app.py missing main function"
        assert hasattr(self.app, 'update_settings'), "app.py missing update_settings function"
        assert hasattr(self.app, 'auth_callback'), "app.py missing auth_callback function"
        assert hasattr(self.app, 'CHAR_LIST'), "app.py missing CHAR_LIST"
        assert hasattr(self.app, 'CHAR_INDEX'), "app.py missing CHAR_INDEX"
        assert hasattr(self.app, 'CHAR_PRIVATE_ETAGS'), "app.py missing CHAR_PRIVATE_ETAGS"
        assert hasattr(self.app, 'character_display_name'), "app.py missing character_display_name function"
        assert hasattr(self.app, 'send_character_message'), "app.py missing send_character_message function"
        assert hasattr(self.app, 'chat_profiles'), "app.py missing chat_profiles function"
        assert hasattr(self.app, 'fetch_models'), "app.py missing fetch_models function"
        assert hasattr(self.app, 'stream_chat'), "app.py missing stream_chat function"
        assert hasattr(self.app, 'detect_emotion'), "app.py missing detect_emotion function"
        assert hasattr(self.app, 'fetch_characters_list'), "app.py missing fetch_characters_list function"
        assert hasattr(self.app, 'fetch_character_private'), "app.py missing fetch_character_private function"
        assert hasattr(self.app, 'load_cached_etag'), "app.py missing load_cached_etag function"
        assert hasattr(self.app, 'save_cached_etag'), "app.py missing save_cached_etag function"

    def test_character_loading_logic(self):
        """Test character API integration functions exist."""
        import inspect
        
        assert callable(self.app.fetch_characters_list), "fetch_characters_list should be callable"
        assert callable(self.app.fetch_character_private), "fetch_character_private should be callable"
        assert callable(self.app.load_cached_characters), "load_cached_characters should be callable"
        
        assert inspect.iscoroutinefunction(self.app.fetch_characters_list), "fetch_characters_list should be async"
        assert inspect.iscoroutinefunction(self.app.fetch_character_private), "fetch_character_private should be async"

    def test_logging_configured(self):
        """Test that app has logging configured."""
        assert hasattr(self.app, 'logger'), "app.py missing logger"
        assert self.app.logger is not None, "Logger not initialized"

    def test_cache_path_configured(self):
        """Test that cache paths are configured."""
        assert hasattr(self.app, 'CHAR_CACHE_PATH'), "app.py missing CHAR_CACHE_PATH"
        assert hasattr(self.app, 'CHAR_CACHE_ETAG_PATH'), "app.py missing CHAR_CACHE_ETAG_PATH"
        assert self.app.CHAR_CACHE_PATH is not None, "CHAR_CACHE_PATH not initialized"
        assert self.app.CHAR_CACHE_ETAG_PATH is not None, "CHAR_CACHE_ETAG_PATH not initialized"

    def test_api_functions_exist(self):
        """Test that API integration functions exist."""
        import inspect
        
        assert callable(self.app.fetch_models), "fetch_models should be callable"
        assert callable(self.app.stream_chat), "stream_chat should be callable"
        assert callable(self.app.detect_emotion), "detect_emotion should be callable"
        
        assert inspect.iscoroutinefunction(self.app.fetch_models), "fetch_models should be async"
        assert inspect.isasyncgenfunction(self.app.stream_chat), "stream_chat should be async generator"
        assert inspect.iscoroutinefunction(self.app.detect_emotion), "detect_emotion should be async"

    def test_etag_caching_functions(self):
        """Test that ETag caching functions exist."""
        assert callable(self.app.load_cached_etag), "load_cached_etag should be callable"
        assert callable(self.app.save_cached_etag), "save_cached_etag should be callable"
        assert callable(self.app.load_cached_characters), "load_cached_characters should be callable"

    def test_authentication_callback(self):
        """Test that authentication callback exists."""
        assert callable(self.app.auth_callback), "auth_callback should be callable"
