import time
from typing import Any

from langchain.tools import tool
from nonebot import logger, require
from playwright.async_api import async_playwright

from utils.staged_artifacts import stage_artifact_response

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import UniMessage  # noqa: E402


@tool(response_format="content_and_artifact")
async def get_static_china_radar(area: str) -> tuple[Any, UniMessage | None]:
    """获取静态中国雷达图

    Args:
        area: 查询的地区名称，为具体的城市或者地区名称，例如：北京、上海、广东、全国、华北等

    Returns:
        tuple[str, Optional[MessageSegment]]: (描述信息, 雷达图消息段)
    """
    start_time = time.time()
    logger.info(f"🛠️ 调用工具: get_static_china_radar, 参数: area={area}")

    try:
        result = await china_static_radar(area)
        end_time = time.time()

        if result:
            logger.info(f"✅ 工具执行成功: get_static_china_radar (耗时: {end_time - start_time:.2f}s)")
            return stage_artifact_response(f"成功获取{area}地区的雷达图", UniMessage.image(url=result))
        else:
            logger.info(f"❌ 工具执行失败: get_static_china_radar - 地区不存在 (耗时: {end_time - start_time:.2f}s)")
            return f"抱歉，找不到{area}地区的雷达图数据", None
    except Exception as e:
        end_time = time.time()
        logger.error(f"💥 工具执行异常: get_static_china_radar - {str(e)} (耗时: {end_time - start_time:.2f}s)")
        return f"获取{area}雷达图失败: {str(e)}", None


async def china_static_radar(area: str):
    if area not in areas:
        return None

    url = f"http://www.nmc.cn/publish/{areas[area]}"
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle")
            # 等待页面里目标元素出现
            try:
                await page.wait_for_selector("div.col-xs-12.time", timeout=7000)
            except Exception as e:
                # 如果超时则继续尝试获取（可能页面以不同方式渲染）
                logger.error(e)

            elements = await page.query_selector_all("div.col-xs-12.time")
            for el in elements:
                img_attr = await el.get_attribute("data-img")
                if img_attr:
                    await browser.close()
                    return img_attr

            await browser.close()
            return None
    except Exception as exc:
        logger.error(f"china_static_radar playwright error: {exc}")
        return None


areas = {
    "全国": "radar/chinaall.html",
    "华北": "radar/huabei.html",
    "东北": "radar/dongbei.html",
    "华东": "radar/huadong.html",
    "华中": "radar/huazhong.html",
    "华南": "radar/huanan.html",
    "西南": "radar/xinan.html",
    "西北": "radar/xibei.html",
    #
    "北京": "radar/bei-jing/da-xing.htm",
    "大兴": "radar/bei-jing/da-xing.htm",
    "海坨山": "tianqishikuang/leidatu/danzhanleida/beijing/haituoshan/index.html",
    #
    "天津": "radar/tian-jin/tian-jin.htm",
    "塘沽": "radar/tian-jin/tian-jin.htm",
    "宝坻": "tianqishikuang/leidatu/danzhanleida/tianjin/baodi/index.html",
    #
    "河北": "radar/he-bei/shi-jia-zhuang.htm",
    "石家庄": "radar/he-bei/shi-jia-zhuang.htm",
    "张家口": "radar/he-bei/zhang-jia-kou.htm",
    "邯郸": "radar/he-bei/han-dan.htm",
    "沧州": "radar/he-bei/cang-zhou.htm",
    "秦皇岛": "radar/he-bei/qin-huang-dao.htm",
    "承德": "radar/he-beig/cheng-de.htm",
    #
    "山西": "radar/shan-xi/tai-yuan.htm",
    "太原": "radar/shan-xi/tai-yuan.htm",
    "临汾": "radar/shan-xi/lin-fen.htm",
    "大同": "radar/shan-xi/da-tong.htm",
    "吕梁": "radar/shan-xi/lv-liang.htm",
    "长治": "radar/shan-xi/chang-zhi.htm",
    "五寨": "tianqishikuang/leidatu/danzhanleida/shanxi/wuzhai/index.html",
    #
    "内蒙古": "radar/nei-meng/e-er-duo-si.htm",
    "鄂尔多斯": "radar/nei-meng/e-er-duo-si.htm",
    "呼和浩特": "radar/nei-meng/hu-he-hao-te.htm",
    "赤峰": "radar/nei-meng/chi-feng.htm",
    "海拉尔": "radar/nei-meng/hai-la-er.htm",
    "通辽": "radar/nei-meng/tong-liao.htm",
    "临河": "radar/nei-meng/lin-he.htm",
    "霍林郭勒": "radar/nei-meng/huo-lin-guo-le.htm",
    "满洲里": "radar/nei-meng/man-zhou-li.htm",
    "集宁": "radar/nei-meng/jininghtml",
    "锡林浩特": "radar/nei-meng/xilinhaote.html",
    "阿尔山": "radar/nei-meng/aershan.html",
    #
    "辽宁": "radar/liao-ning/da-lian.htm",
    "大连": "radar/liao-ning/da-lian.htm",
    "朝阳": "radar/liao-ning/chao-yang.htm",
    "营口": "radar/liao-ning/ying-kou.htm",
    "沈阳": "radar/liao-ning/shen-yang.htm",
    #
    "吉林": "tianqishikuang/leidatu/danzhanleida/jilin/jilin/index.html",
    "长春": "radar/ji-lin/chang-chun.htm",
    "白城": "radar/ji-lin/bai-cheng.htm",
    "白山": "radar/ji-lin/bai-shan.htm",
    "辽源": "radar/ji-lin/liao-yuan.htm",
    "延吉": "radar/ji-lin/yan-ji.htm",
    "松原": "tianqishikuang/leidatu/danzhanleida/jilin/songyuan/index.html",
    #
    "黑龙江": "radar/hei-long-jiang/ha-er-bin.htm",
    "哈尔滨": "radar/hei-long-jiang/ha-er-bin.htm",
    "齐齐哈尔": "radar/hei-long-jiang/qi-qi-ha-er.htm",
    "佳木斯": "radar/hei-long-jiang/jia-mu-si.htm",
    "加格达奇": "radar/hei-long-jiang/jia-ge-da-qi.htm",
    "黑河": "radar/hei-long-jiang/hei-he.htm",
    "伊春": "radar/hei-long-jiang/yi-chun.htm",
    "牡丹江": "radar/hei-long-jiang/mu-dan-jiang.htm",
    "建三江": "radar/hei-long-jiang/jian-san-jiang.htm",
    "九三": "radar/hei-long-jiang/jiu-san.htm",
    "黑瞎子岛": "radar/hei-long-jiang/hei-xia-zi-dao.htm",
    #
    "上海": "radar/shang-hai/qing-pu.htm",
    "青浦": "radar/shang-hai/qing-pu.htm",
    "南汇": "radar/shang-hai/nan-hui.htm",
    #
    "江苏": "radar/jiang-su/nan-jing.htm",
    "南京": "radar/jiang-su/nan-jing.htm",
    "南通": "radar/jiang-su/nan-tong.htm",
    "盐城": "radar/jiang-su/yan-cheng.htm",
    "徐州": "radar/jiang-su/xu-zhou.htm",
    "连云港": "radar/jiang-su/lian-yun-gang.htm",
    "常州": "radar/jiang-su/chang-zhou.htm",
    "淮安": "radar/jiang-su/huai-an.htm",
    "泰州": "radar/jiang-su/tai-zhou.htm",
    "宿迁": "tianqishikuang/leidatu/danzhanleida/jiangsu/suqian/index.html",
    #
    "浙江": "radar/zhe-jiang/hang-zhou.htm",
    "杭州": "radar/zhe-jiang/hang-zhou.htm",
    "宁波": "radar/zhe-jiang/ning-bo.htm",
    "温州": "radar/zhe-jiang/wen-zhou.htm",
    "舟山": "radar/zhe-jiang/zhou-shan.htm",
    "金华": "radar/zhe-jiang/jin-hua.htm",
    "衢州": "radar/zhe-jiang/qu-zhou.htm",
    "台州": "radar/zhe-jiang/tai-zhou.htm",
    "湖州": "radar/zhe-jiang/hu-zhou.htm",
    "丽水": "radar/zhe-jiang/li-shui.htm",
    "嵊泗": "radar/zhe-jiang/cheng-si.htm",
    #
    "安徽": "radar/an-hui/he-fei.htm",
    "合肥": "radar/an-hui/he-fei.htm",
    "马鞍山": "radar/an-hui/ma-an-shan.htm",
    "阜阳": "radar/an-hui/fu-yang.htm",
    "蚌埠": "radar/an-hui/beng-bu.htm",
    "安庆": "radar/an-hui/an-qing.htm",
    "黄山": "radar/an-hui/huang-shan.htm",
    "铜陵": "radar/an-hui/tong-ling.htm",
    "宣城": "radar/an-hui/xuancheng.html",
    #
    "福建": "radar/fu-jian/fu-zhou.htm",
    "福州": "radar/fu-jian/fu-zhou.htm",
    "泉州": "radar/fu-jian/quan-zhou.htm",
    "厦门": "radar/fu-jian/xia-men.htm",
    "建阳": "radar/fu-jian/jian-yang.htm",
    "三明": "radar/fu-jian/san-ming.htm",
    "龙岩": "radar/fu-jian/long-yan.htm",
    "漳州": "radar/fu-jian/zhang-zhou.htm",
    "宁德": "radar/fu-jian/ning-de.htm",
    #
    "江西": "radar/jiang-xi/nan-chang.htm",
    "南昌": "radar/jiang-xi/nan-chang.htm",
    "赣州": "radar/jiang-xi/gan-zhou.htm",
    "九江": "radar/jiang-xi/jiu-jiang.htm",
    "上饶": "radar/jiang-xi/shang-rao.htm",
    "宜春": "radar/jiang-xi/yi-chun.htm",
    "抚州": "radar/jiang-xi/fu-zhou.htm",
    "景德镇": "radar/jiang-xi/jing-de-zhen.htm",
    "吉安": "radar/jiang-xi/ji-an.htm",
    #
    "山东": "radar/shan-dong/ji-nan.htm",
    "济南": "radar/shan-dong/ji-nan.htm",
    "烟台": "radar/shan-dong/yan-tai.htm",
    "临沂": "radar/shan-dong/lin-yi.htm",
    "滨州": "radar/shan-dong/bin-zhou.htm",
    "青岛": "radar/shan-dong/qing-dao.htm",
    "泰山": "radar/shan-dong/tai-shan.htm",
    "荣成": "radar/shan-dong/rong-cheng.htm",
    "潍坊": "radar/shan-dong/wei-fang.htm",
    "济宁": "radar/shan-dong/ji-ning.html",
    #
    "河南": "radar/he-nan/zheng-zhou.htm",
    "郑州": "radar/he-nan/zheng-zhou.htm",
    "商丘": "radar/he-nan/shang-qiu.htm",
    "南阳": "radar/he-nan/nan-yang.htm",
    "洛阳": "radar/he-nan/luo-yang.htm",
    "濮阳": "radar/he-nan/pu-yang.htm",
    "驻马店": "radar/he-nan/zhu-ma-dian.htm",
    "信阳": "radar/henan/xinyang.html",
    "平顶山": "radar/he-nan/ping-ding-shan.htm",
    "三门峡": "radar/he-nan/san-men-xia.htm",
    #
    "湖北": "radar/hu-bei/wu-han.htm",
    "武汉": "radar/hu-bei/wu-han.htm",
    "宜昌": "radar/hu-bei/yi-chang.htm",
    "恩施": "radar/hu-bei/en-shi.htm",
    "十堰": "radar/hu-bei/shi-yan.htm",
    "荆州": "radar/hu-bei/jing-zhou.htm",
    "随州": "radar/hu-bei/sui-zhou.htm",
    "神农架": "radar/hu-bei/shen-nong-jia.htm",
    "襄阳": "radar/hu-bei/xiang-yang.htm",
    "麻城": "radar/hu-bei/ma-cheng.htm",
    #
    "湖南": "radar/hu-nan/chang-sha.htm",
    "长沙": "radar/hu-nan/chang-sha.htm",
    "郴州": "radar/hu-nan/chen-zhou.htm",
    "常德": "radar/hu-nan/chang-de.htm",
    "永州": "radar/hu-nan/yong-zhou.htm",
    "岳阳": "radar/hu-nan/yue-yang.htm",
    "邵阳": "radar/hu-nan/shao-yang.htm",
    "怀化": "radar/hu-nan/huai-hua.htm",
    "张家界": "radar/hu-nan/zhang-jia-jie.htm",
    "湘潭": "radar/hunan/xiangtan.html",
    "衡阳": "radar/hunan/hengyang.html",
    "益阳": "tianqishikuang/leidatu/danzhanleida/hunan/yiyang/index.html",
    "湘西": "tianqishikuang/leidatu/danzhanleida/hunan/xiangxi/index.html",
    #
    "广东": "radar/guang-dong/guang-zhou.htm",
    "广州": "radar/guang-dong/guang-zhou.htm",
    "韶关": "radar/guang-dong/shao-guan.htm",
    "梅州": "radar/guang-dong/mei-zhou.htm",
    "阳江": "radar/guang-dong/yang-jiang.htm",
    "汕头": "radar/guang-dong/shan-tou.htm",
    "深圳": "radar/guang-dong/shen-zhen.htm",
    "湛江": "radar/guang-dong/zhan-jiang.htm",
    "河源": "radar/guang-dong/he-yuan.htm",
    "汕尾": "radar/guang-dong/shan-wei.htm",
    "肇庆": "radar/guang-dong/zhao-qing.htm",
    "连州": "radar/guang-dong/lian-zhou.htm",
    "上川岛": "/tianqishikuang/leidatu/danzhanleida/guangdong/shangchuandao/index.html",
    #
    "广西": "radar/guang-xi/gui-lin.htm",
    "桂林": "radar/guang-xi/gui-lin.htm",
    "柳州": "radar/guang-xi/liu-zhou.htm",
    "南宁": "radar/guang-xi/nan-ning.htm",
    "百色": "radar/guang-xi/bai-se.htm",
    "河池": "radar/guang-xi/he-chi.htm",
    "北海": "radar/guang-xi/bei-hai.htm",
    "梧州": "radar/guang-xi/wu-zhou.htm",
    "玉林": "radar/guang-xi/yu-lin.htm",
    "防城港": "radar/guang-xi/fang-cheng-gang.htm",
    "崇左": "radar/guang-xi/chong-zuo.html",
    #
    "海南": "radar/hai-nan/hai-kou.htm",
    "海口": "radar/hai-nan/hai-kou.htm",
    "三亚": "radar/hai-nan/san-ya.htm",
    "三沙": "radar/hai-nan/san-sha.htm",
    "东方": "tianqishikuang/leidatu/danzhanleida/hainan/dongfang/index.html",
    "万宁": "tianqishikuang/leidatu/danzhanleida/hainan/wanning/index.html",
    #
    "重庆": "radar/chong-qing/chong-qing.htm",
    "万州": "radar/chong-qing/wan-zhou.htm",
    "黔江": "radar/chong-qing/qian-jiang.htm",
    "永川": "radar/chong-qing/yong-chuan.htm",
    "涪陵": "radar/chong-qing/pei-ling.htm",
    #
    "成都": "radar/si-chuan/cheng-du.htm",
    "四川": "radar/si-chuan/cheng-du.htm",
    "宜宾": "radar/si-chuan/yi-bin.htm",
    "绵阳": "radar/si-chuan/mian-yang.htm",
    "南充": "radar/si-chuan/nan-chong.htm",
    "西昌": "radar/si-chuan/xi-chang.htm",
    "广元": "radar/si-chuan/guang-yuan.htm",
    "达州": "radar/si-chuan/da-zhou.htm",
    "乐山": "radar/si-chuan/le-shan.htm",
    "雅安": "radar/si-chuan/ya-an.htm",
    "巴中": "tianqishikuang/leidatu/danzhanleida/sichuan/bazhong/index.html",
    "红原": "tianqishikuang/leidatu/danzhanleida/sichuan/hongyuan/index.html",
    "康定": "tianqishikuang/leidatu/danzhanleida/sichuan/kangding/index.html",
    #
    "贵州": "radar/gui-zhou/gui-yang.htm",
    "贵阳": "radar/gui-zhou/gui-yang.htm",
    "遵义": "radar/gui-zhou/zun-yi.htm",
    "铜仁": "radar/gui-zhou/tong-ren.htm",
    "兴义": "radar/gui-zhou/xing-yi.htm",
    "毕节": "radar/gui-zhou/bi-jie.htm",
    "黔东南": "radar/gui-zhou/qian-dong-nan.htm",
    "都匀": "radar/gui-zhou/dou-yun.htm",
    "六盘水": "radar/gui-zhou/liu-pan-shui.htm",
    "榕江": "tianqishikuang/leidatu/danzhanleida/guizhou/rong-jiang.html",
    "习水": "tianqishikuang/leidatu/danzhanleida/guizhou/xi-shui.html",
    "务川": "tianqishikuang/leidatu/danzhanleida/guizhou/wu-chuan.html",
    #
    "云南": "radar/yun-nan/kun-ming.htm",
    "昆明": "radar/yun-nan/kun-ming.htm",
    "德宏": "radar/yun-nan/de-hong.htm",
    "昭通": "radar/yun-nan/zhao-tong.htm",
    "文山": "radar/yun-nan/wen-shan.htm",
    "思茅": "radar/yun-nan/si-mao.htm",
    "丽江": "radar/yun-nan/li-jiang.htm",
    "大理": "radar/yun-nan/da-li.htm",
    "曲靖": "tianqishikuang/leidatu/danzhanleida/yunnan/qujing/index.html",
    "红河哈尼族彝族自治州": "tianqishikuang/leidatu/danzhanleida/yunnan/honghehanizuyizuzizhizhou/index.html",
    "西双版纳傣族自治州": "tianqishikuang/leidatu/danzhanleida/yunnan/xishuangbannadaizuzizhizhou/index.html",
    "临沧": "tianqishikuang/leidatu/danzhanleida/yunnan/lincang/index.html",
    "怒江": "tianqishikuang/leidatu/danzhanleida/yunnan/nujiang/index.html",
    #
    "西藏": "radar/xi-cang/la-sa.htm",
    "拉萨": "radar/xi-cang/la-sa.htm",
    "林芝": "radar/xi-cang/lin-zhi.htm",
    "日喀则": "radar/xi-cang/ri-ka-ze.htm",
    "那曲": "radar/xi-cang/na-qu.htm",
    #
    "陕西": "radar/shan-xi/xi-an.htm",
    "西安": "radar/shan-xi/xi-an.htm",
    "榆林": "radar/shan-xi/yu-lin.htm",
    "安康": "radar/shan-xi/an-kang.htm",
    "延安": "radar/shan-xi/yan-an.htm",
    "汉中": "radar/shan-xi/han-zhong.htm",
    "宝鸡": "radar/shan-xi/bao-ji.htm",
    "商洛": "radar/shan-xi/shang-luo.htm",
    #
    "甘肃": "radar/gan-su/lan-zhou.htm",
    "兰州": "radar/gan-su/lan-zhou.htm",
    "西峰": "radar/gan-su/xi-feng.htm",
    "张掖": "radar/gan-su/zhang-ye.htm",
    "天水": "radar/gan-su/tian-shui.htm",
    "嘉峪关": "radar/gan-su/jia-yu-guan.htm",
    "甘南": "radar/gan-su/gan-nan.htm",
    "陇南": "tianqishikuang/leidatu/danzhanleida/gansu/longnan/index.html",
    #
    "青海": "radar/qing-hai/xi-ning.htm",
    "西宁": "radar/qing-hai/xi-ning.htm",
    "海北": "radar/qing-hai/hai-bei.htm",
    "海南州": "tianqishikuang/leidatu/danzhanleida/qinghai/hainan/index.html",
    "玉树藏族自治州": "tianqishikuang/leidatu/danzhanleida/qinghai/yushucangzuzizhizhou/index.html",
    "黄南藏族自治州": "tianqishikuang/leidatu/danzhanleida/qinghai/huangnancangzuzizhizhou/index.html",
    #
    "宁夏": "radar/ning-xia/yin-chuan.htm",
    "银川": "radar/ning-xia/yin-chuan.htm",
    "固原": "radar/ning-xia/gu-yuan.htm",
    "吴忠": "radar/ning-xia/wu-zhong.htm",
    #
    "新疆": "radar/xin-jiang/wu-lu-mu-qi.htm",
    "乌鲁木齐": "radar/xin-jiang/wu-lu-mu-qi.htm",
    "克拉玛依": "radar/xin-jiang/ke-la-ma-yi.htm",
    "库尔勒": "radar/xin-jiang/ku-er-le.htm",
    "阿克苏": "radar/xin-jiang/a-ke-su.htm",
    "伊宁": "radar/xin-jiang/yi-ning.htm",
    "石河子": "radar/xin-jiang/shi-he-zi.htm",
    "喀什": "radar/xin-jiang/ka-shen.htm",
    "奎屯": "radar/xin-jiang/kui-tun.htm",
    "五家渠": "radar/xin-jiang/wu-jia-qu.htm",
    "图木舒克": "radar/xin-jiang/tu-mu-shu-ke.htm",
    "塔斯尔海": "radar/xin-jiang/si-ta-er-hai.htm",
    "阿拉尔": "radar/xin-jiang/a-la-er.htm",
    "和田": "radar/xin-jiang/he-tian.htm",
    "精河": "tianqishikuang/leidatu/danzhanleida/xinjiang/jinghe/index.html",
}
