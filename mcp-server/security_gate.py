import ast
import sys
import os
import hashlib
import json

class SecurityGate:
    """
    A robust security auditor with AST analysis and a Trusted Signature whitelist.
    """
    
    TRUSTED_FILE = "trusted_signatures.json"

    @classmethod
    def _get_content_hash(cls, content):
        """Generates a stable SHA-256 hash for code content."""
        return hashlib.sha256(content.strip().encode('utf-8')).hexdigest()

    @classmethod
    def is_trusted(cls, content):
        """Checks if this exact code block has been previously approved."""
        if not os.path.exists(cls.TRUSTED_FILE):
            return False
        
        content_hash = cls._get_content_hash(content)
        try:
            with open(cls.TRUSTED_FILE, "r") as f:
                trusted = json.load(f)
                return content_hash in trusted
        except:
            return False

    @classmethod
    def trust_content(cls, content, reason="User Approved"):
        """Adds a content hash to the persistent whitelist."""
        content_hash = cls._get_content_hash(content)
        trusted = {}
        if os.path.exists(cls.TRUSTED_FILE):
            try:
                with open(cls.TRUSTED_FILE, "r") as f:
                    trusted = json.load(f)
            except: pass
        
        trusted[content_hash] = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "reason": reason
        }
        
        with open(cls.TRUSTED_FILE, "w") as f:
            json.dump(trusted, f, indent=2)
        return True

    PYTHON_FORBIDDEN_MODULES = {
        'os', 'subprocess', 'shlex', 'shutil', 'socket', 'posix', 'pty',
        'google.auth', 'google.oauth2', 'requests.auth', 'importlib', 'builtins',
        'ctypes', 'gc', 'marshal', 'pickle', 'types', 'inspect', 'shelve',
        'http', 'urllib', 'ftplib', 'telnetlib', 'smtplib', 'sys', 'bpy'
    }
    PYTHON_FORBIDDEN_FUNCTIONS = {
        'eval', 'exec', 'getattr', 'setattr', 'globals', 'locals', 'input', '__import__', '__builtins__', 'compile',
        'gethostbyname', 'getaddrinfo', 'create_connection'
    }
    PYTHON_FORBIDDEN_ATTRIBUTES = {
        'environ', 'getenv', '__globals__', '__subclasses__', '__mro__', '__base__', '__class__', '__code__',
        '__getattribute__', '__dict__', 'modules'
    }
    ALLOWED_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0', '::1'}

    # --- Blender-Specific Dangerous Operators ---
    BLENDER_FORBIDDEN_OPERATORS = {
        'wm.execute_python', 'wm.read_homefile', 'wm.open_mainfile', 'wm.quit_blender',
        'wm.save_mainfile', 'wm.save_as_mainfile', 'wm.app_template_install',
        'wm.addon_install', 'wm.addon_disable', 'wm.addon_enable',
        'wm.path_open', 'wm.shell_open', 'wm.url_open'
    }

    # --- Blender Persistence Ban ---
    BLENDER_FORBIDDEN_ATTRIBUTES = {
        'handlers', 'timers'
    }

    @classmethod
    def check_python(cls, code):
        # 0. Check Whitelist first
        if cls.is_trusted(code):
            return []

        # Strict ASCII Check
        try:
            code.encode('ascii')
        except UnicodeEncodeError:
            return ["Security Violation: Non-ASCII characters detected."]

        if len(code) > 50000:
            return ["Security Violation: File too large to safely audit."]

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"Syntax Error: {str(e)}"]

        errors = []
        node_count = 0
        
        for node in ast.walk(tree):
            node_count += 1
            if node_count > 5000:
                return ["Security Violation: File too complex to safely audit."]

            # DoS Protection
            if isinstance(node, (ast.While, ast.For)):
                if cls._is_infinite_loop(node):
                    errors.append("Security Violation: Potential infinite loop detected.")
            
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Mult):
                    # Detect 'A' * 10**8 or 10**8 * 'A'
                    for side in [node.left, node.right]:
                        if isinstance(side, ast.Constant) and isinstance(side.value, int) and side.value > 10**6:
                            errors.append("Security Violation: Potential large memory allocation detected.")
                        # Check for Power-based allocations like 10**8
                        if isinstance(side, ast.BinOp) and isinstance(side.op, ast.Pow):
                            if isinstance(side.right, ast.Constant) and isinstance(side.right.value, int) and side.right.value > 6:
                                errors.append("Security Violation: Potential large memory allocation detected.")

            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)) and node.value > 10**12:
                    errors.append("Security Violation: Extremely large numeric constant.")
                if isinstance(node.value, (bytes, str)) and len(node.value) > 10**6:
                    errors.append("Security Violation: Extremely large data literal.")

            # Check Imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module, asname=None)]):
                    mod_base = alias.name.split('.')[0]
                    if mod_base in cls.PYTHON_FORBIDDEN_MODULES:
                        errors.append(f"Security Violation: Forbidden module import '{alias.name}'")

            # Check Function Calls
            if isinstance(node, ast.Call):
                func_name = cls._resolve_func_name(node.func)
                if func_name in cls.PYTHON_FORBIDDEN_FUNCTIONS:
                    errors.append(f"Security Violation: Use of forbidden function '{func_name}'")
                
                # Blender Operator & Persistence Check
                if isinstance(node.func, ast.Attribute):
                    path = cls._resolve_full_path(node.func)
                    if path.startswith("bpy.ops."):
                        op_full = path[8:] # remove bpy.ops.
                        if op_full in cls.BLENDER_FORBIDDEN_OPERATORS:
                            errors.append(f"Security Violation: Use of forbidden Blender operator 'bpy.ops.{op_full}'")
                    
                    if "bpy.app." in path:
                        attr = path.split('.')[-1]
                        if attr in cls.BLENDER_FORBIDDEN_ATTRIBUTES:
                            errors.append(f"Security Violation: Persistent Blender trick detected: '{path}'")

                    # Special check for ShaderNodeScript (OSL) - catch any .nodes.new()
                    if path.endswith(".nodes.new") or path.endswith(".nodes.add"):
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and arg.value == "ShaderNodeScript":
                                errors.append("Security Violation: OSL Shader Nodes are forbidden.")
                        for kw in node.keywords:
                            if kw.arg == "type" and isinstance(kw.value, ast.Constant) and kw.value.value == "ShaderNodeScript":
                                errors.append("Security Violation: OSL Shader Nodes are forbidden.")

                # Network & Bridge Check
                if func_name in ('get', 'post', 'request'):
                    url = cls._get_url_from_call(node)
                    if url:
                        if "22000" in url or "localhost" in url or "127.0.0.1" in url:
                            if not cls._has_vibe_token(node):
                                errors.append("Security Violation: Local bridge requests MUST include 'X-Vibe-Token' header.")
                        elif not any(host in url for host in cls.ALLOWED_HOSTS):
                            errors.append(f"Security Violation: External network request to '{url}' blocked.")
                
                # File System Safety Check
                if func_name in ('open', 'write', 'Path', 'mkdir', 'remove', 'rmdir'):
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            if not cls._is_path_safe(arg.value):
                                errors.append(f"Security Violation: Access to forbidden path '{arg.value}' blocked.")

            # Check for Internal Access & Persistence Ban
            if isinstance(node, ast.Attribute):
                if node.attr in cls.PYTHON_FORBIDDEN_ATTRIBUTES:
                    errors.append(f"Security Violation: Access to internal attribute '{node.attr}' forbidden.")
                
                # Persistence check for handlers/timers
                path = cls._resolve_full_path(node)
                if any(p in path for p in ["bpy.app.handlers", "bpy.app.timers"]):
                    errors.append(f"Security Violation: Persistent Blender trick detected: '{path}'")

            # Secret Detection
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.upper()
                        if any(k in var_name for k in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'AUTH', 'CREDENTIAL']):
                            if cls._is_sensitive_value(node.value):
                                errors.append(f"Security Violation: Potential hardcoded secret in variable '{target.id}'")

        return errors

    @classmethod
    def _is_sensitive_value(cls, node, in_collection=False):
        threshold = 4 if in_collection else 8
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return len(node.value) >= threshold
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return cls._is_sensitive_value(node.left, in_collection) or cls._is_sensitive_value(node.right, in_collection)
        if isinstance(node, ast.JoinedStr): return True
        if isinstance(node, ast.List):
            return any(cls._is_sensitive_value(elt, True) for elt in node.elts)
        return False

    @classmethod
    def _resolve_func_name(cls, node):
        if isinstance(node, ast.Name): return node.id
        if isinstance(node, ast.Attribute): return node.attr
        return ""

    @classmethod
    def _resolve_full_path(cls, node):
        """Recursively resolves a full attribute path like 'bpy.ops.wm.execute_python'."""
        if isinstance(node, ast.Attribute):
            return f"{cls._resolve_full_path(node.value)}.{node.attr}"
        if isinstance(node, ast.Name):
            return node.id
        return ""

    @classmethod
    def _get_url_from_call(cls, node):
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "http" in arg.value:
                return arg.value
        for kw in node.keywords:
            if kw.arg == 'url' and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value
        return None

    @staticmethod
    def _is_path_safe(path):
        forbidden = ("security_gate.py", "trusted_signatures.json", "metadata/", ".gemini_security/")
        if any(f in path for f in forbidden): return False
        if ".." in path: return False
        return True

    @classmethod
    def _is_infinite_loop(cls, node):
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                return not has_break
        return False

    @classmethod
    def _has_vibe_token(cls, node):
        for kw in node.keywords:
            if kw.arg == 'headers':
                if isinstance(kw.value, ast.Dict):
                    for k in kw.value.keys:
                        if isinstance(k, ast.Constant) and k.value == "X-Vibe-Token":
                            return True
        return False

    # --- Shell Security (Whitelist Based) ---
    SHELL_WHITELIST = {
        'git', 'python', 'python3', 'ls', 'cat', 'mkdir', 'rm', 'cp', 'mv', 
        'grep', 'find', 'pip', 'pip3', 'cargo', 'rustc', 'docker'
    }
    FORBIDDEN_SHELL_PATTERNS = {
        'curl', 'wget', 'ssh', 'nc', 'bash -i', 'sh -i', '>', '>>', '|', '&&', ';', '`', '$(',
        'API_KEY', 'TOKEN', 'gcloud', 'env', 'printenv', '.config',
        'LD_', 'PYTHONPATH', 'PERL5LIB', 'RUBYLIB', '*', '?', '[', ']', '{', '}'
    }

    @classmethod
    def check_shell(cls, cmd):
        parts = cmd.strip().split()
        if not parts: return []
        errors = []
        base_cmd = parts[0]
        
        if base_cmd not in cls.SHELL_WHITELIST:
            errors.append(f"Security Violation: Shell command '{base_cmd}' not whitelisted.")
        
        if "22000" in cmd or "localhost" in cmd:
            if "X-Vibe-Token" not in cmd:
                errors.append("Security Violation: Local bridge requests via shell MUST include token.")

        for pattern in cls.FORBIDDEN_SHELL_PATTERNS:
            if pattern in cmd:
                errors.append(f"Security Violation: Forbidden pattern '{pattern}' detected.")

        if ".." in cmd:
            errors.append("Security Violation: Path traversal detected.")
            
        return errors

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BlenderVibeBridge Security Gate")
    parser.add_argument("file", help="File to audit")
    parser.add_argument("--trust", action="store_true", help="Manually trust this file")
    args = parser.parse_args()
    
    if not os.path.exists(args.file): sys.exit(1)
    with open(args.file, 'r') as f: content = f.read()
    if args.trust:
        SecurityGate.trust_content(content)
        sys.exit(0)
        
    ext = os.path.splitext(args.file)[1]
    issues = SecurityGate.check_python(content) if ext == '.py' else []
    if issues:
        print("\n".join(issues))
        sys.exit(1)
    else:
        print("✅ Security Audit Passed.")
        sys.exit(0)