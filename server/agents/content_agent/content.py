import json
from server.core.llm import LLMService
from server.shared.schemas import Chapter, ChapterContent, QuizQuestion
from typing import Optional

class ContentAgent:
    def __init__(self):
        self.llm = LLMService()

    def generate_chapter_content(self, chapter: Chapter) -> Optional[ChapterContent]:
        system_prompt = (
            "You are an expert world-class educator. Write a HIGHLY EXHAUSTIVE, deeply detailed, and "
            "comprehensive lecture for the provided chapter. The content must be formatted as a SERIES OF SLIDES "
            "found in a presentation, containing 6-10 slides total. Each slide MUST have at least 150-250 words of rich content. "
            "Structure it using '## ' for each Slide Title. "
            "CRITICAL FORMATTING RULES: "
            "1. You MUST use standard Markdown syntax (bolding `**`, lists `-`, etc.). "
            "2. If mathematics, formulas, or equations are relevant, you MUST use LaTeX math formatting enclosed in "
            "dollar signs. Use inline math like `$E=mc^2$` and block math like `$$E=mc^2$$`. Since this is returned "
            "in JSON, BE SURE to properly escape your backslashes (e.g. `\\\\frac`). "
            "3. Embed 1-2 highly relevant, dynamic images within each slide where appropriate. To do this, use standard "
            "markdown image syntax with a public placeholder API (e.g., `![Visual Representation](https://loremflickr.com/800/400/education,keyword)` "
            "Replace 'keyword' with 1 or 2 specific topic words). "
            "4. Make the content incredibly dense, professional, visually engaging, and thoroughly explanatory. "
            "Return ONLY perfectly valid JSON. Do not return markdown wrappers. "
            "Format: { \"chapter_title\": String, \"content_markdown\": String (joined with \\n\\n), "
            "\"quiz\": [{ \"question\": String, \"options\": [String], \"correct_answer\": Int }] }"
        )
        user_prompt = f"Write deeply comprehensive content for Chapter {chapter.chapter_number}: {chapter.title}. Description: {chapter.description}"
        
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
