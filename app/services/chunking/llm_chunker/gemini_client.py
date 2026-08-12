import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.dto.boundary_response import BoundaryResponse

load_dotenv()

class GeminiBoundaryResponse(BaseModel):
    boundaries: list[int]

class GeminiClient:

    def __init__(self,model:str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model  = model

    def detect_boundaries(self,prompt:str)->BoundaryResponse:

        response = self.client.models.generate_content(model=self.model,
                                                      contents=prompt,
                                                      config=types.GenerateContentConfig(
                                                          response_mime_type="application/json",
                                                          response_schema=GeminiBoundaryResponse)
                                                      )

        result = GeminiBoundaryResponse.model_validate_json(response.text)

        return BoundaryResponse(boundaries=result.boundaries)
