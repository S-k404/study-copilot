"""
Concept Explainer Engine
Supports Anthropic Claude, Google Gemini, and an Offline Mock Mode.
"""

import os
import json
import base64
from io import BytesIO
from PIL import Image

SYSTEM_PROMPT = """You are an expert academic tutor and educational co-pilot.
When given an image or text from a course, lecture, or practice problem:
1. Identify the core question, concept, or code snippet.
2. Provide the direct answer or conceptual conclusion.
3. Break down step-by-step WHY this concept is true.
4. Explain why common alternative choices or misconceptions are incorrect.
5. Provide a key takeaway for future study.

Keep your response structured, concise, and easy to read quickly in a small window or notification."""

CLAUDE_MODEL = "claude-sonnet-5-5"
CLAUDE_LABEL = "Claude Sonnet 5.5"

class ExplainerEngine:
    def __init__(self, mode="auto"):
        """
        mode: 'claude', 'gemini', 'mock', or 'auto'
        """
        self.mode = mode
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        if self.mode == "auto":
            if self.anthropic_key:
                self.mode = "claude"
            elif self.gemini_key:
                self.mode = "gemini"
            else:
                self.mode = "mock"

    def set_mode(self, mode: str):
        self.mode = mode

    def explain_image(self, image: Image.Image) -> dict:
        """
        Takes a PIL Image and returns an explanation dictionary:
        {
            "engine": str,
            "title": str,
            "summary": str,
            "full_explanation": str
        }
        """
        if self.mode == "mock":
            return self._mock_explain("image")
        elif self.mode == "claude":
            return self._claude_explain_image(image)
        elif self.mode == "gemini":
            return self._gemini_explain_image(image)
        else:
            return self._mock_explain("image")

    def explain_text(self, text: str) -> dict:
        """
        Takes a string snippet and returns an explanation dictionary.
        """
        if not text.strip():
            return {
                "engine": self.mode,
                "title": "Empty Input",
                "summary": "No text provided in clipboard.",
                "full_explanation": "Please copy text to your clipboard first and try again."
            }

        if self.mode == "mock":
            return self._mock_explain(f"text: {text[:40]}...")
        elif self.mode == "claude":
            return self._claude_explain_text(text)
        elif self.mode == "gemini":
            return self._gemini_explain_text(text)
        else:
            return self._mock_explain(text)

    def _claude_ask(self, content) -> str:
        """Send one request to Claude and return the text of its reply.

        This model always thinks before it answers, so the reply can start with thinking blocks
        (read the text by block type) and max_tokens has to leave room for both.
        If its safety checks decline a request, the API retries it on a fallback model where it can.
        """
        from anthropic import Anthropic
        client = Anthropic(api_key=self.anthropic_key)
        response = client.beta.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
        if response.stop_reason == "refusal":
            return "Claude declined to explain this content. Try another engine from the menu."
        return next((block.text for block in response.content if block.type == "text"), "")

    def _claude_explain_image(self, image: Image.Image) -> dict:
        try:
            # Convert PIL image to PNG base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            raw_text = self._claude_ask([
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_b64,
                    }
                },
                {
                    "type": "text",
                    "text": "Analyze the question or educational content in this screenshot and provide the breakdown."
                }
            ])
            first_line = raw_text.splitlines()[0] if raw_text else "Analysis Complete"
            return {
                "engine": CLAUDE_LABEL,
                "title": first_line[:60],
                "summary": first_line,
                "full_explanation": raw_text
            }
        except Exception as e:
            return {
                "engine": "Claude (Error)",
                "title": "API Error",
                "summary": str(e),
                "full_explanation": f"Failed to call Claude API: {e}\n\nCheck your ANTHROPIC_API_KEY environment variable."
            }

    def _gemini_explain_image(self, image: Image.Image) -> dict:
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)
            
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    image,
                    SYSTEM_PROMPT + "\n\nAnalyze this screenshot and explain the core problem and solutions."
                ]
            )
            raw_text = response.text or "No response generated."
            first_line = raw_text.splitlines()[0] if raw_text else "Analysis Complete"
            return {
                "engine": "Gemini 2.5 Flash",
                "title": first_line[:60],
                "summary": first_line,
                "full_explanation": raw_text
            }
        except Exception as e:
            return {
                "engine": "Gemini (Error)",
                "title": "API Error",
                "summary": str(e),
                "full_explanation": f"Failed to call Gemini API: {e}\n\nCheck your GEMINI_API_KEY environment variable."
            }

    def _claude_explain_text(self, text: str) -> dict:
        try:
            raw_text = self._claude_ask(f"Analyze and explain this concept/problem:\n\n{text}")
            first_line = raw_text.splitlines()[0] if raw_text else "Analysis Complete"
            return {
                "engine": CLAUDE_LABEL,
                "title": first_line[:60],
                "summary": first_line,
                "full_explanation": raw_text
            }
        except Exception as e:
            return {
                "engine": "Claude (Error)",
                "title": "API Error",
                "summary": str(e),
                "full_explanation": f"Failed to call Claude API: {e}"
            }

    def _gemini_explain_text(self, text: str) -> dict:
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{SYSTEM_PROMPT}\n\nAnalyze and explain this problem:\n\n{text}"
            )
            raw_text = response.text or "No response generated."
            first_line = raw_text.splitlines()[0] if raw_text else "Analysis Complete"
            return {
                "engine": "Gemini 2.5 Flash",
                "title": first_line[:60],
                "summary": first_line,
                "full_explanation": raw_text
            }
        except Exception as e:
            return {
                "engine": "Gemini (Error)",
                "title": "API Error",
                "summary": str(e),
                "full_explanation": f"Failed to call Gemini API: {e}"
            }

    def _mock_explain(self, source_info: str) -> dict:
        """
        Realistic simulated response demonstrating step-by-step breakdown.
        """
        return {
            "engine": "Simulation / Mock Mode (Offline)",
            "title": "Simulated Analysis: Algorithm Complexity & Memory Model",
            "summary": "Answer: Option B [O(N log N) average, O(N^2) worst case]",
            "full_explanation": (
                "🎯 Core Concept Identified: QuickSort Complexity Analysis\n\n"
                "✅ Correct Conclusion: Option B\n"
                "• Average Case: O(N log N) — Achieved when the pivot divides the list roughly in half.\n"
                "• Worst Case: O(N^2) — Occurs when the pivot is consistently the minimum or maximum element (e.g. already sorted list with naive first-element pivot).\n\n"
                "❌ Distractor Breakdown:\n"
                "• Option A [O(N) best case]: While 3-way partitioning can approach O(N) for duplicate keys, standard QuickSort best case is O(N log N).\n"
                "• Option C [O(1) auxiliary space]: QuickSort requires O(log N) stack space for recursive calls, unlike truly in-place HeapSort.\n\n"
                "💡 Study Takeaway: Always watch out for pivot selection strategies (e.g. median-of-three, randomized pivot) designed to guard against the O(N^2) worst-case degradation.\n\n"
                "(Note: Set ANTHROPIC_API_KEY or GEMINI_API_KEY in your environment to use live AI models instead of this simulation.)"
            )
        }

