"""
单独测试 Excel 生成功能：不经过 Claude，不需要 API key。
使用前请先关闭 VPN（让新浪数据源能正常连接）。
运行：python3 test_excel_local.py
"""
import os

from finsight_core import generate_excel_report

result = generate_excel_report([
    {"ticker": "00700", "name": "腾讯"},
    {"ticker": "600519", "name": "贵州茅台"},
])

if "error" in result:
    print("❌ 失败：", result)
else:
    print("✅ 已生成：", os.path.abspath(result["file_path"]))
    for s in result["included"]:
        print("  ", s["ticker"], s["name"], s["start_date"], "->", s["end_date"], "|", s["source"])
    if result["failed"]:
        print("⚠️ 失败的股票：", result["failed"])
