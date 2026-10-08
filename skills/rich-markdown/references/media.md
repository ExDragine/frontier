# Media components

媒体是独立模块，可直接放在 ui 根或 section 中。与正文、卡片、表格自由组合；宽图、地图、网页快照优先单独整行，不塞进狭窄的并列卡片。

## Image

```json
{"type":"image","url":"https://example.com/photo.png","alt":"说明图片内容","caption":"可选的来源或说明","aspect":"original","fit":"contain"}
```

`url` 必填，必须是已知的完整公开 HTTP(S) 图片地址，不猜素材 URL。
`alt` 必填（200 字符），`caption` 可选（200）。`aspect` 为 `original`（默认）、`landscape`（16:9）、`portrait`（3:4）或 `square`。`fit` 为 `contain`（默认保留全图）或 `cover`（裁切铺满）。文字、图表和需要查阅的资料保留原图比例，不裁掉信息。

渲染器下载并重新编码位图；不接受 file/data URL、任意本地路径、SVG、模型提供的 media_data 或 HTML。动态图只截第一帧。

## Map

```json
{"type":"map","title":"地点位置","latitude":31.2304,"longitude":121.4737,"zoom":13,"height":480,"caption":"示例坐标，使用时应核实实际地点"}
```

`latitude`（-85–85）、`longitude`（-180–180）必填，均为有限数值。坐标系为 **WGS84**；高德/腾讯的 GCJ-02 坐标不能直接当作 WGS84。先用工具或可靠来源查证，不能从地名猜坐标。
`zoom` 为 2–18，默认 13；`height` 为 200–1000，默认 480；`title/caption` 可选（200）。
当前底图是 OpenStreetMap 单点地图，自动包含坐标、地图 URL 和署名。底图无法加载时保留坐标及链接，不用假的道路或装饰地图代替真实底图。需要特定地图提供商的公开页面时可用 iframe 展示其 URL。

## Iframe

```json
{"type":"iframe","url":"https://example.com/public-dashboard","title":"公开页面预览","height":480,"caption":"可选：页面来源或截取范围"}
```

`url/title` 必填，title 最多 200 字符；`height` 为 200–1200，默认 480；`caption` 可选（200）。height 是网页快照的截取高度，宽度由输出宽度决定，窄屏会按比例缩放。更高的页面需要增加 height 或改用已有网页截图工具；不把整个长页面压成小卡片。

这是**静态网页快照**：在独立、无登录状态的环境中加载公开页面，之后以无脚本的 iframe 嵌入离线长图。不能交互、登录、播放视频或滚动查看未截图内容。不支持 raw HTML、srcdoc、CSS、JavaScript、选择器或任意执行代码。

只使用已知可信且确实用于回答的 URL。不为了装饰而自动访问不相关网页，不截图未经核实的用户隐私或登录页。需要登录、验证码、非 GET 请求、WebSocket、仅代理网络、强制压缩响应或长时间加载的页面可能无法展示；失败时显示说明和原链接，不声称已加载成功。

## Loading limits

每条回复最多预加载 6 个媒体模块；最多同时加载 3 个，整体最多等待 25 秒。单张图片最多 10 MB、20 百万像素；本轮网络资源总计最多 20 MB。只允许公网 HTTP(S) 的 80/443 端口；重定向和网页子资源同样受控。不要在 JSON 中传这些内部限制或资源字段。

普通正文和图表继续本地渲染，媒体失败不影响其余内容。500 字截图规则保留。需要复制图片/地图/网页地址时按全局提示词另发纯文本。
