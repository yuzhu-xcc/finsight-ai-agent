"""
FinSight 终端版 Agent
这个文件只负责"在终端里收发消息"，真正的逻辑（工具、系统提示词、对话循环）都在 finsight_core.py。
"""
import os

from anthropic import Anthropic

from finsight_core import run_agent_turn


def print_tool_call(name, tool_input, result):
    """每次AI调用工具时，在终端打印一行过程；如果生成了Excel，再打印文件位置。"""
    print(f"  🔧 调用工具：{name}，参数：{tool_input}")
    if isinstance(result, dict) and result.get("file_path"):
        print(f"  📄 已生成报告文件：{os.path.abspath(result['file_path'])}")


def main():
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = []  # 保存完整对话历史，Claude才能"记得"之前聊过什么

    print("FinSight Agent 已启动，输入你的问题（输入 exit 退出）\n")
    while True:
        user_input = input("你：")
        if user_input.strip().lower() in ("exit", "quit", "退出"):
            print("再见！")
            break

        messages.append({"role": "user", "content": user_input})
        answer = run_agent_turn(client, messages, on_tool_result=print_tool_call)
        print(f"\nAgent：{answer}\n")


if __name__ == "__main__":
    main()
