# app/gemini_service.py
import logging

import google.genai as genai

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)  #
        # 利用可能なモデルを確認したい場合は以下を実行
        # for m in genai.list_models():
        #   if 'generateContent' in m.supported_generation_methods:
        #     print(m.name)
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash-latest"
        )  # 例: gemini-1.5-flash-latest

    def summarize(self, text_to_summarize: str) -> str:
        try:
            prompt = f"以下のテキストを簡潔に要約してください:\n\n{textToSummarize}"
            response = self.model.generate_content(prompt)  #

            # response.text でテキスト部分を取得
            # response.parts でより詳細な情報を取得可能
            # response.prompt_feedback でプロンプトに関するフィードバックを確認可能
            if response.candidates and response.candidates.content.parts:
                summary_text = "".join(
                    part.text for part in response.candidates.content.parts
                )
                logger.info(f"Gemini API Response: {summary_text}")
                return summary_text
            elif response.text:  # シンプルなテキスト応答の場合
                logger.info(f"Gemini API Response (simple text): {response.text}")
                return response.text
            else:
                logger.warning(
                    f"Gemini API did not return expected content structure: {response}"
                )
                # 安全性設定によりブロックされた可能性などを考慮
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    logger.error(
                        "Gemini content generation blocked:"
                        f" {response.prompt_feedback.block_reason_message}"
                    )
                    raise ValueError(
                        "Gemini content generation blocked:"
                        f" {response.prompt_feedback.block_reason_message}"
                    )
                raise ValueError(
                    "Failed to get summary from Gemini API: No content found."
                )

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            raise ValueError(f"Failed to get summary from Gemini API: {str(e)}")
