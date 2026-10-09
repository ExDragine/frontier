# Media components

媒体是独立模块，可直接插入 Markdown 或放在 section 中。与正文、卡片、表格自由组合；宽图、地图、网页快照优先单独整行，不塞进狭窄的并列卡片。媒体正文留空，说明写在 caption，仍要用独立的 `::` 关闭。旧 ui 的同名字段继续支持。

## Image

```markdown
::image{url="https://example.com/photo.png" alt="说明图片内容" caption="可选的来源或说明" aspect="original" fit="contain"}
::
```

`url` 必填，必须是已知的完整公开 HTTP(S) 图片地址，不猜素材 URL。
`alt` 必填（200 字符），`caption` 可选（200）。`aspect` 为 `original`（默认）、`landscape`（16:9）、`portrait`（3:4）或 `square`。`fit` 为 `contain`（默认保留全图）或 `cover`（裁切铺满）。文字、图表和需要查阅的资料保留原图比例，不裁掉信息。

渲染器下载并重新编码位图；不接受 file/data URL、任意本地路径、SVG、模型提供的 media_data 或 HTML。动态图只截第一帧。

## Map

```markdown
::map{title="地点位置" latitude=31.2304 longitude=121.4737 zoom=13 height=480 caption="示例坐标，使用时应核实实际地点"}
::
```

`latitude`（-85–85）、`longitude`（-180–180）必填，均为有限数值。坐标系为 **WGS84**；高德/腾讯的 GCJ-02 坐标不能直接当作 WGS84。先用工具或可靠来源查证，不能从地名猜坐标。
`zoom` 为 2–18，默认 13；`height` 为 200–1000，默认 480；`title/caption` 可选（200）。
当前底图是 OpenStreetMap 单点地图，只获取当前视野的瓦片并按 Web Mercator 投影合成，瓦片缓存 7 天；自动包含坐标、地图 URL 和署名。底图无法加载时保留坐标及链接，不用假的道路或装饰地图代替真实底图。需要特定地图提供商的公开页面时可用 iframe 展示其 URL。

Leaflet 只负责在本地渲染器中叠加声明式图层，适合标记和路径，不要求截图环境再次访问地图瓦片：

```json
{"type":"map","latitude":31.23,"longitude":121.47,"zoom":12,"markers":[{"latitude":31.23,"longitude":121.47,"label":"中心点","color":"#2563eb"}],"paths":[{"points":[[31.22,121.45],[31.24,121.49]],"color":"#e11d48","weight":5}]}
```

`markers` 最多 50 个，`paths` 最多 20 条，每条路径最多 200 个点。不要在消息中写任意 JavaScript。

可选的 `analysis` 使用 Turf.js 对路径进行静态计算：`distance` 计算路径长度，`area` 计算闭合路径面积；通过 `path_index` 选择路径，并可用 `label` 设置显示名称。

## Three.js 场景

`three` 用于产品示意、空间关系和简单三维数据的静态截图。渲染器在本地沙箱中创建场景，并在截图前完成一次渲染：

```three
{"type":"three","height":420,"background":"#0f172a","grid":true,"objects":[{"kind":"cube","position":[0,0.5,0],"color":"#6366f1","size":1},{"kind":"sphere","position":[2,0.5,0],"color":"#f59e0b","size":1}]}
```

可用几何体为 `cube`、`sphere`、`cylinder`、`torus` 和 `plane`。每个对象可设置位置、旋转、缩放、颜色和尺寸，最多 80 个对象。复杂动画和任意脚本暂不直接放进消息协议，优先使用声明式场景保证截图稳定。

## Flow

`flow` 使用 React Flow 展示节点和连线，适合工作流、Agent 决策链和系统关系图。节点需要唯一的 `id`；不填写坐标时渲染器会自动排布。

```flow
{"type":"flow","height":420,"direction":"LR","nodes":[{"id":"input","label":"输入"},{"id":"tool","label":"调用工具","color":"#059669"},{"id":"answer","label":"回答"}],"edges":[{"source":"input","target":"tool"},{"source":"tool","target":"answer","label":"结果"}]}
```

节点最多 80 个，连线最多 120 条。只使用声明式节点和连线，不在消息中写任意 JavaScript。

## Iframe

```markdown
::iframe{url="https://example.com/public-dashboard" title="公开页面预览" height=480 caption="可选：页面来源或截取范围"}
::
```

`url/title` 必填，title 最多 200 字符；`height` 为 200–1200，默认 480；`caption` 可选（200）。height 是网页加载时的初始高度，宽度由输出宽度决定，窄屏会按比例缩放。`full_page` 默认为 true，按实际内容展开，最多 1200 像素；超出时标明截取范围和原链接。只需要初始视口时可设为 false。更高的完整页面使用已有网页截图工具；不把整个长页面压成小卡片。

这是**静态网页快照**：在独立、无登录状态的环境中加载公开页面，之后以无脚本的 iframe 嵌入离线长图。不能交互、登录、播放视频或滚动查看未截图内容。不支持 raw HTML、srcdoc、CSS、JavaScript、选择器或任意执行代码。

只使用已知可信且确实用于回答的 URL。不为了装饰而自动访问不相关网页，不截图未经核实的用户隐私或登录页。需要登录、验证码、非 GET 请求、WebSocket、仅代理网络、强制压缩响应或长时间加载的页面可能无法展示；失败时显示说明和原链接，不声称已加载成功。

## Loading limits

每条回复最多预加载 6 个媒体模块；最多同时加载 3 个，整体最多等待 25 秒。单张图片最多 10 MB、20 百万像素；本轮网络资源总计最多 20 MB。只允许公网 HTTP(S) 的 80/443 端口；重定向和网页子资源同样受控。不要填写内部限制或资源字段。

普通正文和图表继续本地渲染，媒体失败不影响其余内容。500 字截图规则保留。需要复制图片/地图/网页地址时按全局提示词另发纯文本。
