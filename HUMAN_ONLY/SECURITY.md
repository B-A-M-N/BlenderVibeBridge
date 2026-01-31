# Security Policy

BlenderVibeBridge is a **Governed Geometry Kernel**. We take system isolation and command integrity extremely seriously.

## Supported Versions
Only the latest version of BlenderVibeBridge (currently v1.2.1) is supported for security updates.

## Reporting a Vulnerability
If you discover a security vulnerability (e.g., a way to bypass the AST Security Gate or an unauthorized filesystem mutation), please **do not open a public issue.**

Instead, please send a detailed report to the Author.

### What to include:
- A description of the vulnerability.
- A proof-of-concept (PoC) script if possible.
- The version of BlenderVibeBridge and Blender you are using.

## Security Mandates
The bridge enforces several hardware and software security layers:
- **AST Auditing**: Blocks `import os`, `exec`, and `eval` in AI-generated scripts.
- **Hardware Railings**: Caps subdivision levels, array counts, and light energy to prevent DoS.
- **Airlock Plane**: File-based mutation queue to isolate command interpretation from main-thread execution.
- **Activity Gating**: Prevents mutations during active user input.
