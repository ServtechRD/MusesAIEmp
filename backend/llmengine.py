import os
# import openai
# for future
# from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from dotenv import load_dotenv
from openai import OpenAI


class LLMEngine:
    def __init__(self):
        # 加載 .env 文件
        load_dotenv()

        # 從環境變量中獲取 API 密鑰
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        # self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        # if not self.anthropic_api_key:
        #    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        # 初始化 OpenAI
        # openai.api_key = self.openai_api_key
        self.client = OpenAI(api_key=self.openai_api_key)

        # 初始化 Anthropic (Claude)
        # self.anthropic = Anthropic(api_key=self.anthropic_api_key)

    def askllm(self, llm_mode, model, prompts):
        if llm_mode == "openai":
            return self._ask_gpt(model, prompts)
        # elif llm_mode == "claude":
        #    return self._ask_claude(prompt)
        else:
            raise ValueError(f"Unsupported LLM mode: {llm_mode}")

    def _ask_gpt(self, model, prompts):
        # response = openai.ChatCompletion.create(
        #    model="gpt-3.5-turbo",  # 或者其他 GPT 模型
        #    messages=[{"role": "user", "content": prompt}]
        # )
        response = self.client.chat.completions.create(
            # files=[file_object],
            messages=prompts,
            model=model)
        return response.choices[0].message.content.strip()

   # def _ask_claude(self, prompt):
   #     response = self.anthropic.completions.create(
   #         model="claude-2",  # 或者其他 Claude 模型
   #         prompt=f"{HUMAN_PROMPT} {prompt}{AI_PROMPT}",
   #         max_tokens_to_sample=300
   #     )
   #     return response.completion.strip()
