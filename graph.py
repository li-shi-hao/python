from langgraph.graph import StateGraph, END
from state import ReportState
from nodes import researcher, planner, writer, critic, supervisor
from langgraph.checkpoint.memory import MemorySaver  # 内置内存检查点，可存为SqliteSaver

def build_graph():
    builder = StateGraph(ReportState)
    builder.add_node("researcher", researcher)
    builder.add_node("planner", planner)
    builder.add_node("writer", writer)
    builder.add_node("critic", critic)
    builder.add_node("supervisor", supervisor)

    builder.set_entry_point("supervisor")

    # 条件边：supervisor 根据 state.next 路由
    builder.add_conditional_edges(
        "supervisor",
        lambda state: state.next,
        {
            "researcher": "researcher",
            "planner": "planner",
            "writer": "writer",
            "critic": "critic",
            "END": END,
        }
    )

    # 所有执行节点完成后，回到 supervisor
    for node in ["researcher", "planner", "writer", "critic"]:
        builder.add_edge(node, "supervisor")

    # 编译，启用检查点（用于中断恢复）
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    return graph