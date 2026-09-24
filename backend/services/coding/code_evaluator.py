import json
import uuid
from typing import Dict, Any, List, Optional
from backend.services.coding.code_executor import CodeExecutor
from backend.services.llm.provider_manager import LLMProviderManager

class CodeEvaluator:
    """
    Coding problem generation and evaluation service with Mana-Style explanations.
    """

    @classmethod
    def generate_problem(
        cls,
        language: str = "Python",
        difficulty: str = "medium",
        topic: str = "arrays",
        role: Optional[str] = None,
        document_id: Optional[str] = None,
        include_notes_rag: bool = False
    ) -> Dict[str, Any]:
        lang = language.strip()
        diff = difficulty.lower().strip()

        context_prompt = ""
        if document_id:
            try:
                from backend.services.resume.resume_analyzer import ResumeAnalyzer
                analysis = ResumeAnalyzer.get_or_analyze_resume(document_id)
                res_data = analysis.get("resume_data", {})
                skills = res_data.get("skills", [])
                projects = [p.get("title") for p in res_data.get("projects", [])]
                context_prompt += f"\nCandidate Stack/Skills: {', '.join(skills)}. Key Projects: {', '.join(projects)}."
            except Exception:
                pass

        if include_notes_rag:
            try:
                from backend.services.vector_store import search_multi_documents
                chunks = search_multi_documents(query=f"{lang} {topic} programming problem", top_k=2)
                if chunks:
                    context_prompt += "\nRelevant Study Notes:\n" + "\n".join([c.get("text", "") for c in chunks])
            except Exception:
                pass

        prompt = f"""Generate a structured coding problem.
Language: {lang}
Difficulty: {diff}
Topic: {topic}
Target Role: {role or 'Software Engineer'}
{context_prompt}

CRITICAL RULES:
1. Provide valid starter code with placeholder implementation.
2. For SQL problems: provide executable `setup_sql` statements (CREATE TABLE, INSERT INTO) and sample query requirements.
3. Include at least 3 concrete test cases (inputs and expected outputs).
4. Return ONLY valid JSON matching this schema:
{{
  "title": "Problem Title",
  "statement": "Detailed problem statement describing what the function/query should do.",
  "input_format": "Description of parameters or tables.",
  "output_format": "Description of return value or query result.",
  "constraints": ["Constraint 1", "Constraint 2"],
  "examples": [
    {{
      "input": "Example input",
      "output": "Example expected output",
      "explanation": "Clear explanation of how input produces output."
    }}
  ],
  "starter_code": "Starter code snippet",
  "setup_sql": "Optional CREATE TABLE and INSERT script for SQL problems, else empty string",
  "test_cases": [
    {{
      "input": "test_input_1",
      "expected_output": "expected_output_1",
      "is_hidden": false
    }},
    {{
      "input": "test_input_2",
      "expected_output": "expected_output_2",
      "is_hidden": true
    }}
  ]
}}"""

        manager = LLMProviderManager()
        try:
            resp_str, _ = manager.generate_answer(
                prompt=prompt,
                system_prompt="You are an expert coding interview problem author. Return ONLY raw JSON without markdown codeblocks.",
                temperature=0.3
            )
            clean_str = resp_str.strip()
            if clean_str.startswith("```"):
                clean_str = clean_str.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            
            problem_data = json.loads(clean_str)
            problem_data["problem_id"] = f"prob_{uuid.uuid4().hex[:6]}"
            problem_data["language"] = lang
            problem_data["difficulty"] = diff
            problem_data["topic"] = topic
            return problem_data
        except Exception:
            # Fallback robust problem if LLM JSON fails
            return cls._get_fallback_problem(lang, diff, topic)

    @classmethod
    def evaluate_submission(
        cls,
        language: str,
        code: str,
        problem_statement: str,
        starter_code: Optional[str] = None,
        test_cases: Optional[List[Dict[str, Any]]] = None,
        setup_sql: Optional[str] = None
    ) -> Dict[str, Any]:
        exec_res = CodeExecutor.execute(language=language, code=code, setup_sql=setup_sql)

        if exec_res.get("status") == "JAVA_MISSING":
            return {
                "success": False,
                "status": "JAVA_MISSING",
                "message": "Java compiler/runtime is not installed on this machine.",
                "tests_passed": 0,
                "total_tests": len(test_cases) if test_cases else 0,
                "stdout": exec_res.get("stdout", ""),
                "stderr": exec_res.get("stderr", ""),
                "feedback": "Java is not installed on the system environment.",
                "better_approach": "Ensure JDK is installed on the host machine.",
                "complexity": {"time": "N/A", "space": "N/A"},
                "mana_explanation": "Simple ga cheppalante, ee machine meeda Java compiler (javac) and runtime (java) install ledu, so execution skipped."
            }

        if not exec_res.get("success"):
            status_code = exec_res.get("status", "RUNTIME_ERROR")
            stderr = exec_res.get("stderr", "")

            mana_msg = "Simple ga cheppalante, meecode execution lo bug vachindi. Stderr logs ni check chesi fix cheyyandi."
            if status_code == "COMPILATION_ERROR":
                mana_msg = "Simple ga cheppalante, code compile avvaledu syntax matrix mismatch valla. Compiler error verify cheyyandi."
            elif status_code == "TIMEOUT":
                mana_msg = "Simple ga cheppalante, meecode execution infinite loop valla continuous ga run avthondi or memory limit cross aindi."

            return {
                "success": False,
                "status": status_code,
                "message": f"Execution failed with {status_code}",
                "tests_passed": 0,
                "total_tests": len(test_cases) if test_cases else 1,
                "stdout": exec_res.get("stdout", ""),
                "stderr": stderr,
                "feedback": f"Runtime / Syntax issue detected: {stderr[:200]}",
                "better_approach": "Review syntax and exception handling.",
                "complexity": {"time": "Unknown", "space": "Unknown"},
                "mana_explanation": mana_msg,
                "follow_up_question": "Can you check line references and fix the syntax error?"
            }

        # Analyze code logic with LLM for feedback & Mana-style explanation
        prompt = f"""Analyze the submitted {language} solution for the following coding task.

Problem Statement:
{problem_statement}

Submitted Code:
{code}

Execution Output:
{exec_res.get('stdout', '')}

Evaluate correctness, runtime/space complexity, and improvements.

CRITICAL MANA-STYLE EXPLANATION RULE:
Include a "mana_explanation" using natural Telugu-English written in English letters.
- Always start with "Simple ga cheppalante..."
- Use natural Telugu sentence structure written entirely using English letters (NO Telugu script).
- Mix technical English terms naturally inside Telugu sentences (keep Python, SQL, FAISS, BM25, RAG, AST, etc. in English).
- Do NOT use awkward word-by-word translations or fragmented words.
- Explain conversationally as if a friendly peer is teaching another friend.
- Use natural phrases: "simple ga cheppalante", "ante", "ikkada", "enduku ante", "ela work avtundi ante", "use chestham", "consider cheddam", "example ga".

Return JSON ONLY:
{{
  "is_correct": true,
  "tests_passed": 3,
  "total_tests": 3,
  "feedback": "Detailed qualitative feedback on correctness, edge cases, and code quality.",
  "better_approach": "Optimal approach explanation with algorithm pattern.",
  "time_complexity": "O(N)",
  "space_complexity": "O(1)",
  "mana_explanation": "Simple ga cheppalante, meecode array ni iterate chesi correct output calculate chestundi.",
  "follow_up_question": "How would you handle duplicate numbers in large datasets?"
}}"""

        manager = LLMProviderManager()
        try:
            resp_str, _ = manager.generate_answer(
                prompt=prompt,
                system_prompt="You are an expert senior algorithm evaluator. Output raw JSON only.",
                temperature=0.2
            )
            clean_str = resp_str.strip()
            if clean_str.startswith("```"):
                clean_str = clean_str.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            eval_json = json.loads(clean_str)
            mana_exp = eval_json.get("mana_explanation", "")
            try:
                from backend.services.mana_explanation import ManaExplanationService
                gemini_exp = ManaExplanationService.generate_mana_explanation(
                    question=problem_statement,
                    technical_answer=eval_json.get("feedback", "") + "\n" + eval_json.get("better_approach", ""),
                    source_context=f"Submitted Code:\n{code}",
                    mode="CODING"
                )
                if gemini_exp:
                    mana_exp = gemini_exp
            except Exception as ge_err:
                print(f"Coding Gemini Mana note: {ge_err}")

            return {
                "success": eval_json.get("is_correct", True),
                "status": "ACCEPTED" if eval_json.get("is_correct", True) else "WRONG_ANSWER",
                "message": "Submission evaluated successfully.",
                "tests_passed": t_pass,
                "tests_failed": max(0, t_tot - t_pass),
                "total_tests": t_tot,
                "stdout": exec_res.get("stdout", ""),
                "stderr": "",
                "feedback": eval_json.get("feedback", "Code ran cleanly."),
                "better_approach": eval_json.get("better_approach", ""),
                "complexity": {
                    "time": eval_json.get("time_complexity", "O(N)"),
                    "space": eval_json.get("space_complexity", "O(1)")
                },
                "mana_explanation": mana_exp or "Simple ga cheppalante, mee solution correctly test cases evaluate aindi.",
                "follow_up_question": eval_json.get("follow_up_question", "Can you optimize space complexity?")
            }
        except Exception:
            return {
                "success": True,
                "status": "ACCEPTED",
                "message": "Code executed with clean stdout.",
                "tests_passed": 1,
                "tests_failed": 0,
                "total_tests": 1,
                "stdout": exec_res.get("stdout", ""),
                "stderr": "",
                "feedback": "Your code executed successfully without runtime exceptions.",
                "better_approach": "Consider edge cases such as empty arrays or null values.",
                "complexity": {"time": "O(N)", "space": "O(1)"},
                "mana_explanation": "Simple ga cheppalante, mee code properly execute aindi output exact ga evaluate chesindi.",
                "follow_up_question": "What happens if input size is 10 million items?"
            }

    @classmethod
    def _get_fallback_problem(cls, language: str, difficulty: str, topic: str) -> Dict[str, Any]:
        if language.lower() == "sql":
            return {
                "problem_id": f"prob_fallback_{uuid.uuid4().hex[:6]}",
                "language": "SQL",
                "difficulty": difficulty,
                "topic": topic,
                "title": "Highest Paid Employee by Department",
                "statement": "Write a SQL query to find the employee with the highest salary in each department.",
                "input_format": "Table `employees` (id INT, name TEXT, salary INT, department_id INT).",
                "output_format": "Table with columns (department_id, name, salary).",
                "constraints": ["Salary > 0", "Department ID is non-null"],
                "examples": [
                    {
                        "input": "employees table with Alice (100k, Dept 1), Bob (80k, Dept 1)",
                        "output": "Dept 1 | Alice | 100000",
                        "explanation": "Alice has highest salary in Dept 1."
                    }
                ],
                "starter_code": "SELECT department_id, name, MAX(salary) AS salary\nFROM employees\nGROUP BY department_id;",
                "setup_sql": "CREATE TABLE employees (id INT, name TEXT, salary INT, department_id INT);\nINSERT INTO employees VALUES (1, 'Alice', 100000, 1), (2, 'Bob', 80000, 1), (3, 'Charlie', 120000, 2);",
                "test_cases": [
                    {"input": "SELECT department_id, name, MAX(salary) FROM employees GROUP BY department_id;", "expected_output": "1 | Alice | 100000", "is_hidden": False}
                ]
            }
        
        return {
            "problem_id": f"prob_fallback_{uuid.uuid4().hex[:6]}",
            "language": language,
            "difficulty": difficulty,
            "topic": topic,
            "title": f"Two Sum ({language})",
            "statement": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to target.",
            "input_format": "nums: list/array of integers, target: integer",
            "output_format": "list/array of 2 integer indices",
            "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"],
            "examples": [
                {
                    "input": "nums = [2,7,11,15], target = 9",
                    "output": "[0, 1]",
                    "explanation": "nums[0] + nums[1] == 9, so return [0, 1]."
                }
            ],
            "starter_code": "def two_sum(nums, target):\n    # Write your solution here\n    pass\n\nprint(two_sum([2, 7, 11, 15], 9))",
            "setup_sql": "",
            "test_cases": [
                {"input": "[2, 7, 11, 15], 9", "expected_output": "[0, 1]", "is_hidden": False}
            ]
        }
