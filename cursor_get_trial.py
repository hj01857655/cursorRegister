from DrissionPage import ChromiumOptions, Chromium
from typing import Optional, Tuple

def get_trial_info(cookies: str) -> Optional[Tuple[str, str]]:
    co = ChromiumOptions().incognito().headless()
    browser = Chromium(co)
    try:
        tab = browser.latest_tab
        tab.get('https://www.cursor.com/settings')
        tab.set.cookies(cookies)
        tab.get("https://www.cursor.com/settings")
        
        usage_ele = tab.ele(
            "css:div.col-span-2 > div > div > div > div > div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > span.font-mono.text-sm\\/\\[0\\.875rem\\]")
        trial_days = tab.ele("css:div > span.ml-1\\.5.opacity-50")
        
        usage = usage_ele.text if usage_ele else "未知"
        days = trial_days.text if trial_days else "未知"
        
        return usage, days
    except Exception as e:
        raise Exception(f"获取试用信息失败: {str(e)}")
    finally:
        browser.quit()
