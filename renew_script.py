import os
import time
from playwright.sync_api import sync_playwright

# --- 配置常量 ---
RENEW_URL = "https://gameserver.gratis/service/465077237570474958/renew"
COOKIE_DOMAIN = ".gameserver.gratis"
COOKIE_NAME = "remember_web_3dc7a913ef5fd4b890ecabe3487085573e16cf82"

def find_and_click_renew_button(page_or_frame):
    """在一个页面或框架中查找并点击续订按钮"""
    # --- 【关键修改】 ---
    # 根据截图，将按钮文本从 "Verlängern" 修改为 "RENEW"
    renew_button_selector = 'button:has-text("RENEW")'
    
    print(f"正在此范围内查找按钮: '{renew_button_selector}'")
    try:
        # 等待按钮在30秒内变为可见
        page_or_frame.wait_for_selector(renew_button_selector, state='visible', timeout=30000)
        print(f"成功找到 'RENEW' 按钮。")
        page_or_frame.click(renew_button_selector)
        print(f"成功点击 'RENEW' 按钮!")
        # 等待几秒钟，确保点击操作被服务器处理
        time.sleep(5)
        return True
    except Exception as e:
        # 捕获超时等错误，意味着在此作用域内未找到按钮
        print(f"在此范围内未找到按钮。详细错误: {str(e).splitlines()[0]}")
        return False

def renew_service():
    """
    自动化登录 gameserver.gratis 并点击续订按钮。
    增加 iframe 搜索和更详细的调试功能。
    """
    cookie_value = os.environ.get('GRATIS_COOKIE')
    user_email = os.environ.get('GRATIS_EMAIL')
    user_password = os.environ.get('GRATIS_PASSWORD')

    if not (cookie_value or (user_email and user_password)):
        print("错误: 缺少登录凭据。")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # --- 登录逻辑 ---
            is_logged_in = False
            if cookie_value:
                print("检测到 Cookie, 正在尝试使用 Cookie 登录...")
                context.add_cookies([{'name': COOKIE_NAME, 'value': cookie_value, 'domain': COOKIE_DOMAIN, 'path': '/'}])
                page.goto(RENEW_URL, wait_until="domcontentloaded", timeout=60000)
                if "login" not in page.url.lower():
                    print("Cookie 登录检查通过 (未跳转到登录页)。")
                    is_logged_in = True
                else:
                    print("Cookie 已失效或无效, 将尝试使用账号密码登录。")

            if not is_logged_in:
                if not (user_email and user_password):
                    print("错误: Cookie 登录失败且未提供备用的账号密码。")
                    return
                print("正在使用账号密码登录...")
                page.goto("https://gameserver.gratis/login", wait_until="domcontentloaded", timeout=60000)
                page.fill('input[name="email"]', user_email)
                page.fill('input[name="password"]', user_password)
                page.click('button[type="submit"]:has-text("Login")')
                page.wait_for_load_state("domcontentloaded", timeout=60000)
                page.goto(RENEW_URL, wait_until="domcontentloaded", timeout=60000)
                if "login" in page.url.lower():
                    print("错误: 账号密码登录失败。")
                    page.screenshot(path="login_failed.png")
                    return

            # --- 截图用于调试 ---
            print("导航到目标页面后，立即截图用于调试...")
            page.screenshot(path="debug_page_view.png")
            print("截图 'debug_page_view.png' 已保存。")

            # --- 新的按钮查找逻辑 ---
            print("\n--- 开始查找续订按钮 ---")
            print("1. 在主页面中查找...")
            if find_and_click_renew_button(page):
                page.screenshot(path="renewal_success_main_page.png")
                return

            print("\n2. 主页面未找到，开始搜索页面中的 iframe...")
            if len(page.frames) > 1:
                for i, frame in enumerate(page.frames[1:], 1):
                    print(f"正在检查第 {i} 个 iframe (URL: {frame.url})...")
                    if find_and_click_renew_button(frame):
                        page.screenshot(path=f"renewal_success_iframe_{i}.png")
                        return
            else:
                print("页面上没有找到任何 iframe。")
            
            print("\n--- 查找结束 ---")
            print("错误: 在主页面和所有 iframe 中都未能找到 'RENEW' 按钮。")
            page.screenshot(path="renew_button_not_found_final.png")

        except Exception as e:
            print(f"执行过程中发生未知错误: {e}")
            page.screenshot(path="general_error.png")
        finally:
            print("脚本执行完毕，关闭浏览器。")
            browser.close()

if __name__ == "__main__":
    renew_service()
