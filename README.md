# Cursor 注册助手 🚀

<div align="center">

[English Version](./README_EN.md)

> 一个帮助你轻松使用 Cursor 的小工具，支持多种注册方式，操作简单便捷。

![GitHub release (latest by date)](https://img.shields.io/github/v/release/ktovoz/cursorRegister)
![License](https://img.shields.io/badge/license-CC%20BY--NC--ND%204.0-lightgrey.svg)
![GitHub stars](https://img.shields.io/github/stars/ktovoz/cursorRegister)
![Windows Support](https://img.shields.io/badge/Windows-0078D6?style=flat&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.7+-blue.svg?logo=python&logoColor=white)

</div>

<p align="center">
  <a href="#快速开始-">快速开始</a> •
  <a href="#下载安装-">下载安装</a> •
  <a href="#使用方法-">使用方法</a> •
  <a href="#注册方式-">注册方式</a> •
  <a href="#常见问题-">常见问题</a>
</p>

---

## ⚡ 快速开始

<table>
<tr>
<td width="50%">

### 🔥 特性

- 🚀 全自动注册流程
- 📧 多种邮箱配置方案
- 🔒 安全可靠的账号管理
- 🛠️ 简单易用的界面
- 🔄 自动更新保护

</td>
<td width="50%">

### 📋 前置要求

- Windows 系统
- Cursor v0.44.11
- Python 3.7+
- 网络连接
- 邮箱服务

</td>
</tr>
</table>

## 📥 下载安装

<details>
<summary>Cursor 编辑器</summary>

### Windows 版本 (v0.44.11)
- 🔗 [官方下载](https://downloader.cursor.sh/builds/250103fqxdt5u9z/windows/nsis/x64)
- 🔄 [备用下载](https://download.todesktop.com/230313mzl4w4u92/Cursor%20Setup%200.44.11%20-%20Build%20250103fqxdt5u9z-x64.exe)

</details>

<details>
<summary>注册助手</summary>

- 📦 [从 Release 页面下载](https://github.com/ktovoz/cursorRegister/releases)
> 💡 请下载最新版本以获得最佳体验

</details>

## 目录 📑

- [快速开始](#快速开始-)
- [下载安装](#下载安装-)
- [使用方法](#使用方法-)
- [注册方式](#注册方式-)
- [常见问题](#常见问题-)
- [交流群](#交流群-)
- [致谢](#致谢-)
- [许可证与声明](#许可证与声明-)

## 快速开始 🚀

1. 下载并安装 Cursor v0.44.11
2. 下载最新版本注册助手
3. 选择注册方式（全自动/半自动）
4. 按提示完成注册配置

## 使用方法 🔐

### 前期准备

#### 邮箱配置（二选一）

##### 方案1：临时邮箱（简单快捷）
- 使用临时邮箱服务（如 temp-mail.org）
- 确保可以接收验证邮件

##### 方案2：自有域名（推荐）
1. 准备一个域名
2. 在 Cloudflare 配置：
   - DNS 记录
   - 邮箱转发功能

## 注册方式 📝

### 1. 全自动注册（推荐新手）

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

### 2. 使用临时邮箱注册

1. 准备临时邮箱
2. 填写信息并选择验证方式
3. 等待接收验证码
4. 完成注册

### 3. 使用自有域名注册

1. 完成域名配置
2. 生成随机邮箱
3. 按提示完成注册流程

### 4. GitHub Action 自动注册 ⚠️ [研发中]

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

> ⚠️ 注意：此功能正在研发中，暂不可用
> - 建议自行部署 moemail 服务以确保稳定性
> - 及时从 Artifacts 下载并删除账号信息
> - 妥善保管生成的 token

## 常见问题 ❓

### 1. 临时邮箱 vs 自有域名？

| 方式 | 优点 | 缺点 |
|------|------|------|
| 临时邮箱 | 快速便捷 | 可能被屏蔽 |
| 自有域名 | 稳定可靠 | 需要配置 |

### 2. 注册失败解决方案

- 尝试不同的临时邮箱服务
- 切换到自有域名方式
- 检查网络连接

### 3. 手动获取 Cookie

1. 打开浏览器开发者工具（F12）
2. 访问 cursor.sh 并登录
3. 在 Network 中找到 Cookie
4. 复制并更新到程序中

## 🤝 交流群

<div align="center">
<table>
<tr>
<td>
<img src="assets/wx_20250215215655.jpg" width="300" height="450" alt="进群交流">
</td>
<td>

### 扫码加入交流群
- 获取最新更新
- 解决使用问题
- 分享使用经验
- 交流技术话题

</td>
</tr>
</table>
</div>

## 详细教程 📖

访问 [Cursor 注册助手食用指南](https://www.ktovoz.com/blog/%E6%95%99%E5%AD%A6/Cursor%E6%B3%A8%E5%86%8C%E5%8A%A9%E6%89%8B%E9%A3%9F%E7%94%A8%E6%8C%87%E5%8D%97) 获取完整教程。

## 致谢 🙏

感谢以下开源项目：

- [cursor-auto-free](https://github.com/chengazhen/cursor-auto-free)
- [go-cursor-help](https://github.com/yuaotian/go-cursor-help)
- [CursorRegister](https://github.com/JiuZ-Chn/CursorRegister)
- [moemail](https://github.com/beilunyang/moemail)

## 📜 许可证与声明

<table>
<tr>
<td width="70%">

### 许可证说明
本项目采用 [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) 许可证

✅ 允许：
- 分享 — 在任何媒介以任何形式复制、发行本作品

❌ 不允许：
- 商业使用
- 修改原作品
- 二次分发

</td>
<td width="30%">

### ⚠️ 免责声明
- 仅供学习交流
- 禁止商业用途
- 使用后果自负
- 作者免责声明

</td>
</tr>
</table>

---

<div align="center">

**[⬆ 返回顶部](#cursor-注册助手-)**

</div>
