import asyncio
import os
from playwright.async_api import async_playwright
import datetime

TARGET_URL = "https://m.gdtv.cn/tvChannelDetail/44"
M3U_FILE_PATH = "gdtv.m3u"

async def fetch_m3u8_url() -> str:
    m3u8_link = None
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        )
        page = await context.new_page()
        
        async def intercept_request(request):
            nonlocal m3u8_link
            if ".m3u8" in request.url:
                m3u8_link = request.url

        page.on("request", intercept_request)
        
        try:
            print(f"[{datetime.datetime.now()}] 正在加載目標頁面...")
            await page.goto(TARGET_URL, wait_until="domcontentloaded")
            for _ in range(100):
                if m3u8_link:
                    break
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"抓取錯誤: {e}")
        finally:
            await browser.close()
            
    return m3u8_link

async def main():
    print("開始抓取 GDTV 源...")
    stream_url = await fetch_m3u8_url()
    
    if stream_url:
        print(f"成功獲取: {stream_url}")
        
        # 組合 M3U 播放清單內容
        m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-name="廣東衛視" group-title="廣東台",廣東衛視
{stream_url}
"""
        # 將結果寫入 M3U 檔案
        with open(M3U_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(m3u_content)
        print(f"已成功寫入 {M3U_FILE_PATH}")
    else:
        print("抓取失敗，未能找到 m3u8 連結。")

if __name__ == "__main__":
    asyncio.run(main())
