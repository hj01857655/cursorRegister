# 🎯 Cursor Registration Assistant

<div align="center">

[🌍 English Version](./README_EN.md) | [🇨🇳 中文版](./README.md)

> 🚀 A tool to help you easily use Cursor with multiple registration methods and simple, convenient operations.
>
> 💫 Making registration simple and elegant

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
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-download-and-installation">Download & Installation</a> •
  <a href="#-how-to-use">How to Use</a> •
  <a href="#-roadmap">Roadmap</a> •
  <a href="#-registration-methods">Registration Methods</a> •
  <a href="#-contribution-guide">Contribution Guide</a> •
  <a href="#-faq">FAQ</a> •
  <a href="#-wechat-group">WeChat Group</a> •
  <a href="#detailed-tutorial-">Detailed Tutorial</a> •
  <a href="#-acknowledgments">Acknowledgments</a>
  </b>
</p>

<div align="center">

```shell
🎉 Making Cursor registration simple and elegant 🎉
```

</div>

---

<div align="center">

## ⚡ Quick Start

</div>

### 🌟 Core Features

- 🚀 Fully automated registration process
- 📧 Multiple email configuration options
- 🔒 Secure and reliable account management
- 🎨 Clean and elegant interface
- 🔄 Smart automatic update protection
- 🌐 Multi-platform compatibility
- ⚙️ Flexible configuration options

### 📋 System Requirements

- 💻 Windows OS
- 🎯 Cursor v0.44.11
- 🐍 Python 3.7+
- 🌐 Stable internet connection
- 📮 Available email service

<div align="center">

## 📥 Download and Installation

</div>

<details>
<summary><b>🖥️ Cursor Editor</b></summary>

### Windows Version (v0.44.11)

- 🔗 [Official Download](https://downloader.cursor.sh/builds/250103fqxdt5u9z/windows/nsis/x64)
-
🔄 [Alternative Download](https://download.todesktop.com/230313mzl4w4u92/Cursor%20Setup%200.44.11%20-%20Build%20250103fqxdt5u9z-x64.exe)

</details>

<details>
<summary><b>🛠️ Registration Assistant</b></summary>

- 📦 [Download from Release Page](https://github.com/ktovoz/cursorRegister/releases)

> 💡 Please download the latest version for the best experience

</details>

<div align="center">

## 🗺️ Roadmap

</div>

### 🎯 Current Goals

- 🚀 Optimize automatic registration success rate
- 🤖 Use GitHub Actions for automatic registration
- 🎨 Improve user interface experience
- 📝 Enhance documentation

### ✅ Implemented Features

- 💫 Fully automatic registration process
- 🔒 Seamless cookie refresh for software login
- 📧 Multiple registration methods: semi-automatic, fully automatic, manual
- 💰 Trial quota query
- 🎯 Registration assistance
- 🔄 Machine ID reset
- 🎨 Clean interface
- 📦 One-click packaging and release
- 💾 Account backup functionality
- 🔄 Batch account management
- 🔁 Support switching accounts using long-term token

### 🔮 Future Plans

- 🔄 Batch account management

> 💡 Roadmap will be adjusted based on community feedback and actual needs

<div align="center">

## 🎯 How to Use

</div>

### 🔰 Preparation

#### 📧 Email Configuration (Choose One)

<table>
<tr>
<th>Type</th>
<th>Configuration Steps</th>
<th>Advantages</th>
</tr>
<tr>
<td>

**📨 Temporary Email**
*(Quick & Easy)*

</td>
<td>

1. Visit temporary email service
2. Get temporary email address
3. Ensure verification emails can be received

</td>
<td>

- ⚡ Ready to use
- 🆓 Completely free
- 🔄 Easy to change

</td>
</tr>
<tr>
<td>

**🌐 Own Domain**
*(Recommended)*

</td>
<td>

1. Prepare a domain
2. Cloudflare Configuration:
    - DNS records setup
    - Email forwarding rules

</td>
<td>

- 🔒 Higher security
- ♾️ Permanent availability
- 🎛️ Full control

</td>
</tr>
</table>

<div align="center">

## 🎯 Registration Methods

</div>

### 🌈 Supported Registration Methods

### 1️⃣ Fully Automatic Registration

Recommended for beginners

<details>
<summary><b>📝 Detailed Steps</b></summary>

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

</details>

### 2️⃣ Manual Registration

Supports multiple email solutions

<details>
<summary><b>📝 Detailed Steps</b></summary>

1. Choose email solution:

   **Option A: Temporary Email**
    - Visit temporary email service website
    - Get a temporary email address
    - ⚡ Pros: Quick and easy
    - ⚠️ Cons: May be blocked

   **Option B: Own Domain**
    - Prepare a domain
    - Configure DNS records
    - Set up email forwarding rules
    - 🔒 Pros: Stable and reliable
    - ⚙️ Cons: Requires configuration

2. Start registration process:
    - Open registration assistant
    - Fill in domain
    - Generate random email and password
    - Choose verification method
    - Click "Auto Register"

3. Choose verification method:
    - 🤖 Automatic verification: Software automatically passes CAPTCHA
    - 👨‍💻 Manual verification: Manually pass CAPTCHA
   > 💡 Note: Both methods require manual email verification code input

4. Complete verification:
    - Wait for verification code
    - Complete verification based on chosen method
    - Wait for registration completion

5. Save account information

</details>

### 3️⃣ GitHub Action

⚠️ Under development

<details>
<summary><b>📝 Detailed Steps</b></summary>

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

> ⚠️ Notes:
> - Recommended to deploy your own moemail service
> - Download and delete account info from Artifacts promptly
> - Store generated token securely

</details>

### ⭐ Usage Recommendations

<details>
<summary><b>📝 How to Choose?</b></summary>

#### 🔰 For Beginners

- Choose fully automatic registration
- Convenient and quick, one-click completion
- ⚠️ Requires moemail deployment configuration

#### 🎯 For Stability

- Choose manual registration
- Most stable and reliable
- No additional configuration needed

#### 🔄 For Batch Requirements

- Wait for GitHub Action feature
- Can achieve automated batch registration

</details>
## 🤝 Contribution Guide

</div>

### 🌟 How to Contribute

We warmly welcome and appreciate all forms of contributions! Here are some ways to participate:

- 🐛 Submit bug reports
- 💡 Suggest new features
- 📝 Improve documentation
- ⚙️ Provide code contributions
- 🌍 Help with translations
- 💬 Answer other users' questions

### 📋 Contribution Steps

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

> 💡 **PRs are welcome!** If you have any ideas for improvement, we look forward to your contribution.
<div align="center">

## 🎯 FAQ

</div>

<details>
<summary><b>💡 Temporary Email vs Own Domain?</b></summary>

|       Method       |         Pros         |       Cons        |
|:------------------:|:--------------------:|:-----------------:|
| 📨 Temporary Email |    ⚡ Quick & Easy    | ⚠️ May be blocked |
|   🌐 Own Domain    | 🔒 Stable & Reliable | ⚙️ Requires setup |

</details>

<details>
<summary><b>🔧 Registration Failure Solutions</b></summary>

- 🔄 Try different temporary email services
- 🌐 Switch to own domain method
- 📡 Check network connection

</details>

<details>
<summary><b>🍪 Manual Cookie Retrieval</b></summary>

1. 🔍 Open browser developer tools (F12)
2. 🌐 Visit cursor.sh and login
3. 🔎 Find Cookie in Network tab
4. 📋 Copy and update in program

</details>

<details>
<summary><b>🔄 How to Switch Accounts</b></summary>

1. Select an account from the account list
2. Ensure the account has a long-term token (TOKEN)
   - If there's no long-term token, click "Update Info" first to obtain one
3. Click the "Switch Account" button
4. Wait for the system to process, and a success message will appear when completed
5. Now the Cursor application will use the selected account's identity

> 💡 The account switching feature uses a long-term token, allowing you to switch Cursor accounts without having to log in again, which is very convenient.

</details>

<div align="center">

## 🤝 WeChat Group

</div>

<div align="center">
<table>
<tr>
<td align="center">
<img src="assets/wx_20250215215655.jpg" width="280" height="420" alt="WeChat Group">
</td>
<td>

### 🌟 Join WeChat Group

- 📱 Scan QR code to join WeChat group
- 💬 Share experiences with other users
- ❓ Get help with usage issues
- 📢 Receive latest updates and information

#### Scan the QR code on the left to join our WeChat group!

</td>
</tr>
</table>
</div>

<div align="center">

## Detailed Tutorial 📖

</div>

Visit [Cursor Registration Assistant Usage Guide](https://www.ktovoz.com/blog/%E6%95%99%E5%AD%A6/Cursor%E6%B3%A8%E5%86%8C%E5%8A%A9%E6%89%8B%E9%A3%9F%E7%94%A8%E6%8C%87%E5%8D%97)
for complete tutorial.

<div align="center">

## 🌟 Acknowledgments

</div>

### 👥 Project Contributors

Thanks to all contributors who make this project better!

<div align="center">
<a href="https://github.com/ktovoz/cursorRegister/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ktovoz/cursorRegister&max=100" />
</a>
</div>

### 🏆 Special Thanks

Thanks to the following open-source projects and their authors for providing inspiration and reference:

<div align="center">
<table>
<tr>
<td align="center">
<a href="https://github.com/Ktovoz">
<img src="https://github.com/Ktovoz.png" width="100px;" alt="Ktovoz"/><br/>
<sub><b>Ktovoz</b></sub><br/>
<sub><a href="https://github.com/Ktovoz/cursorRegister"> cursorRegister</a></sub><br/>
</a>
</td>
<td align="center">
<a href="https://github.com/chengazhen">
<img src="https://github.com/chengazhen.png" width="100px;" alt="chengazhen"/><br/>
<sub><b>chengazhen</b></sub><br/>
<sub><a href="https://github.com/chengazhen/cursor-auto-free">cursor-auto-free</a></sub><br/>
</a>
</td>
<td align="center">
<a href="https://github.com/yuaotian">
<img src="https://github.com/yuaotian.png" width="100px;" alt="yuaotian"/><br/>
<sub><b>yuaotian</b></sub><br/>
<sub><a href="https://github.com/yuaotian/go-cursor-help">go-cursor-help</a></sub><br/>
</a>
</td>
<td align="center">
<a href="https://github.com/JiuZ-Chn">
<img src="https://github.com/JiuZ-Chn.png" width="100px;" alt="JiuZ-Chn"/><br/>
<sub><b>JiuZ-Chn</b></sub><br/>
<sub><a href="https://github.com/JiuZ-Chn/CursorRegister">CursorRegister</a></sub><br/>
</a>
</td>
<td align="center">
<a href="https://github.com/beilunyang">
<img src="https://github.com/beilunyang.png" width="100px;" alt="beilunyang"/><br/>
<sub><b>beilunyang</b></sub><br/>
<sub><a href="https://github.com/beilunyang/moemail">moemail</a></sub><br/>
</a>
</td>
</tr>
</table>
</div>

<div align="center">

## 📜 License and Disclaimer

</div>

### 📋 License

This project is licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)

#### ✅ You can:

- 📤 Share — copy and redistribute the material in any medium or format

#### ❌ But you cannot:

- 💰 Use commercially
- ✏️ Modify the original work
- 🔄 Redistribute

### ⚠️ Disclaimer

- 📚 For learning only
- 🚫 No commercial use
- ⚖️ Use at own risk
- 🔒 Author not liable

---

<div align="center">

**[⬆ Back to Top](#-cursor-registration-assistant)**

<br/>

<sub>Made with ❤️ | Copyright © 2025 ktovoz</sub>

</div>

