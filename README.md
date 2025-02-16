# 🎯 Cursor 注册助手

<div align="center">

[🌍 English Version](./README_EN.md) | [🇨🇳 中文版](./README.md)

> 🚀 一个帮助你轻松使用 Cursor 的小工具，支持多种注册方式，操作简单便捷。
> 
> 💫 让注册过程变得简单而优雅

<p align="center">
<img src="https://img.shields.io/github/v/release/ktovoz/cursorRegister?style=flat&logo=github&color=blue" alt="GitHub release"/>
<img src="https://img.shields.io/badge/license-CC%20BY--NC--ND%204.0-lightgrey.svg?style=flat&logo=creative-commons&color=green" alt="License"/>
<img src="https://img.shields.io/github/stars/ktovoz/cursorRegister?style=flat&logo=github&color=yellow" alt="GitHub stars"/>
<br/>
<img src="https://img.shields.io/badge/Windows-0078D6?style=flat&logo=windows&logoColor=white" alt="Windows Support"/>
<img src="https://img.shields.io/badge/Python-3.7+-blue.svg?style=flat&logo=python&logoColor=white" alt="Python"/>
<br/>
<a href="https://github.com/ktovoz/cursorRegister/issues"><img src="https://img.shields.io/github/issues/ktovoz/cursorRegister?style=flat&logo=github&color=orange" alt="GitHub issues"/></a>
<a href="https://github.com/ktovoz/cursorRegister/network"><img src="https://img.shields.io/github/forks/ktovoz/cursorRegister?style=flat&logo=github&color=purple" alt="GitHub forks"/></a>
</p>

</div>

<p align="center">
  <b>
  <a href="#-快速开始">快速开始</a> •
  <a href="#-下载安装">下载安装</a> •
  <a href="#-使用方法">使用方法</a> •
  <a href="#-注册方式">注册方式</a> •
  <a href="#-常见问题">常见问题</a>
  </b>
</p>

<div align="center">

```shell
🎉 让 Cursor 注册变得简单而优雅 
```

</div>

---

<div align="center">

## ⚡ 快速开始

</div>

### 🌟 核心特性

- 🚀 全自动化注册流程
- 📧 多样化邮箱配置方案
- 🔒 安全可靠的账号管理
- 🎨 简洁优雅的操作界面
- 🔄 智能的自动更新保护
- 🌐 多平台兼容支持
- ⚙️ 灵活的配置选项

### 📋 系统要求

- 💻 Windows 系统
- 🎯 Cursor v0.44.11
- 🐍 Python 3.7+
- 🌐 稳定的网络连接
- 📮 可用的邮箱服务

<div align="center">

## 📥 下载安装

</div>

<details>
<summary><b>🖥️ Cursor 编辑器</b></summary>

### Windows 版本 (v0.44.11)
- 🔗 [官方下载](https://downloader.cursor.sh/builds/250103fqxdt5u9z/windows/nsis/x64)
- 🔄 [备用下载](https://download.todesktop.com/230313mzl4w4u92/Cursor%20Setup%200.44.11%20-%20Build%20250103fqxdt5u9z-x64.exe)

</details>

<details>
<summary><b>🛠️ 注册助手</b></summary>

- 📦 [从 Release 页面下载](https://github.com/ktovoz/cursorRegister/releases)
> 💡 请下载最新版本以获得最佳体验

</details>

<div align="center">

## 📑 功能目录

</div>

<table>
<tr>
<td width="33%" align="center"><a href="#-快速开始">⚡ 快速开始</a></td>
<td width="33%" align="center"><a href="#-下载安装">📥 下载安装</a></td>
<td width="33%" align="center"><a href="#-使用方法">🎯 使用方法</a></td>
</tr>
<tr>
<td width="33%" align="center"><a href="#-注册方式">📝 注册方式</a></td>
<td width="33%" align="center"><a href="#-常见问题">❓ 常见问题</a></td>
<td width="33%" align="center"><a href="#-社区交流">🤝 社区交流</a></td>
</tr>
</table>

<div align="center">

## 🎯 使用方法

</div>

### 🔰 前期准备

#### 📧 邮箱配置（二选一）

<table>
<tr>
<th>方案类型</th>
<th>配置步骤</th>
<th>优势</th>
</tr>
<tr>
<td>

**📨 临时邮箱**
*(简单快捷)*

</td>
<td>

1. 访问临时邮箱服务
2. 获取临时邮箱地址
3. 确保可接收验证邮件

</td>
<td>

- ⚡ 即开即用
- 🆓 完全免费
- 🔄 随用随换

</td>
</tr>
<tr>
<td>

**🌐 自有域名**
*(推荐方案)*

</td>
<td>

1. 准备一个域名
2. Cloudflare 配置：
   - DNS 记录设置
   - 邮箱转发规则

</td>
<td>

- 🔒 更高安全性
- ♾️ 永久可用
- 🎛️ 完全控制

</td>
</tr>
</table>

<div align="center">

## 🎯 注册方式

</div>


### 🌈 支持的注册方式


### 1️⃣ 全自动注册
推荐新手使用

<details>
<summary><b>📝 详细步骤</b></summary>

1. 获取必要信息：
   - 从 [moemail](https://github.com/beilunyang/moemail) 获取 API KEY
   - 获取可用 DOMAIN
2. 配置 .env 文件：
   ```
   API_KEY=你的API密钥
   DOMAIN=你的域名
   ```
3. 开始注册：
   - 勾选"全自动注册"
   - 点击"自动注册"
   - 等待完成

</details>

### 2️⃣ 手动注册
支持多种邮箱方案

<details>
<summary><b>📝 详细步骤</b></summary>

1. 选择邮箱方案：

   **方案A：临时邮箱**
   - 访问临时邮箱服务网站
   - 获取一个临时邮箱地址
   - ⚡ 优点：快速便捷
   - ⚠️ 缺点：可能被屏蔽

   **方案B：自有域名**
   - 准备一个域名
   - 配置 DNS 记录
   - 设置邮箱转发规则
   - 🔒 优点：稳定可靠
   - ⚙️ 缺点：需要配置

2. 开始注册流程：
   - 打开注册助手
   - 填写域名
   - 生成随机邮箱和密码
   - 选择验证方式
   - 点击"自动注册"

3. 选择验证方式：
   - 🤖 自动验证：软件自动通过人机验证
   - 👨‍💻 人工验证：手动通过人机验证
   > 💡 提示：两种方式都需要自己输入邮箱验证码

4. 完成验证：
   - 等待接收验证码
   - 根据选择的验证方式完成验证
   - 等待注册完成

5. 保存账号信息

</details>

### 3️⃣ GitHub Action
⚠️ 研发中

<details>
<summary><b>📝 详细步骤</b></summary>

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
   - 在弹出的对话框中输入 `DOMAIN` 值
5. 使用生成的账号：
   - 从 Artifacts 下载账号信息
   - 打开注册助手程序填入信息
   - 点击"刷新cookie"完成配置

> ⚠️ 注意事项：
> - 建议自行部署 moemail 服务以确保稳定性
> - 及时从 Artifacts 下载并删除账号信息
> - 妥善保管生成的 token

</details>

### ⭐ 使用建议

<details>
<summary><b>📝 如何选择？</b></summary>

#### 🔰 新手推荐
- 选择全自动注册
- 方便快捷，一键完成
- ⚠️ 需要配置部署moemail邮箱

#### 🎯 稳定需求
- 选择手动注册
- 最为稳定可靠
- 无需额外配置

#### 🔄 批量需求
- 等待 GitHub Action 功能
- 可以实现自动化批量注册

</details>

<div align="center">

## 🎯 常见问题

</div>

<details>
<summary><b>💡 临时邮箱 vs 自有域名？</b></summary>

| 方式 | 优点 | 缺点 |
|:------:|:------:|:------:|
| 📨 临时邮箱 | ⚡ 快速便捷 | ⚠️ 可能被屏蔽 |
| 🌐 自有域名 | 🔒 稳定可靠 | ⚙️ 需要配置 |

</details>

<details>
<summary><b>🔧 注册失败解决方案</b></summary>

- 🔄 尝试不同的临时邮箱服务
- 🌐 切换到自有域名方式
- 📡 检查网络连接

</details>

<details>
<summary><b>🍪 手动获取 Cookie</b></summary>

1. 🔍 打开浏览器开发者工具（F12）
2. 🌐 访问 cursor.sh 并登录
3. 🔎 在 Network 中找到 Cookie
4. 📋 复制并更新到程序中

</details>

<div align="center">

## 🤝 社区交流

</div>

<div align="center">
<table>
<tr>
<td align="center">
<img src="assets/wx_20250215215655.jpg" width="280" height="420" alt="社区交流群">
</td>
<td>

### 🌟 加入我们的社区

- 📢 获取最新项目动态
- 💡 解决使用过程疑难
- 🎯 分享使用心得体会
- 🔧 探讨技术实现细节

#### 扫描左侧二维码，立即加入交流群！

</td>
</tr>
</table>
</div>

<div align="center">

## 详细教程 📖

</div>

访问 [Cursor 注册助手食用指南](https://www.ktovoz.com/blog/%E6%95%99%E5%AD%A6/Cursor%E6%B3%A8%E5%86%8C%E5%8A%A9%E6%89%8B%E9%A3%9F%E7%94%A8%E6%8C%87%E5%8D%97) 获取完整教程。

<div align="center">

## 🌟 致谢

</div>

感谢以下开源项目的贡献：

<div align="center">

<table>
<tr>
<td align="center">
<a href="https://github.com/chengazhen/cursor-auto-free">
<img src="https://github.com/chengazhen.png" width="50px;" alt="cursor-auto-free"/><br/>
<sub><b>cursor-auto-free</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/yuaotian/go-cursor-help">
<img src="https://github.com/yuaotian.png" width="50px;" alt="go-cursor-help"/><br/>
<sub><b>go-cursor-help</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/JiuZ-Chn/CursorRegister">
<img src="https://github.com/JiuZ-Chn.png" width="50px;" alt="CursorRegister"/><br/>
<sub><b>CursorRegister</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/beilunyang/moemail">
<img src="https://github.com/beilunyang.png" width="50px;" alt="moemail"/><br/>
<sub><b>moemail</b></sub>
</a>
</td>
</tr>
</table>

</div>

<div align="center">

## 📜 许可证与声明

</div>

### 📋 许可说明
本项目采用 [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) 许可证

#### ✅ 您可以：
- 📤 分享 — 在任何媒介以任何形式复制、发行本作品

#### ❌ 但是不能：
- 💰 商业使用
- ✏️ 修改原作品
- 🔄 二次分发

### ⚠️ 免责声明

- 📚 仅供学习交流
- 🚫 禁止商业用途
- ⚖️ 使用后果自负
- 🔒 作者不承担责任

---

<div align="center">

**[⬆ 返回顶部](#-cursor-注册助手)**

<br/>

<sub>用 ❤️ 制作 | Copyright © 2024 ktovoz</sub>

</div>
