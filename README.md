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

### 可选：域名配置（推荐）
如果您希望使用自己的域名进行注册：
1. 准备一个可用的域名（推荐使用便宜的域名服务商）
2. 在 Cloudflare 上完成以下配置:
   - 添加域名并配置 DNS 记录
   - 开启并设置邮箱转发功能（Cloudflare Email Routing）

### 使用步骤

#### 1️⃣ 配置邮箱设置
选择以下任一方式：
- **方式一：使用临时邮箱**
  - 在邮箱输入框中填入任意临时邮箱地址（如 temp-mail.org、10minutemail.com 等提供的邮箱）
  - 确保能够访问该临时邮箱以接收验证邮件
- **方式二：使用自有域名**（可选）
  - 在邮箱输入框中填入已完成邮箱转发配置的域名
  - 确保域名配置正确，以便接收验证邮件
  - 点击"生成随机账号"获取随机的邮箱和密码
#### 2️⃣ 账号注册流程
- 选择"自动注册"，程序将自动填写注册信息
- 遇到人机验证环节时，请手动完成验证步骤
- 等待注册流程完成，系统会自动保存账号信息

#### 3️⃣ ID重置操作
- 点击"重置ID"按钮
- 程序将自动执行以下操作：
  - 重置设备机器码
  - 关闭 Cursor 自动更新功能
  - 确保账号正常使用

#### 4️⃣ 登录凭证更新
- 完成注册后，程序会自动：
  - 获取账号 Cookie 信息
  - 将 Cookie 填入相应输入框
  - 更新 .env 配置文件
- 点击"刷新Cookie"按钮，使本地 Cursor 自动登录已注册账号

## ⚙️ 禁用自动更新
为确保 Cursor 不会自动更新到不支持的新版本，程序会自动禁用自动更新功能。

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
