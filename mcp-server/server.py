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

# BlenderVibeBridge: Modular Kernel Entry Point (v1.5.0)
from mcp.server.fastmcp import FastMCP
from vibe_logging.vibe_logger import setup_vibe_logging
from tools.management import register_management_tools
from tools.telemetry import register_telemetry_tools
from tools.operations import register_operation_tools
from tools.infrastructure import register_infrastructure_tools

# Initialize Logger
logger = setup_vibe_logging()

# Create FastMCP Server
mcp = FastMCP("BlenderVibeBridge")

# Register Modular Tools
register_management_tools(mcp)
register_telemetry_tools(mcp)
register_operation_tools(mcp)
register_infrastructure_tools(mcp)

if __name__ == "__main__":
    logger.info("BlenderVibeBridge Modular Kernel Starting...")
    mcp.run()