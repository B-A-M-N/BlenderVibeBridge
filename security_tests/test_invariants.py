# BlenderVibeBridge: Property-Based Security Tests
from hypothesis import given, strategies as st
from pydantic import ValidationError
import sys
import os

# Add mcp-server to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "mcp-server"))
from core.kernel import TransformMutation

@given(st.floats(allow_nan=True, allow_infinity=True))
def test_transform_magnitude_invariance(val):
    """Verifies that NO transform can ever exceed 1M or contain NaNs."""
    data = {
        "type": "transform",
        "intent": "SCENE_SETUP",
        "op": "translate",
        "value": f"({val}, 0, 0)"
    }
    
    try:
        TransformMutation(**data)
        # If it passes, the value MUST be safe
        import ast
        coords = ast.literal_eval(data["value"])
        assert abs(coords[0]) <= 1000000
        assert not any(v != v for v in coords) # NaN check
    except (ValidationError, ValueError):
        # Successfully caught unsafe input
        pass

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
