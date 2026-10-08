# 消息媒体与 Clash Fake-IP

图片、地图瓦片和网页快照只允许访问公开 HTTP(S) 地址。运行 Frontier 的主机必须能连接素材来源；QQ 客户端的网络不参与素材加载。

默认开启 `[agent].message_media_fake_ip_fallback = true`。当系统 DNS 为域名只返回 `198.18.0.0/15` 地址时，媒体加载器会通过 Cloudflare 的 HTTPS DNS JSON API 查询真实 IPv4 地址。解析服务使用固定公网 IP `1.1.1.1` 连接，保留 `cloudflare-dns.com` 的 TLS 校验和 Host，避免解析服务自身再次落入 Fake-IP。

加载器校验解析结果后直接连接真实公网 IP，保留原素材域名的 TLS 校验和 Host。不会连接 Fake-IP，也不会放行回环、私网、链路本地、IPv4 映射 IPv6 地址或直接写入 URL 的 Fake-IP。每次重定向和网页子资源仍执行相同校验；DNS 返回混合的 Fake-IP 与其他地址时保持拒绝。

解析结果只在当前回复的媒体加载过程中缓存，共用总大小与超时预算。解析服务不接受重定向，单次响应最多 64 KiB；查询失败不降级为连接未经校验的地址。只有遇到 Fake-IP 才向 Cloudflare 查询素材域名，普通公网 DNS 路径不受影响。

Clash TUN 仍可接管真实公网 IP 的连接。需要 TUN 路由能够访问 `1.1.1.1:443` 和素材服务；此兼容并不替代代理或保证所有外站可达。单独启用系统 HTTP 代理时，媒体加载器仍不会读取环境代理。

网页与素材支持 identity、gzip 和 deflate 响应；压缩流必须完整，下载和解压后的内容均受大小预算限制。不支持的编码会显示说明。网页只等待主体出现，再给可见图片最多 2 秒；部分图片或字体过慢时仍截取已经加载的内容。失败提示提供 HTTP 状态码、DNS、连接或超时等分类，不输出原始异常、内部地址和凭据。

若不需要自动解析回退，在 `env.toml` 中设置：

```toml
[agent]
message_media_fake_ip_fallback = false
```

保持原有 `[agent]` 表，添加或修改该键后重启。关闭时，可改用 Clash `fake-ip-filter` 排除素材域名。

协议依据：[Cloudflare DNS JSON API](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/dns-json/)。
