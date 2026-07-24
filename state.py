from typing import Optional, Literal
from pydantic import BaseModel

class ReportState(BaseModel):
    # 用户输入的研究主题
    topic: str

    # 检索到的资料（文本形式）
    research_notes: Optional[str] = None

    # 报告大纲（Markdown文本）
    outline: Optional[str] = None

    # 报告正文（Markdown文本）
    draft: Optional[str] = None

    # 审查反馈意见
    feedback: Optional[str] = None

    # 当前已修改次数
    revision_count: int = 0

    # 调度器决定下一步去哪个节点（只能填这几个名字之一）
    next: Literal["researcher", "planner", "writer", "critic", "END"] = "researcher"

    # 【第二部分会用】存储结构化的大纲对象（方便下游节点直接读取，不用手动解析字符串）
    structured_outline: Optional[dict] = None