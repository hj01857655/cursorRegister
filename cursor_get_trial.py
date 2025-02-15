from DrissionPage import ChromiumOptions, Chromium
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class TrialInfo:
    usage: str
    days: str

def get_trial_info(cookies: str) -> TrialInfo:
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
        
        if not usage_ele or not trial_days:
            raise ValueError("无法获取试用信息，页面结构可能已更改")
        
        return TrialInfo(
            usage=usage_ele.text or "未知",
            days=trial_days.text or "未知"
        )
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"获取试用信息失败: {str(e)}")
    finally:
        browser.quit()
