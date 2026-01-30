#!/bin/bash
# BlenderVibeBridge: Dual-License & Maintenance Agreement (v1.2)
# Copyright (C) 2026 B-A-M-N (The "Author")

# Helper script to zip the addon for distribution
ZIP_NAME="blender_vibe_bridge_v1.2.1.zip"

echo "[*] Packaging BlenderVibeBridge..."
rm -f "$ZIP_NAME"
zip -r "$ZIP_NAME" blender_addon/vibe_bridge/ -x "*.pyc" "__pycache__/*"

echo "✅ Addon packaged as: $ZIP_NAME"
echo "Install this .zip via Blender's Add-on Preferences."
