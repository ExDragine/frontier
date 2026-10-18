import asyncio
from pathlib import Path

from utils.http_client import AsyncClient, HTTPError

current_dir = Path(__file__).resolve().parent

temp_dir = current_dir.parents[2] / "temp"

file_path = temp_dir / "earth_now_test.jpg"


async def fetch_earth_image():
    url = "https://www.storm-chasers.cn/wp-content/uploads/satimgs/Composite_TVIS_FDLK.jpg"
    content = None

    async with AsyncClient(timeout=30) as client:
        for attempt in range(3):
            try:
                print(f"[尝试第 {attempt + 1} 次] 正在获取图片...")
                response = await client.get(url)
                response.raise_for_status()
                content = await response.aread()

                content_length = response.headers.get("Content-Length")
                if content_length and len(content) != int(content_length):
                    print(f"⚠️ 警告：下载大小 {len(content)} 与 Content-Length {content_length} 不符，重试中...")
                    content = None
                    continue

                print(f"✅ 下载完成，大小: {len(content)} 字节")
                break

            except HTTPError as e:
                print(f"❌ 获取图片失败: {e}")
                await asyncio.sleep(1)
                continue

    if not content:
        print("❌ 下载失败：所有重试均失败")
        return None

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)
    print(f"✅ 文件已保存到: {file_path}")

    return content


if __name__ == "__main__":
    asyncio.run(fetch_earth_image())
