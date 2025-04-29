import pytest
from main import XKCDPasswordGenerator

def test_password_generation():
    generator = XKCDPasswordGenerator()
    
    weak = generator.generate("weak")
    assert len(weak) >= 6 
    
    normal = generator.generate("normal")
    assert any(char.isdigit() for char in normal)
    
    strong = generator.generate("strong")
    assert any(not (char.isalpha() or char.isdigit()) for char in strong)
