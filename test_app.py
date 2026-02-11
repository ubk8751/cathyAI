import pytest

def test_emotion():
    """Basic test placeholder - expand as needed"""
    assert True

def test_character_loading():
    """Test that character JSON can be loaded"""
    import json
    from pathlib import Path
    
    char_files = list(Path("characters").glob("*.json"))
    assert len(char_files) > 0, "No character files found"
    
    for f in char_files:
        data = json.load(open(f))
        assert "name" in data
        assert "model" in data
        assert "system_prompt" in data
