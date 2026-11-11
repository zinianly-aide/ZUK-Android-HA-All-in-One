# 08｜安全、开源许可与公开仓库脱敏

本仓库发布的是原创 SOP、脚本、参数验证清单。**公开 GitHub 永久可被检索和克隆**；删除一次误提交的 OAuth token 并不能保证泄露已消除，因此必须在首次 push 之前严格审计。

## 禁止提交的敏感资料

- Termux `~/zuk-ha-native/config-ha/.storage` 的所有文件（包含 HA 认证、配置项、米家 OAuth 凭据、设备 ID、集成状态）。
- `secrets.yaml`、HA Access Token、智能设备本地 token、云 API 凭据、Cookie、VPN 配置、账号密码。
- 小米 OAuth 回调 URL，尤其包含 `state`、`code` 或参数的完整链接。
- 个人家庭 IP、门牌、Wi-Fi SSID、MAC 地址、具体房间与设备清单，以及未经脱敏的截图或日志。
- Android/Termux keychain/keystore、ADB 密钥、GitHub `gh` 凭据、根目录 `.env`、手机联系人。
- Cloudflare R2 临时签名 URL，即使将来会过期也不要放到公开仓库。
- 不分发 Chrome、WebView、HA Android、Termux 或第三方 Xiaomi Home 的原版安装包。它们有各自许可与发布渠道。

## 代码与依赖许可

本仓库原创脚本与文档采用 [MIT](../LICENSE)，不意味着上游 Home Assistant、Google Chrome/WebView、Termux、Xiaomi Home 也自动适用 MIT。使用请遵守各上游项目许可与发布条款。

## 本机安全自检

```bash
# 在刚创建的公开仓库根目录执行，不要在 HA 真正的配置目录运行 git add -A。
git status --short
git ls-files

# 在最终提交的文件中搜索高风险迹象；命中需人工确认，不能直接把命中内容贴到公开 Issue。
git grep -n -i -E 'x-amz-signature|x-amz-credential|refresh_token|access_token|authorization: bearer|client_secret|password=' || true
```

**绝对不要**为了方便在公开仓库新增“自动上传 HA 配置”的 CI。真实配置备份应离线或加密存放于个人受控存储。

## 运维风险

Android 7、Chrome/WebView 119 均停止了安全维护；不要把 HA HTTP 端口直接暴露到互联网。可使用隔离 VLAN、可信 VPN 和 HA 多因素认证，定期进行离线备份；要严格限制 Root 和远程调试。长时间运行需关注锂电池状态、充电温度、设备自启动权限及存储空间。
