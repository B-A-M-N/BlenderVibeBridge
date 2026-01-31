# Coordinate Translation & Unit Normalization Formulas (Vibe-Meters)

**Protocol Version:** 1.0.0  
**Reference Engine:** Blender (Right-Handed, Z-Up) → Unity (Left-Handed, Y-Up)

---

## 1. Unit Normalization (SI Meters)

To ensure cross-engine determinism, all positional and scale data MUST be normalized to SI Meters (1.0 = 1 Meter) before transmission.

### From Blender to Sync Boundary
```python
normalized_pos = blender_pos * scene.unit_settings.scale_length
normalized_scale = blender_scale * scene.unit_settings.scale_length
```

### From Sync Boundary to Blender
```python
blender_pos = incoming_pos / scene.unit_settings.scale_length
blender_scale = incoming_scale / scene.unit_settings.scale_length
```

---

## 2. Axis Basis Translation (Right to Left Handed)

### Blender (Z-Up) → Unity (Y-Up)
**The "Y-Z Swap" Rule:**
1.  **Position**: Swap Y and Z. Negate the new Z (if necessary depending on look-at).
    *   `Unity.x = Blender.x`
    *   `Unity.y = Blender.z`
    *   `Unity.z = Blender.y`
2.  **Rotation (Euler)**: 
    *   `Unity.rx = -Blender.rx`
    *   `Unity.ry = -Blender.rz`
    *   `Unity.rz = -Blender.ry`

---

## 3. The Scale-Invariant Enforcement Formula

If a datablock (Mesh) has a non-uniform scale, the AI must apply the scale to the vertex positions (Freeze Transforms) before topological analysis.

**The "Vibe Factor" Check:**
```python
is_dirty = any(abs(s - 1.0) > 0.0001 for s in object.scale)
if is_dirty:
    # Logic: apply scale to data, then reset scale to 1.0
```

---

## 4. Resource Budget Constants

| Metric | Soft Cap (Warning) | Hard Cap (Reject) |
| :--- | :--- | :--- |
| Vertex Count | 100,000 | 1,000,000 |
| Face Count | 50,000 | 500,000 |
| Texture Resolution | 2048px | 4096px |
| Modifier Iterations | 2 | 4 |

---

# ABSOLUTE META-RULE
**When in doubt, normalize to world-space SI Meters.** 
Local-space drift is the primary cause of identity collapse.
