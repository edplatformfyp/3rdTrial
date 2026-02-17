import json
from server.core.llm import LLMService
from server.shared.schemas import CourseRoadmap, Chapter
from typing import Optional

class PlannerAgent:
    def __init__(self):
        self.llm = LLMService()

    def generate_roadmap(self, topic: str, grade_level: str, structure_type: str = "week") -> Optional[CourseRoadmap]:
        prompt_structure = "chapters"
        if structure_type == "week":
            prompt_structure = "weeks"
        elif structure_type == "day":
            prompt_structure = "days"
            
        system_prompt = (
            "You are an expert curriculum planner. Create a structured learning roadmap "
            f"for the given topic and grade level. The structure should be organized by {prompt_structure}. "
            "Return ONLY valid JSON matching the following structure: "
            f"{{ \"topic\":String, \"chapters\": [{{ \"chapter_number\": Int, \"title\": String, \"description\": String }}] }}"
            "Note: 'chapter_number' should just be the sequential index. The 'chapters' array should directly contain objects, DO NOT use keys like '0', '1' to wrap them."
        )
        user_prompt = f"Create a {structure_type}-based course roadmap for '{topic}' at a '{grade_level}' level."
        
        with open("debug_planner.txt", "a", encoding="utf-8") as f:
            f.write(f"DEBUG: Generating roadmap for {topic}\n")
        
        response_text = self.llm.generate(user_prompt, system_prompt, json_mode=True)
        
        with open("debug_planner.txt", "a", encoding="utf-8") as f:
            f.write(f"DEBUG: Roadmap response: {response_text}\n")
        
        if not response_text:
            return None

        # Clean markdown code blocks if present
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(cleaned_text)
            
            # Post-Process: Fix potential nesting like [{"0": {...}}, {"1": {...}}]
            if "chapters" in data and isinstance(data["chapters"], list):
                cleaned_chapters = []
                for item in data["chapters"]:
                    keys = list(item.keys())
                    if len(keys) == 1 and keys[0].isdigit():
                        # Unwrap
                        cleaned_chapters.append(item[keys[0]])
                    else:
                        cleaned_chapters.append(item)
                data["chapters"] = cleaned_chapters

            # Validate with Pydantic
            roadmap = CourseRoadmap(**data)
            return roadmap
        except json.JSONDecodeError:
            msg = f"Failed to parse JSON: {cleaned_text}"
            print(msg)
            with open("debug_planner.txt", "a", encoding="utf-8") as f:
                f.write(msg + "\n")
            return None
        except Exception as e:
            msg = f"Validation error: {e}"
            print(msg)
            with open("debug_planner.txt", "a", encoding="utf-8") as f:
                f.write(msg + "\n")
            return None
