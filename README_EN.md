# Cursor Registration Assistant 🚀

<div align="center">

[中文版](./README.md)

> A tool to help you easily use Cursor with multiple registration methods and simple operations.

![GitHub release (latest by date)](https://img.shields.io/github/v/release/ktovoz/cursorRegister)
![License](https://img.shields.io/badge/license-CC%20BY--NC--ND%204.0-lightgrey.svg)
![GitHub stars](https://img.shields.io/github/stars/ktovoz/cursorRegister)
![Windows Support](https://img.shields.io/badge/Windows-0078D6?style=flat&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.7+-blue.svg?logo=python&logoColor=white)

</div>

<p align="center">
  <a href="#quick-start-">Quick Start</a> •
  <a href="#download-and-installation-">Download & Installation</a> •
  <a href="#how-to-use-">How to Use</a> •
  <a href="#registration-methods-">Registration Methods</a> •
  <a href="#faq-">FAQ</a>
</p>

---

## ⚡ Quick Start

<table>
<tr>
<td width="50%">

### 🔥 Features

- 🚀 Fully automated registration process
- 📧 Multiple email configuration options
- 🔒 Secure account management
- 🛠️ User-friendly interface
- 🔄 Automatic update protection

</td>
<td width="50%">

### 📋 Prerequisites

- Windows OS
- Cursor v0.44.11
- Python 3.7+
- Internet connection
- Email service

</td>
</tr>
</table>

## 📥 Download and Installation

<details>
<summary>Cursor Editor</summary>

### Windows Version (v0.44.11)
- 🔗 [Official Download](https://downloader.cursor.sh/builds/250103fqxdt5u9z/windows/nsis/x64)
- 🔄 [Alternative Download](https://download.todesktop.com/230313mzl4w4u92/Cursor%20Setup%200.44.11%20-%20Build%20250103fqxdt5u9z-x64.exe)

</details>

<details>
<summary>Registration Assistant</summary>

- 📦 [Download from Release Page](https://github.com/ktovoz/cursorRegister/releases)
> 💡 Please download the latest version for the best experience

</details>

## Table of Contents 📑

- [Quick Start](#quick-start-)
- [Download and Installation](#download-and-installation-)
- [How to Use](#how-to-use-)
- [Registration Methods](#registration-methods-)
- [FAQ](#faq-)
- [Community](#community-)
- [Acknowledgments](#acknowledgments-)
- [License and Disclaimer](#license-and-disclaimer-)

## Quick Start 🚀

1. Download and install Cursor v0.44.11
2. Download the latest version of Registration Assistant
3. Choose registration method (Fully/Semi-automatic)
4. Follow prompts to complete registration

## How to Use 🔐

### Preparation

#### Email Configuration (Choose One)

##### Option 1: Temporary Email (Quick & Easy)
- Use temporary email services (like temp-mail.org)
- Ensure you can receive verification emails

##### Option 2: Own Domain (Recommended)
1. Prepare a domain
2. Configure in Cloudflare:
   - DNS records
   - Email forwarding

## Registration Methods 📝

### 1. Fully Automatic Registration (Recommended for Beginners)

1. Get required information:
   - Get API KEY from [moemail](https://github.com/beilunyang/moemail)
   - Get available DOMAIN
2. Configure .env file:
   ```
   API_KEY=your_api_key
   DOMAIN=your_domain
   ```
3. Start registration:
   - Check "Fully Automatic Registration"
   - Click "Auto Register"
   - Wait for completion

### 2. Register with Temporary Email

1. Prepare temporary email
2. Fill in information and choose verification method
3. Wait for verification code
4. Complete registration

### 3. Register with Own Domain

1. Complete domain configuration
2. Generate random email
3. Follow prompts to complete registration

### 4. GitHub Action Automatic Registration ⚠️ [In Development]

1. Fork this project to your GitHub account
2. Get API KEY from [moemail](https://github.com/beilunyang/moemail)
3. Configure GitHub Secrets:
   - Go to project settings -> Secrets and variables -> Actions
   - Add `API_KEY` secret with your API KEY
   - Add `MOE_MAIL_URL` secret with moemail service URL
4. Trigger registration:
   - Go to Actions tab
   - Select `Register Account` workflow
   - Click "Run workflow"
   - Enter `DOMAIN` value in popup
5. Use generated account:
   - Download account info from Artifacts
   - Fill info into registration assistant
   - Click "Refresh cookie" to complete

> ⚠️ Note: This feature is under development
> - Recommended to deploy your own moemail service
> - Download and delete account info from Artifacts promptly
> - Store generated token securely

## FAQ ❓

### 1. Temporary Email vs Own Domain?

| Method | Pros | Cons |
|--------|------|------|
| Temporary Email | Quick & Easy | May be blocked |
| Own Domain | Stable & Reliable | Requires setup |

### 2. Registration Failure Solutions

- Try different temporary email services
- Switch to own domain method
- Check network connection

### 3. Manual Cookie Retrieval

1. Open browser developer tools (F12)
2. Visit cursor.sh and login
3. Find Cookie in Network tab
4. Copy and update in program

## 🤝 Community

<div align="center">
<table>
<tr>
<td>
<img src="assets/wx_20250215215655.jpg" width="300" height="450" alt="Join Community">
</td>
<td>

### Scan to Join Community
- Get latest updates
- Solve usage issues
- Share experiences
- Discuss technical topics

</td>
</tr>
</table>
</div>

## Detailed Tutorial 📖

Visit [Cursor Registration Assistant Usage Guide](https://www.ktovoz.com/blog/%E6%95%99%E5%AD%A6/Cursor%E6%B3%A8%E5%86%8C%E5%8A%A9%E6%89%8B%E9%A3%9F%E7%94%A8%E6%8C%87%E5%8D%97) for complete tutorial.

## Acknowledgments 🙏

Thanks to these open source projects:

- [cursor-auto-free](https://github.com/chengazhen/cursor-auto-free)
- [go-cursor-help](https://github.com/yuaotian/go-cursor-help)
- [CursorRegister](https://github.com/JiuZ-Chn/CursorRegister)
- [moemail](https://github.com/beilunyang/moemail)

## 📜 License and Disclaimer

<table>
<tr>
<td width="70%">

### License
This project is licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)

✅ Allowed:
- Share — copy and redistribute the material in any medium or format

❌ Not Allowed:
- Commercial use
- Modifications
- Redistribution

</td>
<td width="30%">

### ⚠️ Disclaimer
- For learning only
- No commercial use
- Use at own risk
- Author not liable

</td>
</tr>
</table>

---

<div align="center">

**[⬆ Back to Top](#cursor-registration-assistant-)**

</div> 