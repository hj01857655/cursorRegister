# Cursor 注册助手

> 一个帮助你轻松使用 Cursor 的小工具

## 📥 下载 Cursor

### Windows 版本 (v0.44.11)
- ⚡ [Cursor 官方下载](https://downloader.cursor.sh/builds/250103fqxdt5u9z/windows/nsis/x64)
- 🔄 [ToDesktop 备用下载](https://download.todesktop.com/230313mzl4w4u92/Cursor%20Setup%200.44.11%20-%20Build%20250103fqxdt5u9z-x64.exe)

### 注册助手下载
- 📦 [从 Release 页面下载](https://github.com/ktovoz/cursorRegister/releases)
  > 在 Release 页面下载最新版本的注册助手程序

## 🔐 使用方法

### 前置准备
1. 购买一个域名
2. 在 Cloudflare 上配置:
   - DNS 设置
   - 邮箱转发功能

### 具体步骤

#### 1️⃣ 配置环境
- 创建 `.env` 文件
- 填入已配置好邮箱转发的域名

#### 2️⃣ 注册账号
- 打开 Cursor 注册页面
- 使用注册助手生成的账户和密码进行注册

#### 3️⃣ 获取 Token
1. 在浏览器中打开开发者工具（F12）
2. 切换到 Network 面板
3. 搜索 `WorkosCursorSessionToken`
4. 复制找到的 token 值

#### 4️⃣ 完成设置
- 将复制的 token 输入到程序中
- 程序将自动刷新登录信息

## ⚙️ 禁用自动更新
为确保 Cursor 不会自动更新到不支持的新版本，建议禁用自动更新功能。

## 📖 详细教程
完整的使用教程将发布在 [ktovoz.com](https://ktovoz.com)

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
