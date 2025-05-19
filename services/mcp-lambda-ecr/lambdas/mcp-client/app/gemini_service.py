# app/gemini_service.py
import logging

from google import genai as google_genai_sdk  # 新しいSDKのインポート
# from google.generativeai import types as google_genai_types  # オプション設定用

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self, api_key: str):
        # 新しいSDKでは、APIキーはClientオブジェクトの初期化時に渡すか、
        # 環境変数 GOOGLE_API_KEY から自動的に読み込まれる
        self.client = google_genai_sdk.Client(api_key=api_key)
        self.model_name = "gemini-1.5-flash-latest"  # または "gemini-2.0-flash" など

    def summarize(self, text_to_summarize: str) -> str:
        try:
            prompt = f"以下のテキストを簡潔に要約してください:\n\n{textToSummarize}"

            # generation_config や safety_settings は config パラメータ経由で渡す
            # 例:
            # generation_config = google_genai_types.GenerationConfig(
            #     candidate_count=1,
            #     temperature=0.7,
            # )
            # safety_settings =
            # response = self.client.models.generate_content(
            #     model=self.model_name,
            #     contents=prompt,
            #     config=google_genai_types.GenerateContentConfig(
            #         generation_config=generation_config,
            #         safety_settings=safety_settings
            #     )
            # )

            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt  # モデル名を指定
            )

            # 新しいSDKでも response.text でテキストを取得可能
            if response.text:
                summary_text = response.text
                logger.info(f"Gemini API Response: {summary_text}")
                return summary_text
            else:
                # 詳細なエラーハンドリング (旧SDKのものを参考に調整)
                logger.warning(
                    f"Gemini API did not return expected text content: {response}"
                )
                # 安全性設定によりブロックされた場合の確認方法がSDKによって異なる可能性があるため、
                # ドキュメントを参照して適切なエラーハンドリングを行う
                # 例: response.prompt_feedback などで確認
                if (
                    hasattr(response, "prompt_feedback")
                    and response.prompt_feedback
                    and response.prompt_feedback.block_reason
                ):
                    block_reason_message = (
                        response.prompt_feedback.block_reason_message
                        or "Unknown block reason"
                    )
                    logger.error(
                        f"Gemini content generation blocked: {block_reason_message}"
                    )
                    raise ValueError(
                        f"Gemini content generation blocked: {block_reason_message}"
                    )
                raise ValueError(
                    "Failed to get summary from Gemini API: No text content found."
                )

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            # エラーの種類に応じて、より具体的なエラーメッセージを返すことも検討
            if "API_KEY_INVALID" in str(e) or "PermissionDenied" in str(
                e
            ):  # これは一般的なエラー文字列の例
                raise ValueError("Invalid Gemini API Key or insufficient permissions.")
            raise ValueError(f"Failed to get summary from Gemini API: {str(e)}")
