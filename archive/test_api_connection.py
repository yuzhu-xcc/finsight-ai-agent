"""
Week 3 / Day 15：AI Agent 第一步 —— 先确认能不能连上Claude API
在搭建复杂的Agent逻辑之前，先跑一个最简单的测试，
确认：API key有效、网络能连通、SDK装对了。
"""
import os

from anthropic import Anthropic

api_key = os.environ.get("ANTHROPIC_API_KEY")

if not api_key:
    print("❌ 没有找到 ANTHROPIC_API_KEY 这个环境变量，说明还没设置好。")
    print("先看下面的说明设置好，再重新运行这个脚本。")
else:
    print("✅ 找到了API key，正在测试连接...")
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "用一句话介绍一下你自己"}],
    )
    print("✅ 连接成功！Claude的回复：")
    print(response.content[0].text)
