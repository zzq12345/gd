import asyncio
from playwright.async_api import async_playwright

M3U_FILE_PATH = "gdtv_all.m3u"

# 频道列表：名称 -> URL
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

async def fetch_m3u8_for_channel(context, url: str) -> str:
    """在给定浏览器上下文中访问页面，返回第一个 .m3u8 请求的 URL"""
    page = await context.new_page()
    m3u8_link = None

    def intercept_request(request):
        nonlocal m3u8_link
        if ".m3u8" in request.url and m3u8_link is None:
            m3u8_link = request.url

    page.on("request", intercept_request)

    try:
        print(f"正在加载: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        # 等待最多 10 秒，直到捕获到 m3u8 链接
        for _ in range(100):
            if m3u8_link:
                break
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"抓取 {url} 出错: {e}")
    finally:
        await page.close()

    return m3u8_link

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 使用移动端 UA，模拟手机访问
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        )

        results = []  # (频道名, m3u8链接)
        for name, url in CHANNELS:
            m3u8 = await fetch_m3u8_for_channel(context, url)
            if m3u8:
                print(f"✅ {name} 获取成功: {m3u8}")
                results.append((name, m3u8))
            else:
                print(f"❌ {name} 获取失败")

        await browser.close()

    # 生成 M3U 文件
    if results:
        lines = ["#EXTM3U"]
        for name, url in results:
            # tvg-name 和 group-title 可自行调整
            lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="广东台",{name}')
            lines.append(url)
        with open(M3U_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n成功写入 {len(results)} 个频道到 {M3U_FILE_PATH}")
    else:
        print("没有获取到任何频道，文件未生成")

if __name__ == "__main__":
    asyncio.run(main())
