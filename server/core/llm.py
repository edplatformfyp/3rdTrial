import os
import sys
print(f"DEBUG: sys.stdout.encoding = {sys.stdout.encoding}")
import time
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
import google.generativeai as genai

load_dotenv()

class LLMService:
    def __init__(self, provider: str = "groq"):
        self.provider = provider
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

        with open("debug_init.txt", "a") as f:
             f.write(f"Init LLMService. Provider: {provider}\n")
             mask_groq = self.groq_api_key[:4] + "..." + self.groq_api_key[-4:] if self.groq_api_key else "None"
             mask_gemini = self.gemini_api_key[:4] + "..." + self.gemini_api_key[-4:] if self.gemini_api_key else "None"
             f.write(f"GROQ_KEY: '{mask_groq}'\n")
             f.write(f"GEMINI_KEY: '{mask_gemini}'\n")
             f.write(f"CWD: {os.getcwd()}\n")

        self.groq_client = None
        if self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                print(f"Failed to init Groq client: {e}")

        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                print(f"Failed to init Gemini client: {e}")

    def generate(self, prompt: str, system_instruction: str = "", retries: int = 3, json_mode: bool = False) -> Optional[str]:
        print(f"DEBUG: LLM Generate. Provider: {self.provider}")
        print(f"DEBUG: GEMINI_KEY present: {bool(self.gemini_api_key)}")
        
        # Try primary provider first
        try:
            if self.provider == "groq" and self.groq_client:
                return self._call_groq(prompt, system_instruction, json_mode)
            elif self.provider == "gemini" and self.gemini_api_key:
                return self._call_gemini(prompt, system_instruction)
        except Exception as e:
             error_msg = f"Primary provider ({self.provider}) failed: {e}"
             print(error_msg)
             with open("debug_log.txt", "a") as f:
                 f.write(error_msg + "\n")

             # Fallback to Gemini if Groq fails
             if self.provider == "groq" and self.gemini_api_key:
                 print("Attempting fallback to Gemini...")
                 with open("debug_log.txt", "a") as f:
                     f.write("Attempting fallback to Gemini...\n")
                 try:
                     return self._call_gemini(prompt, system_instruction)
                 except Exception as e2:
                     print(f"Fallback to Gemini failed: {e2}")
                     with open("debug_log.txt", "a") as f:
                         f.write(f"Fallback to Gemini failed: {e2}\n")

        return None

    def _call_groq(self, prompt: str, system_instruction: str, json_mode: bool = False) -> str:
        import requests
        import json
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": system_instruction,
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "model": "llama-3.1-8b-instant",
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            print(f"DEBUG: Sending RAW request to Groq. Key len: {len(self.groq_api_key)}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                error_msg = f"Groq RAW Error: {response.status_code} - {response.text}"
                print(error_msg)
                with open("debug_log.txt", "a") as f:
                    f.write(error_msg + "\n")
                raise Exception(error_msg)
                
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            error_msg = f"Groq RAW Exception: {e}"
            print(error_msg)
            with open("debug_log.txt", "a") as f:
                f.write(error_msg + "\n")
            raise e

    def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        try:
            full_prompt = f"System: {system_instruction}\n\nUser: {prompt}"
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
             print(f"Gemini SDK Error: {e}")
             raise e
