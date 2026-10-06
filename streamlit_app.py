"""
FinSight 网页版 Agent
这个文件只负责"网页界面"，真正的逻辑（工具、系统提示词、对话循环）都在 finsight_core.py。
"""
import os
import tempfile

import streamlit as st
from anthropic import Anthropic

from finsight_core import run_agent_turn

# 云端服务器上，生成的Excel放进系统临时目录（本地终端版则默认放在项目的 reports 文件夹）
os.environ.setdefault("FINSIGHT_REPORT_DIR", tempfile.gettempdir())

EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

st.set_page_config(page_title="FinSight Agent", page_icon="📈")
st.title("📈 FinSight — AI 金融数据分析 Agent")
st.caption("任意A股/港股 · 实时优先，联网失败自动降级 · 可生成Excel报告 · 基于 Claude function calling")

client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# session_state：网页每次交互都会把整个脚本重跑一遍，所以对话历史必须存在这里，否则每次都会"失忆"
if "api_messages" not in st.session_state:
    st.session_state.api_messages = []      # 给Claude用的完整历史（含工具调用细节）
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []  # 给界面显示用的简化版：{"role","text","files"}


def render_downloads(files, msg_index):
    """把这条消息生成的Excel文件，显示成下载按钮。"""
    for j, path in enumerate(files):
        if os.path.exists(path):
            with open(path, "rb") as f:
                st.download_button(
                    label=f"📥 下载 Excel 报告（{os.path.basename(path)}）",
                    data=f.read(),
                    file_name=os.path.basename(path),
                    mime=EXCEL_MIME,
                    key=f"download_{msg_index}_{j}",
                )
        else:
            st.caption("（这份报告文件已过期，请重新生成）")


# 把之前的对话重新画出来
for i, msg in enumerate(st.session_state.display_messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])
        render_downloads(msg.get("files", []), i)

user_input = st.chat_input("问问关于A股/港股的问题，比如“腾讯最近表现怎么样”或“帮我生成腾讯和茅台的Excel报告”")

if user_input:
    st.session_state.display_messages.append({"role": "user", "text": user_input, "files": []})
    with st.chat_message("user"):
        st.markdown(user_input)

    checkpoint = len(st.session_state.api_messages)  # 出错时用来回滚，避免对话历史处于半截状态
    st.session_state.api_messages.append({"role": "user", "content": user_input})

    generated_files = []

    def collect_files(tool_name, tool_input, result):
        if isinstance(result, dict) and result.get("file_path"):
            generated_files.append(result["file_path"])

    with st.chat_message("assistant"):
        try:
            with st.spinner("正在查询数据..."):
                answer = run_agent_turn(
                    client, st.session_state.api_messages, on_tool_result=collect_files
                )
            st.markdown(answer)
            render_downloads(generated_files, len(st.session_state.display_messages))
            st.session_state.display_messages.append(
                {"role": "assistant", "text": answer, "files": generated_files}
            )
        except Exception:
            # 比如API额度用完、网络问题：给访问者一句人话，而不是一屏红色报错
            del st.session_state.api_messages[checkpoint:]
            notice = "⚠️ 抱歉，服务暂时不可用（可能是接口额度或网络问题），请稍后再试。"
            st.error(notice)
            st.session_state.display_messages.append({"role": "assistant", "text": notice, "files": []})
