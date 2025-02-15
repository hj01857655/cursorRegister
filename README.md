# Cursor 注册助手

[English Version](./README_EN.md)

> 一个帮助你轻松使用 Cursor 的小工具

## 📥 下载 Cursor

### Windows 版本 (v0.44.11)
- ⚡ [Cursor 官方下载](https://downloader.cursor.sh/builds/250103fqxdt5u9z/windows/nsis/x64)
- 🔄 [ToDesktop 备用下载](https://download.todesktop.com/230313mzl4w4u92/Cursor%20Setup%200.44.11%20-%20Build%20250103fqxdt5u9z-x64.exe)

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
#### 1️⃣ 账号注册
- **使用临时邮箱注册：**
  - 在邮箱输入框中填入临时邮箱地址
  - 选择"自动注册"，程序将自动填写注册信息

- **使用自有域名注册：**
  - 点击"生成账号"获取随机的邮箱和密码
  - 选择"自动注册"，程序将自动填写注册信息

- 遇到人机验证时，请手动完成验证
- 等待注册完成，系统会自动保存账号信息

#### 2️⃣ 登录凭证配置
- 完成注册后，程序会自动：
  - 获取账号 Cookie 信息
  - 将 Cookie 填入相应输入框
  - 更新 .env 配置文件
- 点击"刷新Cookie"按钮，使本地 Cursor 自动登录

#### 3️⃣ ID重置和更新保护
- 点击"重置ID"按钮，程序将自动：
  - 重置设备机器码
  - 关闭 Cursor 自动更新功能
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
完整的使用教程已发布在[Cursor 注册助手食用指南](https://www.ktovoz.com/blog/%E6%95%99%E5%AD%A6/Cursor%E6%B3%A8%E5%86%8C%E5%8A%A9%E6%89%8B%E9%A3%9F%E7%94%A8%E6%8C%87%E5%8D%97)


## 🙏 致谢
特别感谢以下开源项目的贡献：

- [cursor-auto-free](https://github.com/chengazhen/cursor-auto-free)
- [go-cursor-help](https://github.com/yuaotian/go-cursor-help)

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
