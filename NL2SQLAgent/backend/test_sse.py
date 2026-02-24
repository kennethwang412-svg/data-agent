"""测试 SSE 聊天接口"""
import json
import requests

BASE = "http://127.0.0.1:8001"

# 1. 创建会话
resp = requests.post(f"{BASE}/api/sessions", json={"title": "SSE测试"})
session = resp.json()
sid = session["id"]
print(f"✅ 会话创建: {sid}\n")

# 2. 测试 SSE 聊天
print("=" * 60)
print("SSE 聊天测试: 各个地区的销售总额是多少？")
print("=" * 60)

resp = requests.post(
    f"{BASE}/api/chat/{sid}",
    json={"message": "各个地区的销售总额是多少"},
    stream=True,
    headers={"Accept": "text/event-stream"},
)

full_answer = ""
event_type = ""
try:
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("event:"):
            event_type = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data = line.split(":", 1)[1].strip()
            if event_type == "sql":
                print(f"\n📝 [SQL] {data}")
            elif event_type == "query_result":
                print(f"\n📊 [查询结果] {data[:200]}...")
            elif event_type == "answer":
                full_answer += data
                print(data, end="", flush=True)
            elif event_type == "chart":
                chart = json.loads(data)
                print(f"\n\n📈 [图表] type={chart.get('chartType')}, title={chart.get('title')}")
                print(f"    option keys: {list(chart.get('option', {}).keys())}")
            elif event_type == "error":
                print(f"\n❌ [错误] {data}")
            elif event_type == "done":
                print(f"\n\n✅ [完成] 回答长度: {len(full_answer)} 字符")
                break
except Exception:
    pass

# 3. 验证会话详情
import time
time.sleep(2)
print("\n" + "=" * 60)
print("验证持久化")
print("=" * 60)
detail = requests.get(f"{BASE}/api/sessions/{sid}").json()
msgs = detail.get("messages", [])
print(f"消息数量: {len(msgs)}")
for m in msgs:
    role = m["role"]
    content = m["content"][:80] if m["content"] else "(empty)"
    has_sql = "✓" if m.get("sql_query") else "✗"
    has_chart = "✓" if m.get("chart_config") else "✗"
    print(f"  [{role}] {content}... | sql={has_sql} chart={has_chart}")

# 4. 清理
requests.delete(f"{BASE}/api/sessions/{sid}")
print(f"\n🗑️ 会话已清理")
