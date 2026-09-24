import os
import sys
import shutil
import tempfile
import subprocess
import sqlite3
import re
from typing import Dict, Any, List, Optional

class CodeExecutor:
    """
    Secure subprocess code execution engine.
    Executes Python, JavaScript, Java, and SQL in isolated temporary environments with timeouts.
    Never uses eval(), exec(), or shell=True.
    """

    MAX_TIMEOUT_SECONDS = 5
    MAX_OUTPUT_BYTES = 10000

    @classmethod
    def execute(cls, language: str, code: str, input_data: str = "", setup_sql: Optional[str] = None) -> Dict[str, Any]:
        lang = language.lower().strip()

        if lang in ["python", "py"]:
            return cls._execute_python(code, input_data)
        elif lang in ["javascript", "js", "node"]:
            return cls._execute_javascript(code, input_data)
        elif lang == "java":
            return cls._execute_java(code, input_data)
        elif lang == "sql":
            return cls._execute_sql(code, setup_sql=setup_sql)
        else:
            return {
                "success": False,
                "status": "UNSUPPORTED_LANGUAGE",
                "stdout": "",
                "stderr": f"Language '{language}' is not supported.",
                "execution_time_ms": 0
            }

    @classmethod
    def _execute_python(cls, code: str, input_data: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "solution.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            python_bin = sys.executable or "python"
            cmd = [python_bin, file_path]

            try:
                proc = subprocess.run(
                    cmd,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=cls.MAX_TIMEOUT_SECONDS,
                    cwd=temp_dir
                )
                stdout = proc.stdout[:cls.MAX_OUTPUT_BYTES]
                stderr = proc.stderr[:cls.MAX_OUTPUT_BYTES]
                success = (proc.returncode == 0)

                return {
                    "success": success,
                    "status": "SUCCESS" if success else "RUNTIME_ERROR",
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": proc.returncode
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "status": "TIMEOUT",
                    "stdout": "",
                    "stderr": f"Execution timed out ({cls.MAX_TIMEOUT_SECONDS}s limit exceeded).",
                    "returncode": -1
                }
            except Exception as e:
                return {
                    "success": False,
                    "status": "ERROR",
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1
                }

    @classmethod
    def _execute_javascript(cls, code: str, input_data: str) -> Dict[str, Any]:
        node_bin = shutil.which("node")
        if not node_bin:
            return {
                "success": False,
                "status": "NODE_MISSING",
                "stdout": "",
                "stderr": "Node.js execution engine is not installed on this machine.",
                "returncode": -1
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "solution.js")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            cmd = [node_bin, file_path]

            try:
                proc = subprocess.run(
                    cmd,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=cls.MAX_TIMEOUT_SECONDS,
                    cwd=temp_dir
                )
                stdout = proc.stdout[:cls.MAX_OUTPUT_BYTES]
                stderr = proc.stderr[:cls.MAX_OUTPUT_BYTES]
                success = (proc.returncode == 0)

                return {
                    "success": success,
                    "status": "SUCCESS" if success else "RUNTIME_ERROR",
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": proc.returncode
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "status": "TIMEOUT",
                    "stdout": "",
                    "stderr": f"Execution timed out ({cls.MAX_TIMEOUT_SECONDS}s limit exceeded).",
                    "returncode": -1
                }
            except Exception as e:
                return {
                    "success": False,
                    "status": "ERROR",
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1
                }

    @classmethod
    def _execute_java(cls, code: str, input_data: str) -> Dict[str, Any]:
        javac_bin = shutil.which("javac")
        java_bin = shutil.which("java")

        if not javac_bin or not java_bin:
            return {
                "success": False,
                "status": "JAVA_MISSING",
                "stdout": "",
                "stderr": "Java compiler/runtime is not installed on this machine.",
                "returncode": -1
            }

        class_match = re.search(r'public\s+class\s+([A-Za-z0-9_]+)', code)
        class_name = class_match.group(1) if class_match else "Solution"

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, f"{class_name}.java")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Compile step
            compile_cmd = [javac_bin, file_path]
            try:
                comp_proc = subprocess.run(
                    compile_cmd,
                    capture_output=True,
                    text=True,
                    timeout=cls.MAX_TIMEOUT_SECONDS,
                    cwd=temp_dir
                )
                if comp_proc.returncode != 0:
                    return {
                        "success": False,
                        "status": "COMPILATION_ERROR",
                        "stdout": "",
                        "stderr": comp_proc.stderr[:cls.MAX_OUTPUT_BYTES],
                        "returncode": comp_proc.returncode
                    }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "status": "TIMEOUT",
                    "stdout": "",
                    "stderr": "Compilation timed out.",
                    "returncode": -1
                }

            # Run step
            run_cmd = [java_bin, class_name]
            try:
                proc = subprocess.run(
                    run_cmd,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=cls.MAX_TIMEOUT_SECONDS,
                    cwd=temp_dir
                )
                stdout = proc.stdout[:cls.MAX_OUTPUT_BYTES]
                stderr = proc.stderr[:cls.MAX_OUTPUT_BYTES]
                success = (proc.returncode == 0)

                return {
                    "success": success,
                    "status": "SUCCESS" if success else "RUNTIME_ERROR",
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": proc.returncode
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "status": "TIMEOUT",
                    "stdout": "",
                    "stderr": f"Execution timed out ({cls.MAX_TIMEOUT_SECONDS}s limit exceeded).",
                    "returncode": -1
                }
            except Exception as e:
                return {
                    "success": False,
                    "status": "ERROR",
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1
                }

    @classmethod
    def _execute_sql(cls, query_code: str, setup_sql: Optional[str] = None) -> Dict[str, Any]:
        """Execute SQL query against an isolated temporary in-memory SQLite database."""
        conn = None
        try:
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()

            if setup_sql:
                cursor.executescript(setup_sql)

            output_lines = []
            try:
                cursor.execute(query_code)
                if cursor.description:
                    cols = [desc[0] for desc in cursor.description]
                    output_lines.append(" | ".join(cols))
                    output_lines.append("-" * max(20, (sum(len(c) for c in cols) + 3 * len(cols))))
                    rows = cursor.fetchall()
                    for row in rows:
                        output_lines.append(" | ".join(str(val) for val in row))
                else:
                    output_lines.append("Query executed successfully.")
            except Exception:
                cursor.executescript(query_code)
                output_lines.append("SQL script executed successfully.")

            stdout = "\n".join(output_lines) if output_lines else "Query executed successfully."
            conn.close()

            return {
                "success": True,
                "status": "SUCCESS",
                "stdout": stdout,
                "stderr": "",
                "returncode": 0
            }
        except Exception as e:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            return {
                "success": False,
                "status": "SQL_ERROR",
                "stdout": "",
                "stderr": f"SQL Execution Error: {str(e)}",
                "returncode": 1
            }
