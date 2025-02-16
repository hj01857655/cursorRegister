# Cursor 注册助手

[English Version](./README_EN.md)

> 一个帮助你轻松使用 Cursor 的小工具

## 📥 下载 Cursor

### Windows 版本 (v0.44.11)

- ⚡ [Cursor 官方下载](https://downloader.cursor.sh/builds/250103fqxdt5u9z/windows/nsis/x64)

🔄 [ToDesktop 备用下载](https://download.todesktop.com/230313mzl4w4u92/Cursor%20Setup%200.44.11%20-%20Build%20250103fqxdt5u9z-x64.exe)

### 注册助手下载

- 📦 [从 Release 页面下载](https://github.com/ktovoz/cursorRegister/releases)
  > 在 Release 页面下载最新版本的注册助手程序

## 🔐 使用方法

### 使用前准备

#### 1️⃣ 下载并安装

- 从 Release 页面下载最新版本的注册助手程序
- 确保已安装 Cursor v0.44.11 版本

#### 2️⃣ 邮箱配置（二选一）

- **方式一：使用临时邮箱**（简单快捷）
    - 使用临时邮箱服务（如 temp-mail.org、10minutemail.com 等）
    - 确保能够访问该临时邮箱以接收验证邮件

- **方式二：使用自有域名**（推荐长期使用）
    1. 准备一个可用的域名（推荐使用便宜的域名服务商）
    2. 在 Cloudflare 上完成配置:
        - 添加域名并配置 DNS 记录
        - 开启并设置邮箱转发功能（Cloudflare Email Routing）

### 注册和配置步骤

#### 1️⃣ 账号注册方式（四选一）

##### 方式一：软件全自动注册（新手推荐）
1. 从 [moemail](https://github.com/beilunyang/moemail) 服务获取：
    - API KEY
    - 可用的 DOMAIN
2. 配置软件：
    - 打开 .env 文件
    - 填入 `API_KEY=你的API密钥`
    - 填入 `DOMAIN=你的域名`
3. 开始注册：
    - 勾选"全自动注册"选项
    - 点击"自动注册"按钮
    - 等待程序自动完成注册流程
> ⚠️ 注意：
> - 确保填入的 API KEY 和 DOMAIN 是有效的
> - 注册过程中可能需要手动完成人机验证
> - 注册成功后程序会自动配置所有必要信息

##### 方式二：GitHub Action 自动注册（进阶用户推荐）
1. Fork 本项目到你的 GitHub 账号
2. 从 [moemail](https://github.com/beilunyang/moemail) 项目获取 API KEY
3. 配置 GitHub Secrets：
    - 进入项目设置 -> Secrets and variables -> Actions
    - 添加名为 `API_KEY` 的 secret，值为获取到的 API KEY
    - 添加名为 `MOE_MAIL_URL` 的 secret，值为 moemail 服务的 URL
4. 触发注册流程：
    - 进入 Actions 标签页
    - 选择 `注册账号` workflow
    - 点击 "Run workflow"
    - 在弹出的对话框中输入 `DOMAIN` 值（从 moemail 服务获取的域名）
5. 使用生成的账号：
    - 从 Artifacts 下载账号信息
    - 打开注册助手程序填入信息
    - 点击"刷新cookie"完成配置
> ⚠️ 注意：
> - 建议自行部署 moemail 服务以确保稳定性
> - 及时从 Artifacts 下载并删除账号信息
> - 妥善保管生成的 token

##### 方式三：使用临时邮箱注册（简单但不稳定）
1. 准备临时邮箱地址（如 temp-mail.org、10minutemail.com 等）
2. 在程序中：
    - 填入临时邮箱地址
    - 勾选"人工过验证"或"自动过验证"选项
    - 点击"自动注册"按钮
3. 验证步骤：
    - 等待注册邮件发送
    - 在临时邮箱中查收验证码
    - 手动将验证码填入程序
    - 等待注册完成
> ⚠️ 注意：
> - 部分临时邮箱可能被 Cursor 屏蔽
> - 请确保能及时收到并填写验证码
> - 验证码有效期较短，需要快速操作

##### 方式四：使用自有域名注册（稳定可靠）
1. 域名配置：
    - 准备一个可用域名
    - 在 Cloudflare 配置 DNS 和邮箱转发
2. 注册流程：
    - 点击"生成账号"获取随机邮箱和密码
    - 勾选"人工过验证"或"自动过验证"选项
    - 点击"自动注册"按钮
3. 验证步骤：
    - 等待注册邮件发送到域名邮箱
    - 从转发的邮件中获取验证码
    - 手动将验证码填入程序
    - 等待注册完成
> ⚠️ 注意：
> - 确保域名邮箱转发配置正确
> - 验证码有效期较短，请及时查收并填写
> - 如未收到验证码，检查邮箱转发设置

#### 2️⃣ 登录凭证配置

注册完成后，程序会自动：
- 获取账号 Cookie 信息
- 将 Cookie 填入相应输入框
- 更新 .env 配置文件
- 点击"刷新Cookie"按钮使本地 Cursor 自动登录

#### 3️⃣ ID重置和更新保护

完成注册后：
- 点击"重置ID"按钮
- 程序将自动：
    - 重置设备机器码
    - 关闭自动更新功能
    - 确保账号正常使用

### ⚙️ 其他说明

- 程序会自动禁用 Cursor 的自动更新功能，确保不会更新到不支持的新版本
- 建议定期备份 .env 配置文件，以防需要重新配置

### ❓ 常见问题 (FAQ)

#### 1. 为什么推荐使用自有域名而不是临时邮箱？

- 知名的临时邮箱服务（如 temp-mail.org、10minutemail 等）可能被 Cursor 屏蔽，导致注册失败
- 自有域名可以长期稳定使用，不会被识别为临时邮箱
- 使用自有域名可以生成多个随机邮箱账号，更加灵活

#### 2. 使用临时邮箱注册失败怎么办？

- 尝试使用较为小众的临时邮箱服务
- 建议切换到自有域名方式注册，这是最稳定可靠的方案
- 如果一定要使用临时邮箱，可以多尝试几个不同的临时邮箱服务

#### 3. 自动注册功能不可用怎么办？

- 可以手动在浏览器中完成注册流程
- 注册成功后，从浏览器开发者工具中获取 Cookie：
    1. 打开浏览器开发者工具（F12）
    2. 进入 Network（网络）标签页
    3. 访问 cursor.sh 网站并注册登录
    4. 在请求中搜索`WorkosCursorSessionToken`找到包含完整 Cookie 信息的请求
    5. 复制 Cookie 值
- 将获取到的 Cookie 粘贴到程序中
- 点击"更新账号信息"按钮更新登录信息

## 📖 详细教程

推荐使用半自动注册。

完整的使用教程已发布在[Cursor 注册助手食用指南](https://www.ktovoz.com/blog/%E6%95%99%E5%AD%A6/Cursor%E6%B3%A8%E5%86%8C%E5%8A%A9%E6%89%8B%E9%A3%9F%E7%94%A8%E6%8C%87%E5%8D%97)

有疑问可以进群交流:

<img src="assets/wx_20250215215655.jpg" width="300" height="450" alt="进群交流" style="float: left; margin-right: 20px;">

## 🙏 致谢

特别感谢以下开源项目的贡献：

- [cursor-auto-free](https://github.com/chengazhen/cursor-auto-free)
- [go-cursor-help](https://github.com/yuaotian/go-cursor-help)
- [CursorRegister](https://github.com/JiuZ-Chn/CursorRegister)
- [moemail](https://github.com/beilunyang/moemail) - 提供了稳定可靠的临时邮箱服务

## 📜 许可证与声明

### 许可证

本项目采用 [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) 许可证，允许您：

- ✅ 分享 — 在任何媒介以任何形式复制、发行本作品

限制条件：

- ❌ 禁止商业使用
- ❌ 禁止修改原作品
- ✅ 必须保留原作者署名

### 免责声明

> ⚠️ 重要提示：
> - 本项目仅供学习交流，严禁用于商业用途
> - 使用本项目产生的任何后果由使用者自行承担
> - 作者不对使用过程中可能出现的任何问题负责
