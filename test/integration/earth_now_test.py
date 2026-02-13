import asyncio
from pathlib import Path

import httpx

# 当前文件所在目录（绝对路径）
current_dir = Path(__file__).resolve().parent

# 项目根目录下的 temp 文件夹
temp_dir = current_dir.parents[2] / "temp"

# 如果 temp 文件夹不存在就创建
temp_dir.mkdir(parents=True, exist_ok=True)

# 拼出目标文件路径
file_path = temp_dir / "earth_now_test.jpg"


async def fetch_earth_image():
    url = "https://www.storm-chasers.cn/wp-content/uploads/satimgs/Composite_TVIS_FDLK.jpg"
    content = None

    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(3):
            try:
                print(f"[尝试第 {attempt + 1} 次] 正在获取图片...")
                response = await client.get(url)
                response.raise_for_status()
                # 确保完整读取响应体
                content = await response.aread()

                # 检查 Content-Length 一致性
                content_length = response.headers.get("Content-Length")
                if content_length and len(content) != int(content_length):
                    print(f"⚠️ 警告：下载大小 {len(content)} 与 Content-Length {content_length} 不符，重试中...")
                    content = None
                    continue

                print(f"✅ 下载完成，大小: {len(content)} 字节")
                break

            except httpx.HTTPError as e:
                print(f"❌ 获取图片失败: {e}")
                await asyncio.sleep(1)  # 间隔重试
                continue

    if not content:
        print("❌ 下载失败：所有重试均失败")
        return None

    # 保存文件以验证完整性
    with open(file_path, "wb", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 文件已保存到: {file_path}")

    return content


if __name__ == "__main__":
    asyncio.run(fetch_earth_image())
