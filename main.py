import argparse
import datetime
from graph import build_graph
from state import ReportState

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, required=True, help="研究主题")
    args = parser.parse_args()

    # 初始状态
    initial_state = ReportState(topic=args.topic)
    graph = build_graph()

    # 配置检查点（thread_id用于恢复）
    config = {"configurable": {"thread_id": "report_thread"}}

    print(f"\n=== 开始生成报告，主题：{args.topic} ===\n")
    try:
        # 运行工作流
        final_state = graph.invoke(initial_state, config)
        # 或者用 stream 观察中间步骤，这里用 invoke 简化
        print("\n=== 工作流执行完毕 ===\n")
        print(f"修改次数: {final_state['revision_count']}")
        print(f"大纲预览: {final_state['outline'][:200]}...")
        print(f"报告字数: {len(final_state['draft'])}")
        # 保存文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"报告_{args.topic.replace(' ', '_')}_{timestamp}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_state["outline"] + "\n\n---\n\n" + final_state["draft"])
        print(f"\n报告已保存至: {filename}")
        # 打印运行摘要
        print("\n=== 运行摘要 ===")
        print(f"总步数: 未统计 (需实现步数计数，此处略)")
        print(f"最终修订次数: {final_state['revision_count']}")
        print(f"反馈: {final_state.get('feedback', '无')[:100]}...")
    except Exception as e:
        print(f"运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()