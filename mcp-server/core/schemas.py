# BlenderVibeBridge: Dual-License & Maintenance Agreement (v1.2)
# Copyright (C) 2026 B-A-M-N (The "Author")
#
# This software is distributed under a Dual-Licensing Model:
# 1. THE OPEN-SOURCE PATH: GNU AGPLv3 (see LICENSE for details)
# 2. THE COMMERCIAL PATH: "WORK-OR-PAY" MODEL
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.

# BlenderVibeBridge: ISA Schema Registry (v1.5.0)
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any, Dict, Union

class VibeCommand(BaseModel):
    """Base contract for all Bridge operations."""
    id: str = Field(..., description="Unique UUID for this command.")
    type: str = Field(..., description="Opcode type (e.g., transform, modifier_op).")
    intent: str = Field(..., description="The declared artistic intent.")
    vibe_session_id: Optional[str] = None

    @validator('intent')
    def validate_intent(cls, v):
        allowed = {"OPTIMIZE", "RIG", "LIGHT", "ANIMATE", "SCENE_SETUP", "GENERAL", "AUDIT"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid intent: {v}")
        return v.upper()

class TransformData(VibeCommand):
    """Schema for Opcode 0x03 (Transform)."""
    name: str = Field(..., description="Target object name.")
    uuid: str = Field(..., description="Target object vibe_uuid.")
    op: str = Field(..., description="Operation: translate, rotate, scale.")
    value: str = Field(..., description="The (x,y,z) coordinate string.")

    @validator('value')
    def validate_magnitude(cls, v):
        import ast
        try:
            coords = ast.literal_eval(v)
            if any(abs(c) > 1000000 for c in coords):
                raise ValueError("Geometric magnitude exceeds 1M safety limit.")
        except:
            raise ValueError("Invalid coordinate format. Use '(x, y, z)'.")
        return v

class ModifierData(VibeCommand):
    """Schema for Opcode 0x04 (Modifier)."""
    name: str
    uuid: Optional[str] = None
    action: str # add, remove, set
    mod_name: str
    mod_type: Optional[str] = None
    props: Optional[Dict[str, Any]] = None

class MaterialData(VibeCommand):
    """Schema for Opcode 0x09 (Material)."""
    name: str
    obj_name: Optional[str] = None

class IOData(VibeCommand):
    """Schema for Opcode 0x0B (IO)."""
    action: str # import_fbx, export_fbx
    filepath: str
