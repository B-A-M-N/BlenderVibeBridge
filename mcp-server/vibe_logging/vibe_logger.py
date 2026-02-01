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

# BlenderVibeBridge: Logger (v1.5.0)
import logging
import sys
import re

class RedactionFilter(logging.Filter):
    def filter(self, record):
        msg = str(record.msg)
        # Redact ?key=... patterns
        msg = re.sub(r'key=[a-zA-Z0-9_\-]+', 'key=[REDACTED]', msg)
        # Redact generic VIBE_... keys
        msg = re.sub(r'VIBE_[777_]*[a-zA-Z0-9]{4,}', '[KEY_REDACTED]', msg)
        record.msg = msg
        return True

def setup_vibe_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [MCP] %(message)s",
        handlers=[
            logging.FileHandler("/home/bamn/BlenderVibeBridge/server.log"),
            logging.StreamHandler(sys.stderr)
        ]
    )
    logger = logging.getLogger("MCPServer")
    logger.addFilter(RedactionFilter())
    return logger
