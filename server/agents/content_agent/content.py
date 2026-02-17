import json
from server.core.llm import LLMService
from server.shared.schemas import Chapter, ChapterContent, QuizQuestion
from typing import Optional

class ContentAgent:
    def __init__(self):
        self.llm = LLMService()

    def generate_chapter_content(self, chapter: Chapter) -> Optional[ChapterContent]:
        system_prompt = (
            "You are an expert world-class educator. Write a COMPREHENSIVE, DEEP STYLED lecture "
            "for the provided chapter. The content must be formatted as a SERIES OF SLIDES found in a presentation. "
            "Structure it using '## ' for each Slide Title. containing 5-8 slides total. "
            "For each slide, use bullet points ('* ') for key takeaways. "
            "CRITICAL: Do NOT use LaTeX or any complex formatting. Use standard text and emojis. "
            "Strictly avoid '\\' characters or code blocks. "
            "Return ONLY valid JSON. "
            "Format: { \"chapter_title\": String, \"content_markdown\": String (joined with \\n), "
            "\"quiz\": [{ \"question\": String, \"options\": [String], \"correct_answer\": Int }] }"
        )
        user_prompt = f"Write content for Chapter {chapter.chapter_number}: {chapter.title}. Description: {chapter.description}"
        
        response_text = self.llm.generate(user_prompt, system_prompt, json_mode=True)
        
        if not response_text:
            return None

        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(cleaned_text)
            return ChapterContent(**data)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON content: {cleaned_text}")
            return None
        except Exception as e:
            print(f"Validation error: {e}")
            return None
