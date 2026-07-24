import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# 配置LLM（兼容DeepSeek或其他OpenAI兼容接口）
LLM = ChatOpenAI(
    model="glm-4-flash",          # 或 "gpt-4o-mini" 等
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
)

# 为不同Agent准备不同温度的模型实例
def get_llm(temperature: float):
    return ChatOpenAI(
        model="glm-4-flash",
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
    )