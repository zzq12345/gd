import asyncio
from playwright.async_api import async_playwright

M3U_FILE_PATH = "gdtv.m3u"

CHANNELS = [
    ("广东珠江", "https://m.gdtv.cn/tvChannelDetail/44"),
    ("广东卫视", "https://m.gdtv.cn/tvChannelDetail/43"),
    ("广东新闻", "https://m.gdtv.cn/tvChannelDetail/45"),
    ("广东民生", "https://m.gdtv.cn/tvChannelDetail/48"),
    ("广东体育", "https://m.gdtv.cn/tvChannelDetail/47"),
    ("大湾区卫视", "https://m.gdtv.cn/tvChannelDetail/51"),
    ("大湾区卫视海外版", "https://m.gdtv.cn/tvChannelDetail/46"),
    ("广东影视", "https://m.gdtv.cn/tvChannelDetail/53"),
    ("4K超高清", "https://m.gdtv.cn/tvChannelDetail/16"),
    ("广东少儿", "https://m.gdtv.cn/tvChannelDetail/54"),
    ("嘉禾卡通", "https://m.gdtv.cn/tvChannelDetail/66"),
    ("岭南戏曲", "https://m.gdtv.cn/tvChannelDetail/15"),
    ("广东移动", "https://m.gdtv.cn/tvChannelDetail/74"),
    ("广东经典剧", "https://m.gdtv.cn/tvChannelDetail/100"),
    ("广东纪录片", "https://m.gdtv.cn/tvChannelDetail/94"),
    ("广东健康", "https://m.gdtv.cn/tvChannelDetail/99"),
    ("广东生活", "https://m.gdtv.cn/tvChannelDetail/102"),
]

# 播放时需要添加的 Referer（固定为网站根域名）
REFERER = "https://m.gdtv.cn"

async def fetch_m3u8_for_channel(context, url: str, retries=3) -> str:
    for attempt in range(1, retries + 1):
        page = await context.new_page()
        m3u8_link = None

        def on_request(request):
            nonlocal m3u8_link
            if m3u8_link is None and ".m3u8" in request.url:
                m3u8_link = request.url

        def on_response(response):
            nonlocal m3u8_link
            if m3u8_link is None and ".m3u8" in response.url:
                m3u8_link = response.url

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            print(f"[尝试 {attempt}] 加载 {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # 轮询 25 秒
            for _ in range(250):
                if m3u8_link:
                    break
                await asyncio.sleep(0.1)

            # 从 video 标签回退
            if not m3u8_link:
                video_src = await page.evaluate('''
                    () => {
                        const video = document.querySelector('video');
                        return video ? video.src : null;
                    }
                ''')
                if video_src and ".m3u8" in video_src:
                    m3u8_link = video_src

            if m3u8_link:
                return m3u8_link

            print(f"  第 {attempt} 次尝试未获取到链接")
        except Exception as e:
            print(f"  第 {attempt} 次尝试出错: {e}")
        finally:
            await page.close()

    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            viewport={"width": 375, "height": 812}
        )

        results = []
        for name, url in CHANNELS:
            m3u8 = await fetch_m3u8_for_channel(context, url)
            if m3u8:
                print(f"✅ {name} -> {m3u8}")
                results.append((name, m3u8))
            else:
                print(f"❌ {name} 获取失败（已重试）")
            await asyncio.sleep(0.5)

        await browser.close()

    if results:
        lines = ["#EXTM3U"]
        # 添加一个全局注释，说明 Referer 设置（可选）
        lines.append('# 注意：若播放时出现403，请确保播放器携带 Referer: https://m.gdtv.cn')
        lines.append('# VLC 用户会自动使用下方 #EXTVLCOPT 指令')
        for name, url in results:
            lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="广东台",{name}')
            # 为 VLC 添加自定义 Referer
            lines.append(f'#EXTVLCOPT:http-referrer={REFERER}')
            lines.append(url)
        with open(M3U_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n成功写入 {len(results)} 个频道到 {M3U_FILE_PATH}")
    else:
        print("没有获取到任何频道，文件未生成")

if __name__ == "__main__":
    asyncio.run(main())
