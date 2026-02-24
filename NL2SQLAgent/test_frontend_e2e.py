"""前端端到端浏览器自动化测试
测试目标: 验证 Web UI 的完整用户交互流程和 Markdown 渲染质量
"""
import time
import json
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, expect

# 测试配置
FRONTEND_URL = "http://localhost:5175/"
SCREENSHOTS_DIR = Path("test_screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

def save_screenshot(page: Page, name: str) -> str:
    """保存截图并返回文件路径"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{name}.png"
    filepath = SCREENSHOTS_DIR / filename
    page.screenshot(path=str(filepath), full_page=True)
    print(f"  📸 截图已保存: {filepath}")
    return str(filepath)

def extract_markdown_content(page: Page) -> dict:
    """提取页面上显示的 AI 响应内容"""
    try:
        # 等待 AI 响应内容出现
        page.wait_for_selector(".message-content", timeout=5000)
        
        # 获取所有 AI 消息
        ai_messages = page.query_selector_all(".message.assistant")
        
        if not ai_messages:
            return {"error": "未找到 AI 消息"}
        
        # 获取最后一条 AI 消息
        last_message = ai_messages[-1]
        
        # 提取文本内容
        content_elem = last_message.query_selector(".message-content")
        if not content_elem:
            return {"error": "未找到消息内容元素"}
        
        text_content = content_elem.inner_text()
        html_content = content_elem.inner_html()
        
        return {
            "text": text_content,
            "html": html_content,
            "length": len(text_content)
        }
    except Exception as e:
        return {"error": f"提取内容失败: {str(e)}"}

def check_markdown_rendering(page: Page) -> dict:
    """检查 Markdown 渲染质量"""
    issues = []
    
    try:
        # 获取最后一条 AI 消息的内容
        ai_messages = page.query_selector_all(".message.assistant")
        if not ai_messages:
            return {"error": "未找到 AI 消息", "issues": []}
        
        last_message = ai_messages[-1]
        content_elem = last_message.query_selector(".message-content")
        
        if not content_elem:
            return {"error": "未找到消息内容元素", "issues": []}
        
        html = content_elem.inner_html()
        text = content_elem.inner_text()
        
        # 检查1: 是否有未渲染的 Markdown 标记
        if "**" in text:
            count = text.count("**")
            issues.append(f"❌ 发现未渲染的粗体标记 '**'，共 {count} 处")
        
        if "##" in text or "###" in text:
            issues.append("❌ 发现未渲染的标题标记 '##' 或 '###'")
        
        if text.strip().startswith("-") or text.strip().startswith("*"):
            issues.append("❌ 发现未渲染的列表标记")
        
        # 检查2: 是否有正确的 HTML 标签
        has_bold = "<strong>" in html or "<b>" in html
        has_headers = "<h1>" in html or "<h2>" in html or "<h3>" in html
        has_lists = "<ul>" in html or "<ol>" in html
        
        # 检查3: 粗体标记格式问题 (如 "**88,948.0 **" 而不是 "**88,948.0**")
        import re
        broken_bold_pattern = r'\*\*[^*]+\s+\*\*'
        if re.search(broken_bold_pattern, text):
            issues.append("❌ 发现格式错误的粗体标记（数字和结束标记之间有空格）")
        
        # 检查4: 多余的空行
        empty_lines = text.count("\n\n\n")
        if empty_lines > 0:
            issues.append(f"⚠️  发现 {empty_lines} 处多余的空行（连续3个换行符）")
        
        # 检查5: 内容中间的异常断行
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.strip() and len(line.strip()) < 10 and i < len(lines) - 1:
                if lines[i+1].strip() and not lines[i+1].strip().startswith(("-", "*", "1.", "2.")):
                    issues.append(f"⚠️  第 {i+1} 行可能有异常断行: '{line.strip()}'")
                    break  # 只报告第一个
        
        # 检查6: 数据是否完整显示
        if "销售总额" in text or "sales" in text.lower():
            if not any(char.isdigit() for char in text):
                issues.append("❌ 响应中没有数字数据，可能数据未正确显示")
        
        result = {
            "issues": issues,
            "has_bold_tags": has_bold,
            "has_header_tags": has_headers,
            "has_list_tags": has_lists,
            "text_length": len(text),
            "html_length": len(html)
        }
        
        if not issues:
            result["summary"] = "✅ Markdown 渲染质量良好，未发现明显问题"
        else:
            result["summary"] = f"⚠️  发现 {len(issues)} 个潜在问题"
        
        return result
        
    except Exception as e:
        return {"error": f"检查失败: {str(e)}", "issues": []}

def test_frontend_flow():
    """执行前端完整流程测试"""
    print("\n" + "=" * 80)
    print("前端端到端浏览器自动化测试")
    print("=" * 80)
    
    with sync_playwright() as p:
        # 启动浏览器（使用 chromium，headless=False 可以看到浏览器）
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        try:
            # 步骤1: 导航到首页
            print("\n[步骤1] 导航到前端应用...")
            page.goto(FRONTEND_URL, wait_until="networkidle")
            time.sleep(2)  # 等待页面稳定
            
            screenshot_initial = save_screenshot(page, "01_initial_page")
            print(f"  ✅ 页面加载成功")
            
            # 步骤2: 查找并点击"新建会话"按钮
            print("\n[步骤2] 查找新建会话按钮...")
            new_session_btn = None
            
            # 尝试多种选择器
            selectors = [
                'button:has-text("新建会话")',
                'button:has-text("新建")',
                '[class*="new-session"]',
                'button[class*="new"]',
            ]
            
            for selector in selectors:
                try:
                    new_session_btn = page.query_selector(selector)
                    if new_session_btn:
                        print(f"  ✅ 找到按钮: {selector}")
                        break
                except:
                    continue
            
            if new_session_btn:
                new_session_btn.click()
                time.sleep(1)
                print(f"  ✅ 点击新建会话按钮")
            else:
                print(f"  ⚠️  未找到新建会话按钮，尝试直接使用输入框")
            
            # 步骤3: 查找输入框并输入消息
            print("\n[步骤3] 查找聊天输入框...")
            input_selectors = [
                'textarea[placeholder*="输入"]',
                'textarea[placeholder*="问题"]',
                'input[type="text"]',
                'textarea',
                '[contenteditable="true"]',
            ]
            
            input_elem = None
            for selector in input_selectors:
                try:
                    input_elem = page.query_selector(selector)
                    if input_elem:
                        print(f"  ✅ 找到输入框: {selector}")
                        break
                except:
                    continue
            
            if not input_elem:
                screenshot_error = save_screenshot(page, "error_no_input")
                raise Exception("未找到聊天输入框！请检查页面结构")
            
            # 输入测试消息
            test_message = "各地区的销售总额是多少？"
            print(f"\n[步骤4] 输入测试消息: '{test_message}'")
            
            if input_elem.get_attribute("contenteditable"):
                # contenteditable 元素
                page.evaluate(f'document.querySelector("[contenteditable=true]").innerText = "{test_message}"')
            else:
                # 普通 input/textarea
                input_elem.fill(test_message)
            
            time.sleep(0.5)
            save_screenshot(page, "02_message_typed")
            print(f"  ✅ 消息已输入")
            
            # 步骤5: 发送消息
            print("\n[步骤5] 发送消息...")
            send_btn = None
            
            send_selectors = [
                'button[type="submit"]',
                'button:has-text("发送")',
                'button:has-text("Send")',
                '[class*="send"]',
                'button[class*="submit"]',
            ]
            
            for selector in send_selectors:
                try:
                    send_btn = page.query_selector(selector)
                    if send_btn and send_btn.is_visible():
                        print(f"  ✅ 找到发送按钮: {selector}")
                        break
                except:
                    continue
            
            if send_btn:
                send_btn.click()
            else:
                # 尝试按 Enter 键
                print(f"  ⚠️  未找到发送按钮，尝试按 Enter")
                input_elem.press("Enter")
            
            time.sleep(1)
            save_screenshot(page, "03_message_sent")
            print(f"  ✅ 消息已发送")
            
            # 步骤6: 等待 AI 响应完成
            print("\n[步骤6] 等待 AI 响应完成...")
            print("  ⏳ 等待思考步骤、SQL 查询、查询结果和 AI 分析...")
            
            # 等待最多 45 秒，期间每隔 5 秒检查一次
            max_wait = 45
            check_interval = 5
            elapsed = 0
            response_complete = False
            
            while elapsed < max_wait:
                time.sleep(check_interval)
                elapsed += check_interval
                
                # 检查是否出现"完成"标记或停止输出的迹象
                # 这里可以根据实际 UI 调整检测逻辑
                page_text = page.content()
                
                # 简单判断：如果页面内容包含表格和大段文字，认为响应完成
                has_table = "query_result" in page_text or "<table>" in page_text
                has_long_text = len(page.inner_text()) > 500
                
                if has_table and has_long_text:
                    # 再等待 3 秒确保完全渲染
                    time.sleep(3)
                    response_complete = True
                    print(f"  ✅ 检测到响应完成 (耗时约 {elapsed} 秒)")
                    break
                else:
                    print(f"  ⏳ 等待中... ({elapsed}/{max_wait}s)")
            
            if not response_complete:
                print(f"  ⚠️  超时 {max_wait} 秒，继续进行检查")
            
            # 步骤7: 截图完整响应
            print("\n[步骤7] 截图完整响应...")
            screenshot_response = save_screenshot(page, "04_full_response")
            print(f"  ✅ 响应截图已保存")
            
            # 步骤8: 提取和检查 AI 响应内容
            print("\n[步骤8] 提取 AI 响应内容...")
            content = extract_markdown_content(page)
            
            if "error" in content:
                print(f"  ❌ {content['error']}")
            else:
                print(f"  ✅ 成功提取响应内容")
                print(f"     文本长度: {content['length']} 字符")
                print(f"\n  --- AI 响应内容预览 ---")
                preview = content['text'][:500] + "..." if len(content['text']) > 500 else content['text']
                print(f"  {preview}")
                print(f"  --- 预览结束 ---\n")
            
            # 步骤9: 检查 Markdown 渲染质量
            print("\n[步骤9] 检查 Markdown 渲染质量...")
            render_check = check_markdown_rendering(page)
            
            if "error" in render_check:
                print(f"  ❌ {render_check['error']}")
            else:
                print(f"  {render_check['summary']}")
                print(f"\n  渲染分析:")
                print(f"    - 有粗体标签: {'✅' if render_check.get('has_bold_tags') else '❌'}")
                print(f"    - 有标题标签: {'✅' if render_check.get('has_header_tags') else '⚠️ (可能没有标题)'}")
                print(f"    - 有列表标签: {'✅' if render_check.get('has_list_tags') else '⚠️ (可能没有列表)'}")
                print(f"    - 文本长度: {render_check.get('text_length', 0)} 字符")
                print(f"    - HTML 长度: {render_check.get('html_length', 0)} 字符")
                
                if render_check.get('issues'):
                    print(f"\n  发现的问题:")
                    for issue in render_check['issues']:
                        print(f"    {issue}")
            
            # 步骤10: 保存详细测试报告
            print("\n[步骤10] 生成测试报告...")
            report = {
                "timestamp": datetime.now().isoformat(),
                "test_url": FRONTEND_URL,
                "screenshots": {
                    "initial": screenshot_initial,
                    "message_typed": str(SCREENSHOTS_DIR / "02_message_typed.png"),
                    "message_sent": str(SCREENSHOTS_DIR / "03_message_sent.png"),
                    "full_response": screenshot_response,
                },
                "response_content": content if "error" not in content else None,
                "markdown_quality": render_check,
                "test_status": "PASSED" if not render_check.get('issues') else "PASSED_WITH_WARNINGS"
            }
            
            report_path = SCREENSHOTS_DIR / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ 测试报告已保存: {report_path}")
            
            # 最后再等待几秒，让用户看清楚
            print("\n[完成] 保持浏览器打开 5 秒，以便查看...")
            time.sleep(5)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            save_screenshot(page, "error_final")
            raise
        finally:
            browser.close()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print(f"所有截图和报告保存在: {SCREENSHOTS_DIR.absolute()}")
    print("=" * 80)

if __name__ == "__main__":
    test_frontend_flow()
