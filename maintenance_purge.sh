#!/bin/bash
# BlenderVibeBridge: Dual-License & Maintenance Agreement (v1.2)
# Copyright (C) 2026 B-A-M-N (The "Author")

# Helper script to clean up the airlock and logs
echo "[*] Purging stuck airlock commands and rotating logs..."

# 1. Clean Airlock
rm -f vibe_queue/inbox/*.json
rm -f vibe_queue/outbox/*.json
rm -f vibe_queue/outbox/*.tmp

# 2. Clean temporary diagnostic files
rm -f avatar_scripts/*.tmp

# 3. Rotate logs (Clear but keep file)
cat /dev/null > bridge.log
cat /dev/null > server.log

echo "✅ Maintenance complete."
