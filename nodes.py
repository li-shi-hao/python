import json
import re
from state import ReportState
from config import get_llm
from tools import search_tool
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List

# 数据模型
class Section(BaseModel):
    title: str
    key_points: List[str]

class OutlineSchema(BaseModel):
    title: str
    sections: List[Section]

# ---------- Researcher ----------
def researcher(state: ReportState) -> dict:
    print(f"[Researcher] 正在搜索主题: {state.topic}")
    notes = search_tool(state.topic)
    print(f"[Researcher] 搜索完成，资料长度: {len(notes)} 字符")
    return {"research_notes": notes}

# 工具：清洗文本提取纯JSON
def clean_extract_json(raw_text: str) -> str:
    match = re.search(r"\{[\s\S]*\}", raw_text)
    if match:
        return match.group(0)
    return raw_text

# ---------- Planner (修复结构化输出报错 + 重试) ----------
def planner(state: ReportState) -> dict:
    print("[Planner] 正在生成报告大纲...")
    llm = get_llm(0.1)
    structured_llm = llm.with_structured_output(OutlineSchema)

    sys_prompt = """
你是结构化大纲生成器，严格遵守规则：
1. 禁止输出任何解释、标题、前言、思考文字，只返回符合OutlineSchema的JSON；
2. 不要加markdown、不要写“大纲如下”“报告大纲”等前缀；
3. JSON字段严格：title(报告标题)、sections数组，每个section包含title、key_points数组；
4. 不输出多余注释、换行说明，仅纯JSON。
"""
    human_prompt = f"""
报告主题：{state.topic}
参考资料：{state.research_notes}
生成完整专业报告大纲。
"""
    messages = [
        SystemMessage(content=sys_prompt),
        HumanMessage(content=human_prompt)
    ]

    max_retry = 2
    outline_obj = None
    for retry in range(max_retry):
        try:
            # 部分模型会夹带文字，先清洗再解析
            raw_resp = llm.invoke(messages).content
            json_str = clean_extract_json(raw_resp)
            outline_obj = structured_llm.invoke(json_str)

            break
        except Exception as e:
            print(f"[Planner] 第{retry+1}次生成失败: {str(e)}")
            continue

    # 兜底逻辑
    if outline_obj is None:
        print(f"[Planner] 生成大纲失败，启用兜底模板")
        fallback_md = f"# {state.topic} 报告\n\n## 引言\n- 背景介绍\n\n## 主体内容\n- 核心分析\n\n## 结论\n- 总结与展望\n"
        return {"outline": fallback_md, "structured_outline": {}}

    # 转Markdown
    md = f"# {outline_obj.title}\n\n"
    for sec in outline_obj.sections:
        md += f"## {sec.title}\n"
        for pt in sec.key_points:
            md += f"- {pt}\n"
        md += "\n"
    print(f"[Planner] 大纲生成成功，共 {len(outline_obj.sections)} 章节")
    return {
        "outline": md,
        "structured_outline": outline_obj.model_dump()
    }

# ---------- Writer ----------
def writer(state: ReportState) -> dict:
    print("[Writer] 正在撰写报告正文...")
    llm = get_llm(0.7)
    prompt = f"""
    主题：{state.topic}
    完整大纲：{state.outline}
    参考资料：{state.research_notes}
    根据大纲撰写完整专业报告，逻辑通顺、论据充足，标准Markdown格式。
    """
    messages = [SystemMessage(content="你是专业行业报告撰写专家。"), HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    draft = response.content
    print(f"[Writer] 报告撰写完成，字数: {len(draft)}")
    return {"draft": draft}

# ---------- Critic ----------
def critic(state: ReportState) -> dict:
    print("[Critic] 正在审查报告...")
    llm = get_llm(0.1)
    prompt = f"""
全面审查这份报告，从内容完整度、逻辑、事实、格式四点评判：
1. 合格直接回复：通过
2. 不合格逐条写出修改位置+修改方案

报告原文：
{state.draft}
"""
    messages = [SystemMessage(content="严谨报告评审专家，回答简洁客观。"), HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    feedback = response.content
    print(f"[Critic] 审查完成，反馈长度: {len(feedback)}")
    return {"feedback": feedback}

# ---------- Supervisor 修复计数BUG ----------
def supervisor(state: ReportState) -> dict:
    current_rev = state.revision_count
    print(f"[Supervisor] 当前修订次数: {current_rev}")
    next_node = ""

    if state.draft is None:
        if state.outline is None:
            next_node = "planner" if state.research_notes else "researcher"
        else:
            next_node = "writer"
    else:
        if state.feedback is None:
            next_node = "critic"
        elif "通过" in state.feedback or current_rev >= 2:
            next_node = "END"
        else:
            next_node = "writer"
            current_rev += 1  # 新计数，不直接修改state对象

    print(f"[Supervisor] 下一步 -> {next_node}")
    # 必须返回新revision_count更新状态
    return {"next": next_node, "revision_count": current_rev}


# import json
# from state import ReportState
# from config import get_llm
# from tools import search_tool
# from langchain_core.messages import HumanMessage, SystemMessage
#
# # ---------- Researcher ----------
# def researcher(state: ReportState) -> dict:
#     print(f"[Researcher] 正在搜索主题: {state.topic}")
#     notes = search_tool(state.topic)
#     print(f"[Researcher] 搜索完成，资料长度: {len(notes)} 字符")
#     return {"research_notes": notes}
#
# # ---------- Planner (结构化输出) ----------
# from pydantic import BaseModel
# from typing import List
#
# class Section(BaseModel):
#     title: str
#     key_points: List[str]
#
# class OutlineSchema(BaseModel):
#     title: str
#     sections: List[Section]
#
# def planner(state: ReportState) -> dict:
#     print("[Planner] 正在生成报告大纲...")
#     llm = get_llm(0.1)  # 低温，确保结构化稳定
#     structured_llm = llm.with_structured_output(OutlineSchema)
#     prompt = f"""
#     主题：{state.topic}
#     资料：{state.research_notes}
#     请根据以上内容生成一份报告大纲，大纲需包含标题和各章节的要点。
#     """
#     try:
#         outline_obj = structured_llm.invoke(prompt)
#         # 转为Markdown
#         md = f"# {outline_obj.title}\n\n"
#         for sec in outline_obj.sections:
#             md += f"## {sec.title}\n"
#             for pt in sec.key_points:
#                 md += f"- {pt}\n"
#             md += "\n"
#         print(f"[Planner] 大纲生成成功，共 {len(outline_obj.sections)} 章节")
#         return {
#             "outline": md,
#             "structured_outline": outline_obj.model_dump()
#         }
#     except Exception as e:
#         print(f"[Planner] 生成大纲失败: {e}")
#         # 兜底大纲
#         fallback = f"# {state.topic} 报告\n\n## 引言\n- 背景介绍\n\n## 主体内容\n- 核心分析\n\n## 结论\n- 总结与展望\n"
#         return {"outline": fallback, "structured_outline": {}}
#
# # ---------- Writer ----------
# def writer(state: ReportState) -> dict:
#     print("[Writer] 正在撰写报告正文...")
#     llm = get_llm(0.7)  # 高温，增强创造力
#     prompt = f"""
#     主题：{state.topic}
#     大纲：{state.outline}
#     资料：{state.research_notes}
#     请根据以上大纲和资料，撰写一份结构完整、论据充分的报告正文。使用Markdown格式。
#     """
#     messages = [SystemMessage(content="你是一位专业的报告撰写专家。"), HumanMessage(content=prompt)]
#     response = llm.invoke(messages)
#     draft = response.content
#     print(f"[Writer] 报告撰写完成，字数: {len(draft)}")
#     return {"draft": draft}
#
# # ---------- Critic ----------
# def critic(state: ReportState) -> dict:
#     print("[Critic] 正在审查报告...")
#     llm = get_llm(0.1)  # 低温，确保稳定评判
#     prompt = f"""
#     请审查以下报告，从完整性、逻辑性、事实准确性、格式规范等方面给出反馈。
#     如果报告质量合格，请回复“通过”，否则请给出具体的修改建议（指出哪里需要改进以及如何改进）。
#
#     报告内容：
#     {state.draft}
#     """
#     messages = [SystemMessage(content="你是一位严谨的报告审查专家。"), HumanMessage(content=prompt)]
#     response = llm.invoke(messages)
#     feedback = response.content
#     print(f"[Critic] 审查完成，反馈长度: {len(feedback)}")
#     return {"feedback": feedback}
#
# # ---------- Supervisor (调度器) ----------
# def supervisor(state: ReportState) -> dict:
#     print(f"[Supervisor] 当前修订次数: {state.revision_count}")
#     # 决策逻辑
#     if state.draft is None:
#         # 还没有草稿
#         if state.outline is None:
#             nxt = "planner" if state.research_notes else "researcher"
#         else:
#             nxt = "writer"
#     else:
#         # 已有草稿
#         if state.feedback is None:
#             nxt = "critic"
#         elif "通过" in state.feedback or state.revision_count >= 2:  # 最大修改次数2
#             nxt = "END"
#         else:
#             nxt = "writer"
#             state.revision_count += 1  # 增加修改计数
#     print(f"[Supervisor] 下一步 -> {nxt}")
#     return {"next": nxt, "revision_count": state.revision_count}