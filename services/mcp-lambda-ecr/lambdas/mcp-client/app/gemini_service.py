# services/mcp-lambda-ecr/lambdas/mcp-client/app/gemini_service.py
import logging

from google import genai

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self, api_key: str):
        if not api_key:
            logger.error("Gemini API key is missing for GeminiService.")
            raise ValueError("Gemini API Key is required for GeminiService.")

        genai.configure(api_key=api_key)
        # For basic summarization, a flash model is often sufficient and faster.
        self.model = genai.GenerativeModel("gemini-1.5-flash-latest")
        logger.info(f"GeminiService initialized with model: {self.model.model_name}")

    def summarize(self, text_to_summarize: str) -> str:
        if not text_to_summarize:
            logger.warning("Text to summarize is empty. Returning an empty summary.")
            return ""

        try:
            # The prompt is now expected to be fully formed by the caller
            prompt = text_to_summarize
            logger.info(
                f"Sending prompt to Gemini (length: {len(prompt)} chars). Preview:"
                f" '{prompt[:200]}...'"
            )

            # Basic generation call
            response = self.model.generate_content(prompt)

            if response.text:
                summary_text = response.text
                logger.info(
                    f"Gemini API call successful. Response length: {len(summary_text)}."
                    f" Preview: '{summary_text[:200]}...'"
                )
                return summary_text
            else:
                # Handle cases where response.text is empty or None
                logger.warning(
                    f"Gemini API did not return text. Full response: {response}"
                )
                block_reason_msg = "No text content in response."
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    block_reason_msg = (
                        "Content generation blocked:"
                        f" {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}"
                    )
                    logger.error(block_reason_msg)
                elif not response.candidates:
                    block_reason_msg = "No candidates found in response."
                    logger.error(block_reason_msg)
                raise ValueError(
                    f"Failed to get summary from Gemini API: {block_reason_msg}"
                )

        except ValueError as ve:  # Re-raise ValueErrors (e.g., from blocking)
            raise
        except Exception as e:  # Catch other potential exceptions from the SDK
            logger.error(
                f"Error calling Gemini API: {type(e).__name__} - {e}", exc_info=True
            )
            # Check for common API key or permission related issues
            error_str = str(e).upper()
            if (
                "API_KEY" in error_str
                or "PERMISSION_DENIED" in error_str
                or "UNAUTHENTICATED" in error_str
                or "AUTH" in error_str
            ):  # Broader auth check
                raise ValueError(
                    f"Gemini API authentication or permission issue: {str(e)}"
                ) from e
            raise ValueError(
                "Failed to get summary from Gemini API due to an unexpected error:"
                f" {str(e)}"
            ) from e
