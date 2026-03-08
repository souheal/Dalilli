from typing import Optional
from app.config import settings

# Only import ollama if LLM is enabled
if settings.enable_llm:
    try:
        import ollama
        OLLAMA_AVAILABLE = True
    except ImportError:
        OLLAMA_AVAILABLE = False
else:
    OLLAMA_AVAILABLE = False


class LLMService:
    """Service for interacting with LLM models via Ollama"""

    def __init__(
        self,
        model_name: str = "llama3",
        temperature: float = 0.1,
        max_tokens: int = 2048
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enabled = settings.enable_llm and OLLAMA_AVAILABLE

        if self.enabled:
            self.client = ollama.Client(host=settings.ollama_base_url)
        else:
            self.client = None

    def generate_answer(self, query: str, context: str) -> str:
        """Generate an answer based on the query and context"""
        if not self.enabled:
            # Return context directly when LLM is disabled
            return f"**Retrieved Information:**\n\n{context}\n\n---\n*Note: AI answer generation is disabled. Above is the relevant context from your documents.*"

        system_prompt = """أنت مساعد ذكي متخصص في الإجابة على الأسئلة بناءً على السياق المقدم.
قواعد الإجابة:
- أجب دائماً باللغة العربية
- اعتمد فقط على المعلومات الموجودة في السياق المقدم
- كن دقيقاً ومختصراً وواضحاً
- إذا كان السياق لا يحتوي على معلومات كافية، قل ذلك بوضوح
- لا تختلق معلومات غير موجودة في السياق
- استخدم المصطلحات القانونية كما وردت في النص الأصلي"""

        user_prompt = f"""السياق:
{context}

السؤال: {query}

أجب على السؤال بناءً على السياق أعلاه بشكل شامل ودقيق باللغة العربية."""

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def rewrite_query(self, query: str) -> str:
        """Rewrite the query for better retrieval"""
        if not self.enabled:
            return query

        system_prompt = """أنت مساعد لإعادة صياغة الاستعلامات لتحسين البحث في المستندات.
أعد صياغة الاستعلام بحيث:
- يكون أكثر وضوحاً وتحديداً
- يتضمن مرادفات أو مصطلحات ذات صلة
- يحافظ على اللغة الأصلية للاستعلام (عربي يبقى عربي)
- يحافظ على المعنى الأصلي

أعد فقط الاستعلام المعاد صياغته، بدون أي شرح."""

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"أعد صياغة هذا الاستعلام: {query}"}
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 200
                }
            )
            return response["message"]["content"].strip()
        except Exception:
            return query

    def extract_metadata(self, text: str) -> dict:
        """Extract metadata from document text"""
        if not self.enabled:
            return {}

        system_prompt = """Extract key metadata from the following document text.
Return a JSON object with the following fields (if found):
- title: Document title
- date: Any dates mentioned
- parties: Names of parties/companies mentioned
- type: Type of document (contract, invoice, report, etc.)
- summary: Brief 1-2 sentence summary

Return only valid JSON, nothing else."""

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract metadata from:\n\n{text[:2000]}"}
                ],
                options={
                    "temperature": 0.1,
                    "num_predict": 500
                }
            )
            import json
            return json.loads(response["message"]["content"])
        except Exception:
            return {}
