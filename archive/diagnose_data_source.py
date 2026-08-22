"""
数据源诊断脚本
目的：不再瞎猜"网络不行"，而是一层层测试，看清楚到底卡在哪一步。

运行方式：在你的 finsight-ai-agent 文件夹终端里跑：
python3 diagnose_data_source.py

跑完之后，把终端里【全部】打印出来的文字复制粘贴给我（不用截图）。
文字比图片对我来说更容易看清楚报错细节，尤其是报错信息，图片有时候会看不清楚具体是哪一行。
"""

print("=== 步骤1：先测试最基本的网络能力（跟股票数据无关）===")
# 这一步只是测试：你的电脑能不能正常访问外部网站。
# 如果连这个都失败，说明问题出在网络本身（比如公司/学校网络限制），跟akshare、yfinance都没关系。
import requests
try:
    r = requests.get("https://www.baidu.com", timeout=5)
    print("✅ 能正常访问百度，状态码：", r.status_code)
except Exception as e:
    print("❌ 连百度都连不上，说明是网络本身的问题：")
    print(e)

print()
print("=== 步骤2：检查akshare有没有正确安装、版本是多少 ===")
# akshare这个库更新很快，版本太旧的话，里面某些接口可能已经失效或者改了用法。
import akshare as ak
print("akshare版本：", ak.__version__)

print()
print("=== 步骤3：测试A股数据（akshare里最稳定、用的人最多的接口，先排除是不是akshare整体坏了）===")
# 这里查的是贵州茅台（600519），纯粹因为这是最常用的测试股票代码，跟你的项目内容无关，只是用来验证接口通不通。
try:
    a_data = ak.stock_zh_a_hist(
        symbol="600519", period="daily",
        start_date="20260601", end_date="20260703", adjust=""
    )
    print("✅ A股数据获取成功！前5行：")
    print(a_data.head())
except Exception as e:
    print("❌ 连A股数据都失败了，完整报错信息如下：")
    print(repr(e))

print()
print("=== 步骤4：测试港股数据，把完整报错打印出来（不是只看到'失败'两个字）===")
try:
    hk_data = ak.stock_hk_hist(
        symbol="00700", period="daily",
        start_date="20260601", end_date="20260703", adjust=""
    )
    print("✅ 港股数据获取成功！前5行：")
    print(hk_data.head())
except Exception as e:
    print("❌ 港股数据失败，完整报错信息如下：")
    print(repr(e))

print()
print("=== 诊断完成 ===")
print("把上面【从步骤1开始的全部文字】复制粘贴发给我，我们根据具体报错判断下一步怎么修。")
