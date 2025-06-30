import os
import time
from playwright.sync_api import sync_playwright

# --- 配置常量 ---
# 目标续订页面的 URL
RENEW_URL = "https://gameserver.gratis/service/465077237570474958/renew"
# 网站的域名，用于设置 Cookie
COOKIE_DOMAIN = ".gameserver.gratis"
# 登录 Cookie 的名称
COOKIE_NAME = "remember_web_3dc7a913ef5fd4b890ecabe3487085573e16cf82"

def renew_service():
    """
    自动化登录 gameserver.gratis 并点击续订按钮。
    优先使用 Cookie 登录，如果失败则回退到邮箱密码登录。
    """
    # --- 从环境变量获取凭据 ---
    # 这是最关键的凭据，只要它有效，就无需账号密码
    cookie_value = os.environ.get('GRATIS_COOKIE')
    # 备用登录方案所需的凭据
    user_email = os.environ.get('GRATIS_EMAIL')
    user_password = os.environ.get('GRATIS_PASSWORD')

    if not (cookie_value or (user_email and user_password)):
        print("错误: 缺少登录凭据。请在 GitHub Secrets 中设置 'GRATIS_COOKIE' 或 ('GRATIS_EMAIL' 和 'GRATIS_PASSWORD')。")
        return False

    with sync_playwright() as p:
        # 启动一个 Chromium 无头浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            is_logged_in = False

            # --- 优先尝试 Cookie 登录 ---
            if cookie_value:
                print("检测到 Cookie, 正在尝试使用 Cookie 登录...")
                # 将从 Secrets 获取的 Cookie 值添加到浏览器上下文中
                context.add_cookies([{
                    'name': COOKIE_NAME,
                    'value': cookie_value,
                    'domain': COOKIE_DOMAIN,
                    'path': '/'
                }])
                
                print(f"Cookie 已设置, 正在导航到目标页面: {RENEW_URL}")
                page.goto(RENEW_URL, wait_until="networkidle", timeout=60000)

                # 检查是否需要登录，如果页面 URL 包含 'login'，说明 Cookie 失效
                if "login" not in page.url.lower():
                    print("Cookie 登录成功!")
                    is_logged_in = True
                else:
                    print("Cookie 已失效或无效, 将尝试使用账号密码登录。")

            # --- 如果未登录, 则使用账号密码登录 ---
            if not is_logged_in:
                if not (user_email and user_password):
                    print("错误: Cookie 登录失败且未提供备用的账号密码。")
                    return False

                print("正在使用账号密码登录...")
                # 通常登录页面和主站是同一个域名
                page.goto("https://gameserver.gratis/login", wait_until="networkidle", timeout=60000)
                
                print("填充登录信息...")
                page.fill('input[name="email"]', user_email)
                page.fill('input[name="password"]', user_password)
                
                print("点击登录按钮...")
                page.click('button[type="submit"]:has-text("Login")')
                
                # 等待页面跳转，可以等待特定元素出现或简单等待网络空闲
                page.wait_for_load_state("networkidle", timeout=60000)

                # 登录后再次导航到目标续订页面
                print(f"登录成功后, 再次导航到: {RENEW_URL}")
                page.goto(RENEW_URL, wait_until="networkidle", timeout=60000)

                if "login" in page.url.lower():
                     print("错误: 账号密码登录失败，请检查凭据是否正确。")
                     page.screenshot(path="login_failed.png")
                     return False
            
            # --- 查找并点击 "Verlängern" 按钮 ---
            renew_button_selector = 'button:has-text("Verlängern")'
            print(f"正在目标页面上查找续订按钮: '{renew_button_selector}'")
            
            try:
                # 等待按钮可见
                page.wait_for_selector(renew_button_selector, state='visible', timeout=30000)
                print("成功找到 'Verlängern' 按钮。")
                page.click(renew_button_selector)
                print("成功点击 'Verlängern' 按钮!")
                # 等待几秒钟，确保点击操作被服务器处理
                time.sleep(5)
                page.screenshot(path="renewal_success.png")
                return True
            except Exception as e:
                print(f"错误: 未能找到或点击 'Verlängern' 按钮。可能是因为已经续订过了，或者页面结构已改变。")
                print(f"详细错误: {e}")
                page.screenshot(path="renew_button_not_found.png")
                return False

        except Exception as e:
            print(f"执行过程中发生未知错误: {e}")
            page.screenshot(path="general_error.png")
            return False
        finally:
            print("脚本执行完毕，关闭浏览器。")
            browser.close()

if __name__ == "__main__":
    renew_service()
