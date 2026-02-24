"""Phase 4 端到端验收测试脚本"""
import json
import time
import requests

BASE = "http://127.0.0.1:8001"

def test_scenario_1():
    """场景1: 新建会话 -> 自然语言提问 -> SQL/结果/回答/图表 全链路"""
    print("\n" + "=" * 60)
    print("场景 1: 新建会话 + 自然语言提问")
    print("=" * 60)

    resp = requests.post(f"{BASE}/api/sessions", json={"title": "新对话"})
    assert resp.status_code == 201, f"创建会话失败: {resp.status_code}"
    session = resp.json()
    sid = session["id"]
    print(f"  [OK] 创建会话: {sid}, title={session['title']}")

    events = {}
    answer_chunks = []
    resp = requests.post(
        f"{BASE}/api/chat/{sid}",
        json={"message": "各地区的销售总额是多少"},
        stream=True,
    )
    assert resp.status_code == 200, f"SSE 请求失败: {resp.status_code}"

    current_event = ""
    data_lines = []
    try:
        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip(" "))
            elif line.strip() == "":
                if current_event and data_lines:
                    data = "\n".join(data_lines)
                    if current_event == "answer":
                        answer_chunks.append(data)
                    else:
                        events[current_event] = data
                current_event = ""
                data_lines = []
    except Exception:
        pass

    assert "sql" in events, "未收到 sql 事件"
    print(f"  [OK] 收到 SQL:\n       {events['sql'][:80]}...")

    assert "query_result" in events, "未收到 query_result 事件"
    qr = json.loads(events["query_result"])
    assert isinstance(qr, list) and len(qr) > 0, "query_result 不是有效 JSON 列表"
    print(f"  [OK] 收到 query_result: {len(qr)} 行, 首行={qr[0]}")

    full_answer = "".join(answer_chunks)
    assert len(full_answer) > 20, f"AI 回答太短: {len(full_answer)} 字符"
    print(f"  [OK] 收到 answer: {len(full_answer)} 字符")

    assert "chart" in events, "未收到 chart 事件"
    chart = json.loads(events["chart"])
    assert "chartType" in chart, "chart 缺少 chartType 字段"
    assert "option" in chart, "chart 缺少 option 字段"
    print(f"  [OK] 收到 chart: type={chart['chartType']}, title={chart.get('title', '')}")

    assert "done" in events or events.get("done") == "", "未收到 done 事件"
    print(f"  [OK] 收到 done 事件")

    return sid


def test_scenario_2(sid: str):
    """场景2: 同一会话追问 -> 验证上下文记忆"""
    print("\n" + "=" * 60)
    print("场景 2: 同一会话追问 (上下文记忆)")
    print("=" * 60)

    events = {}
    answer_chunks = []
    resp = requests.post(
        f"{BASE}/api/chat/{sid}",
        json={"message": "按月份展示销售趋势"},
        stream=True,
    )
    assert resp.status_code == 200

    current_event = ""
    data_lines = []
    try:
        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line
            if line.startswith("event:"):
                current_event = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].lstrip(" "))
            elif line.strip() == "":
                if current_event and data_lines:
                    data = "\n".join(data_lines)
                    if current_event == "answer":
                        answer_chunks.append(data)
                    else:
                        events[current_event] = data
                current_event = ""
                data_lines = []
    except Exception:
        pass

    assert "sql" in events, "追问未收到 sql"
    sql = events["sql"].upper()
    print(f"  [OK] 追问生成 SQL:\n       {events['sql'][:80]}...")

    assert "query_result" in events, "追问未收到 query_result"
    qr = json.loads(events["query_result"])
    print(f"  [OK] 追问 query_result: {len(qr)} 行")

    full_answer = "".join(answer_chunks)
    assert len(full_answer) > 10
    print(f"  [OK] 追问 answer: {len(full_answer)} 字符")

    chart = json.loads(events.get("chart", "{}"))
    if chart:
        print(f"  [OK] 追问 chart: type={chart.get('chartType')}")
    else:
        print(f"  [WARN] 追问未生成图表")

    return sid


def test_scenario_3(sid: str):
    """场景3: 切换会话 -> 历史消息和图表正确加载"""
    print("\n" + "=" * 60)
    print("场景 3: 切换会话 (历史消息加载)")
    print("=" * 60)

    time.sleep(2)

    resp = requests.get(f"{BASE}/api/sessions/{sid}")
    assert resp.status_code == 200
    detail = resp.json()
    session_info = detail["session"]
    messages = detail["messages"]

    assert len(messages) >= 4, f"消息数应 >= 4 (2轮对话), 实际={len(messages)}"
    print(f"  [OK] 会话 {sid[:8]}... 加载了 {len(messages)} 条消息")

    roles = [m["role"] for m in messages]
    assert roles == ["user", "assistant", "user", "assistant"], f"消息角色顺序异常: {roles}"
    print(f"  [OK] 消息角色顺序: {roles}")

    ai_msg_1 = messages[1]
    assert ai_msg_1["sql_query"], "第一轮 AI 消息缺少 sql_query"
    assert ai_msg_1["query_result"], "第一轮 AI 消息缺少 query_result"
    assert ai_msg_1["content"], "第一轮 AI 消息缺少 content"
    assert ai_msg_1["chart_config"], "第一轮 AI 消息缺少 chart_config"
    print(f"  [OK] 第一轮 AI 消息字段完整: sql/query_result/content/chart_config")

    chart1 = ai_msg_1["chart_config"]
    if isinstance(chart1, str):
        chart1 = json.loads(chart1)
    assert "chartType" in chart1, "chart_config 缺少 chartType"
    print(f"  [OK] 第一轮图表: type={chart1['chartType']}")

    assert session_info["title"] != "新对话", f"会话标题未更新: {session_info['title']}"
    print(f"  [OK] 会话标题已自动更新: {session_info['title']}")


def test_scenario_4(sid: str):
    """场景4: 删除会话 -> 列表更新"""
    print("\n" + "=" * 60)
    print("场景 4: 删除会话")
    print("=" * 60)

    resp = requests.get(f"{BASE}/api/sessions")
    sessions_before = resp.json()
    count_before = len(sessions_before)
    print(f"  删除前会话数: {count_before}")

    resp = requests.delete(f"{BASE}/api/sessions/{sid}")
    assert resp.status_code == 204, f"删除会话失败: {resp.status_code}"
    print(f"  [OK] 删除会话 {sid[:8]}... 成功")

    resp = requests.get(f"{BASE}/api/sessions")
    sessions_after = resp.json()
    count_after = len(sessions_after)
    assert count_after == count_before - 1, f"删除后会话数异常: {count_after}"
    print(f"  [OK] 删除后会话数: {count_after}")

    ids = [s["id"] for s in sessions_after]
    assert sid not in ids, "已删除的会话仍在列表中"
    print(f"  [OK] 已删除会话不在列表中")


if __name__ == "__main__":
    print("Phase 4 端到端验收测试")
    print("后端地址:", BASE)

    resp = requests.get(f"{BASE}/health")
    assert resp.status_code == 200, "后端不可用"
    print("[OK] 后端健康检查通过")

    sid = test_scenario_1()
    test_scenario_2(sid)
    test_scenario_3(sid)
    test_scenario_4(sid)

    print("\n" + "=" * 60)
    print("全部 4 个场景测试通过!")
    print("=" * 60)
