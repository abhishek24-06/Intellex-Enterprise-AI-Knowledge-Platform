from __future__ import annotations

import os

from google import genai
from google.genai import types

class GeminiClient:

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(self,*,api_key:str | None=None,model_name:str=DEFAULT_MODEL):

        self.api_key = (api_key or os.getenv("GEMINI_API_KEY"))

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.model_name = model_name

        self.client = genai.Client(
            api_key=self.api_key,
        )

    def generate(self,*,system_prompt:str,user_prompt:str)->str:

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt)
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text