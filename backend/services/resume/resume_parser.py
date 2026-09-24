import os
import json
import re
import hashlib
from datetime import datetime
from backend.services.ingestion.document_indexer import DocumentMetadataStore

RESUME_DATA_DIR = os.path.join(DocumentMetadataStore.get_metadata_path("b8f2cb48").rsplit(os.sep, 2)[0], "resumes")
os.makedirs(RESUME_DATA_DIR, exist_ok=True)

PARSER_VERSION = "2.7"

HEADING_MAP = {
    "summary": [
        "PROFESSIONAL SUMMARY", "SUMMARY", "PROFILE", "PERSONAL PROFILE", "EXECUTIVE SUMMARY", "OBJECTIVE", "ABOUT ME"
    ],
    "education": [
        "EDUCATION", "ACADEMIC QUALIFICATIONS", "ACADEMIC BACKGROUND", "EDUCATION & CREDENTIALS", "QUALIFICATIONS"
    ],
    "skills": [
        "TECHNICAL SKILLS", "SKILLS", "TECHNICAL & CORE SKILLS", "CORE COMPETENCIES", "SKILLS & TOOLS", "SKILL HIGHLIGHTS"
    ],
    "experience": [
        "INTERNSHIP EXPERIENCE", "WORK EXPERIENCE", "EXPERIENCE", "PROFESSIONAL EXPERIENCE", "EMPLOYMENT HISTORY", "INTERNSHIPS"
    ],
    "projects": [
        "PROJECTS", "KEY PROJECTS", "ACADEMIC PROJECTS", "PERSONAL PROJECTS", "TECHNICAL PROJECTS"
    ],
    "certifications": [
        "CERTIFICATIONS", "CERTIFICATES", "COURSES & CERTIFICATIONS", "LICENSES & CERTIFICATIONS"
    ],
    "achievements": [
        "ACHIEVEMENTS", "AWARDS", "ACHIEVEMENTS & AWARDS", "HONORS & AWARDS", "ACCOMPLISHMENTS"
    ]
}


def calculate_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def detect_sections_from_text(full_text: str) -> dict:
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    if not lines:
        return {}

    candidate_name = lines[0]
    location = None

    for line in lines[1:5]:
        if re.search(r'(india|telangana|hyderabad|bangalore|usa|uk|singapore|delhi|mumbai|pune|chennai|ca|tx)', line, re.IGNORECASE):
            location = line
            break
        elif "," in line and "@" not in line and not re.search(r'https?://', line):
            location = line
            break

    heading_to_key = {}
    for key, aliases in HEADING_MAP.items():
        for alias in aliases:
            heading_to_key[alias] = key

    section_spans = []
    for i, line in enumerate(lines):
        clean_line = line.upper().strip(" :-—•")
        if clean_line in heading_to_key:
            section_spans.append((i, heading_to_key[clean_line], line))

    parsed_sections = {
        "candidate_name": candidate_name,
        "location": location,
        "summary": None,
        "education": [],
        "skills": {
            "programming": [],
            "ai_ml": [],
            "generative_ai": [],
            "libraries": [],
            "frontend": [],
            "backend": [],
            "tools": []
        },
        "experience": [],
        "projects": [],
        "certifications": [],
        "achievements": []
    }

    if not section_spans:
        parsed_sections["summary"] = " ".join(lines[1:6])
        return parsed_sections

    for idx, (line_idx, key, raw_heading) in enumerate(section_spans):
        start = line_idx + 1
        end = section_spans[idx + 1][0] if idx + 1 < len(section_spans) else len(lines)
        sec_lines = lines[start:end]

        if key == "summary":
            parsed_sections["summary"] = " ".join(sec_lines)

        elif key == "education":
            edu_entry = {}
            for l in sec_lines:
                if re.search(r'\b(20\d\d|19\d\d)\b', l):
                    edu_entry["year"] = l
                elif re.search(r'\b(B\.Tech|B\.E|M\.Tech|B\.S|M\.S|B\.Sc|M\.Sc|Degree|Diploma)\b', l, re.IGNORECASE):
                    edu_entry["degree"] = l
                elif "CGPA" in l or "GPA" in l or "%" in l:
                    edu_entry["score"] = l
                else:
                    if not edu_entry.get("institution"):
                        edu_entry["institution"] = l
                    else:
                        edu_entry["degree"] = f"{edu_entry.get('degree', '')} {l}".strip()
            if edu_entry:
                parsed_sections["education"].append(edu_entry)

        elif key == "skills":
            for l in sec_lines:
                if ":" in l:
                    category, vals = l.split(":", 1)
                    cat_clean = category.strip().lower()
                    val_list = [v.strip() for v in vals.split(",") if v.strip()]
                    if "programming" in cat_clean:
                        parsed_sections["skills"]["programming"].extend(val_list)
                    elif "generative" in cat_clean or "genai" in cat_clean:
                        parsed_sections["skills"]["generative_ai"].extend(val_list)
                    elif "ai" in cat_clean or "ml" in cat_clean or "machine" in cat_clean:
                        parsed_sections["skills"]["ai_ml"].extend(val_list)
                    elif "library" in cat_clean or "libraries" in cat_clean or "framework" in cat_clean:
                        parsed_sections["skills"]["libraries"].extend(val_list)
                    elif "front" in cat_clean:
                        parsed_sections["skills"]["frontend"].extend(val_list)
                    elif "back" in cat_clean:
                        parsed_sections["skills"]["backend"].extend(val_list)
                    elif "tool" in cat_clean:
                        parsed_sections["skills"]["tools"].extend(val_list)
                    else:
                        parsed_sections["skills"]["tools"].extend(val_list)
                else:
                    val_list = [v.strip() for v in l.split(",") if v.strip()]
                    parsed_sections["skills"]["tools"].extend(val_list)

        elif key == "experience":
            exp_list = []
            curr_exp = None
            i = 0
            while i < len(sec_lines):
                l = sec_lines[i]
                if re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d\d)\b', l, re.IGNORECASE):
                    duration = l
                    company = sec_lines[i-1] if i > 0 else "Company"
                    role = None
                    if i + 1 < len(sec_lines):
                        next_l = sec_lines[i+1]
                        if not next_l.startswith("•") and not next_l.startswith("-") and not next_l.startswith("*") and not "Project:" in next_l:
                            role = next_l
                            i += 1
                    curr_exp = {
                        "company": company,
                        "role": role or "Role",
                        "duration": duration,
                        "highlights": []
                    }
                    exp_list.append(curr_exp)
                elif "Project:" in l and curr_exp:
                    curr_exp["project"] = l.replace("Project:", "").strip()
                elif (l.startswith("•") or l.startswith("-") or l.startswith("*")) and curr_exp:
                    curr_exp["highlights"].append(l.strip("•-* "))
                elif curr_exp and curr_exp.get("highlights"):
                    last_h = curr_exp["highlights"][-1]
                    if last_h.endswith("-"):
                        curr_exp["highlights"][-1] = last_h[:-1] + l
                    else:
                        curr_exp["highlights"][-1] = last_h + " " + l
                i += 1
            parsed_sections["experience"] = exp_list

        elif key == "projects":
            proj_list = []
            curr_proj = None
            for l in sec_lines:
                is_bullet = l.startswith("•") or l.startswith("-") or l.startswith("*")
                clean_bullet = l.strip("•-* ")

                if is_bullet:
                    if not curr_proj:
                        curr_proj = {"title": "Project", "technologies": [], "highlights": []}
                    curr_proj["highlights"].append(clean_bullet)
                elif "," in l and curr_proj and not curr_proj.get("technologies") and not curr_proj.get("highlights"):
                    curr_proj["technologies"] = [v.strip() for v in l.split(",")]
                elif curr_proj and curr_proj.get("highlights") and (l[0].islower() or not re.search(r'^[A-Z][A-Za-z0-9\s\-]+$', l) or len(l.split()) > 10):
                    last_h = curr_proj["highlights"][-1]
                    if last_h.endswith("-"):
                        curr_proj["highlights"][-1] = last_h[:-1] + l
                    else:
                        curr_proj["highlights"][-1] = last_h + " " + l
                else:
                    if curr_proj and (curr_proj.get("highlights") or curr_proj.get("technologies")):
                        proj_list.append(curr_proj)
                        curr_proj = None
                    if not curr_proj:
                        curr_proj = {"title": l, "technologies": [], "highlights": []}
                    elif "," in l and not curr_proj.get("technologies"):
                        curr_proj["technologies"] = [v.strip() for v in l.split(",")]
                    else:
                        curr_proj["highlights"].append(l)
            if curr_proj:
                proj_list.append(curr_proj)
            parsed_sections["projects"] = proj_list

        elif key == "certifications":
            for l in sec_lines:
                clean_item = l.strip("•-* ")
                if clean_item:
                    parsed_sections["certifications"].append(clean_item)

        elif key == "achievements":
            for l in sec_lines:
                clean_item = l.strip("•-* ")
                if clean_item:
                    parsed_sections["achievements"].append(clean_item)

    return parsed_sections


def extract_sections_llm(full_text: str) -> dict | None:
    prompt = f"""Extract structured JSON from this candidate resume.
Return ONLY raw valid JSON matching this exact schema:
{{
  "candidate_name": "Full Name",
  "location": "City, State, Country or null",
  "summary": "Professional summary or null",
  "skills": {{
    "programming": ["Python", "SQL"],
    "ai_ml": ["Machine Learning", "NLP"],
    "generative_ai": ["LLMs", "RAG", "Embeddings"],
    "libraries": ["Pandas", "NumPy", "TensorFlow", "PyTorch"],
    "frontend": ["HTML5", "CSS3", "JavaScript", "React.js"],
    "backend": ["FastAPI", "REST APIs"],
    "tools": ["Git", "GitHub", "VS Code"]
  }},
  "education": [
    {{
      "institution": "College / University Name",
      "degree": "Degree Name",
      "year": "Graduation Year",
      "score": "CGPA or percentage"
    }}
  ],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title / Role (Copy verbatim, e.g. 'AI Engineer Intern')",
      "duration": "Start Date - End Date",
      "project": "Project Name if applicable",
      "highlights": [
        "Key responsibility or achievement bullet 1",
        "Key responsibility or achievement bullet 2"
      ]
    }}
  ],
  "projects": [
    {{
      "title": "Project Title",
      "technologies": ["Tech 1", "Tech 2"],
      "description": "Short description",
      "highlights": [
        "Project bullet 1",
        "Project bullet 2"
      ]
    }}
  ],
  "certifications": [
    "Certification 1",
    "Certification 2"
  ],
  "achievements": [
    "Achievement / Award 1",
    "Achievement / Award 2"
  ]
}}

CRITICAL RULES:
1. Do NOT invent missing details.
2. STRICT SOURCE FIDELITY: Copy exact verbatim wording from source resume text. Do NOT summarize or normalize job titles (e.g. output 'AI Engineer Intern', NOT 'Intern / Developer').
3. If a section is absent in resume text, return null or empty array [].
4. Output raw JSON only without markdown ``` json ``` fences.

Resume Source Text:
{full_text[:8000]}"""

    system_prompt = "You are an expert resume parsing system. Output raw JSON ONLY with exact verbatim source fidelity."

    try:
        from backend.services.llm.provider_manager import LLMProviderManager
        manager = LLMProviderManager()
        ans_text, provider, model = manager.generate_raw_completion(prompt=prompt, system_prompt=system_prompt)

        clean_text = ans_text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            if isinstance(parsed, dict) and ("candidate_name" in parsed or "skills" in parsed):
                return parsed
    except Exception as e:
        print(f"LLM Resume Parsing note: {e}")

    return None


def parse_and_store_resume(document_id: str) -> dict:
    meta = DocumentMetadataStore.load_metadata(document_id)
    if not meta:
        raise FileNotFoundError(f"Document '{document_id}' metadata not found.")

    pages = meta.get("pages", [])
    full_text_list = [p.get("normalized_text") or p.get("raw_text") or "" for p in pages]
    full_text = "\n\n".join(full_text_list).strip()

    source_hash = calculate_text_hash(full_text)
    cache_path = os.path.join(RESUME_DATA_DIR, f"{document_id}.json")

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            if cached_data.get("source_text_hash") == source_hash and cached_data.get("parser_version") == PARSER_VERSION:
                analysis = cached_data.get("analysis")
                if analysis:
                    meta["resume_data"] = analysis
                    DocumentMetadataStore.save_metadata(meta)
                    return analysis
        except Exception:
            pass

    if not full_text:
        analysis = {
            "document_id": document_id,
            "document_type": "RESUME",
            "candidate_name": "Unknown Candidate",
            "location": None,
            "summary": None,
            "skills": {
                "programming": [], "ai_ml": [], "generative_ai": [], "libraries": [], "frontend": [], "backend": [], "tools": []
            },
            "all_skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "achievements": []
        }
    else:
        rule_data = detect_sections_from_text(full_text)
        llm_data = extract_sections_llm(full_text)

        if llm_data and isinstance(llm_data, dict):
            analysis = llm_data
            analysis["document_id"] = document_id
            analysis["document_type"] = "RESUME"

            for key in ["candidate_name", "location", "summary"]:
                if rule_data.get(key):
                    analysis[key] = rule_data[key]

            if rule_data.get("experience"):
                rule_exp_map = {e.get("company", "").strip().lower(): e for e in rule_data["experience"] if isinstance(e, dict)}
                if analysis.get("experience"):
                    for exp_item in analysis["experience"]:
                        if isinstance(exp_item, dict):
                            comp_key = exp_item.get("company", "").strip().lower()
                            if comp_key in rule_exp_map:
                                matched_rule = rule_exp_map[comp_key]
                                if matched_rule.get("role"):
                                    exp_item["role"] = matched_rule["role"]
                                if matched_rule.get("company"):
                                    exp_item["company"] = matched_rule["company"]
                                if matched_rule.get("project"):
                                    exp_item["project"] = matched_rule["project"]
                else:
                    analysis["experience"] = rule_data["experience"]

            for key in ["education", "projects", "certifications", "achievements"]:
                if not analysis.get(key) and rule_data.get(key):
                    analysis[key] = rule_data[key]

            if not analysis.get("skills"):
                analysis["skills"] = rule_data.get("skills", {})
        else:
            analysis = rule_data
            analysis["document_id"] = document_id
            analysis["document_type"] = "RESUME"

        skills_obj = analysis.get("skills")
        if not isinstance(skills_obj, dict):
            skills_obj = {
                "programming": skills_obj if isinstance(skills_obj, list) else [],
                "ai_ml": [], "generative_ai": [], "libraries": [], "frontend": [], "backend": [], "tools": []
            }

        all_skills_set = set()
        for cat_list in skills_obj.values():
            if isinstance(cat_list, list):
                for item in cat_list:
                    if isinstance(item, str) and item.strip():
                        all_skills_set.add(item.strip())

        analysis["skills"] = skills_obj
        analysis["all_skills"] = sorted(list(all_skills_set))
        analysis["technical_skills"] = analysis["all_skills"]

    record = {
        "document_id": document_id,
        "document_type": "RESUME",
        "source_text_hash": source_hash,
        "parser_version": PARSER_VERSION,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "analysis": analysis
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    meta["resume_data"] = analysis
    DocumentMetadataStore.save_metadata(meta)

    return analysis
