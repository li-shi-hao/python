import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

# 优先使用Tavily（如果你有key），否则使用DuckDuckGo
USE_TAVILY = os.getenv("TAVILY_API_KEY") is not None

if USE_TAVILY:
    from tavily import TavilyClient
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def _search_with_retry(query: str):
        return client.search(query, max_results=5)
    def _format_results(result):
        return "\n".join([f"- {r['title']}: {r['content']}" for r in result["results"]])
else:
    from ddgs import DDGS
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def _search_with_retry(query: str):
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=5))
    def _format_results(result):
        return "\n".join([f"- {r['title']}: {r['body']}" for r in result])

def search_tool(topic: str) -> str:
    try:
        raw = _search_with_retry(topic)
        if raw:
            return _format_results(raw)
        else:
            return f"未找到关于 '{topic}' 的具体资料，请基于通用知识撰写。"
    except Exception as e:
        print(f"[搜索警告] 搜索服务不可用，启用降级方案。错误: {e}")
        return f"搜索服务暂时不可用。以下是基于主题 '{topic}' 的通用知识进行报告撰写。"