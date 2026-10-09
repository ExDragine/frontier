# 图片、地图与网页快照

此示例用于本地渲染验证，网址由测试夹具提供内容。实际回答时必须核实地址、坐标和来源。

::section{title="各模块保持独立"}
::grid{columns=2}
::card{title="图片与地图" color="emerald"}
图片保留比例；地图注明坐标系和来源。
::
::card{title="网页快照" color="amber"}
公开页面在隔离环境中截图，最终长图展示静态快照。
::
::
::

::image{url="https://example.com/media/demo.png" alt="渲染测试图片" caption="测试夹具提供的图像"}
::

::map{title="地图模块测试" latitude=31.2304 longitude=121.4737 zoom=12 height=420 caption="示例 WGS84 坐标，非真实底图展示"}
::

::iframe{url="https://example.com/public-dashboard" title="独立网页快照" height=420 caption="测试夹具提供的公开页面"}
::

::image{url="https://example.com/media/unavailable.png" alt="不可用素材" caption="失败时保留说明与来源地址"}
::

独立媒体之后继续解释，不需要把后续段落放进媒体模块。
