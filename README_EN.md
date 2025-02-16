# Cursor Registration Assistant

[中文版](./README.md)

> A tool to help you easily use Cursor

## 📥 Download Cursor

### Windows Version (v0.44.11)

- ⚡ [Official Cursor Download](https://downloader.cursor.sh/builds/250103fqxdt5u9z/windows/nsis/x64)

🔄 [ToDesktop Alternative Download](https://download.todesktop.com/230313mzl4w4u92/Cursor%20Setup%200.44.11%20-%20Build%20250103fqxdt5u9z-x64.exe)

### Registration Assistant Download

- 📦 [Download from Release Page](https://github.com/ktovoz/cursorRegister/releases)
  > Download the latest version of the registration assistant from the Release page

## 🔐 How to Use

### Preparation

#### 1️⃣ Download and Install

- Download the latest version of the registration assistant from the Release page
- Ensure Cursor v0.44.11 is installed

#### 2️⃣ Email Configuration (Choose One)

- **Option 1: Use Temporary Email** (Quick and Easy)
    - Use temporary email services (like temp-mail.org, 10minutemail.com, etc.)
    - Ensure you can access the temporary email to receive verification emails

- **Option 2: Use Your Own Domain** (Recommended for Long-term Use)
    1. Prepare an available domain (recommend using affordable domain registrars)
    2. Complete configuration on Cloudflare:
        - Add domain and configure DNS records
        - Enable and set up Cloudflare Email Routing

### Registration and Configuration Steps

#### 1️⃣ Account Registration Methods (Choose One)

##### Method 1: Software Fully Automatic Registration (Recommended for Beginners)
1. Get from [moemail](https://github.com/beilunyang/moemail) service:
    - API KEY
    - Available DOMAIN
2. Configure software:
    - Open .env file
    - Fill in `API_KEY=your_api_key`
    - Fill in `DOMAIN=your_domain`
3. Start registration:
    - Check "Fully Automatic Registration" option
    - Click "Auto Register" button
    - Wait for the program to complete registration process
> ⚠️ Note:
> - Ensure the API KEY and DOMAIN entered are valid
> - Manual CAPTCHA verification may be required during registration
> - The program will automatically configure all necessary information after successful registration

##### Method 2: GitHub Action Automatic Registration (Recommended for Advanced Users)
1. Fork this project to your GitHub account
2. Get API KEY from [moemail](https://github.com/beilunyang/moemail) project
3. Configure GitHub Secrets:
    - Go to project settings -> Secrets and variables -> Actions
    - Add a secret named `API_KEY` with the value of your obtained API KEY
    - Add a secret named `MOE_MAIL_URL` with the value of moemail service URL
4. Trigger registration process:
    - Go to Actions tab
    - Select `Register Account` workflow
    - Click "Run workflow"
    - Enter `DOMAIN` value in the popup dialog (domain obtained from moemail service)
5. Use generated account:
    - Download account information from Artifacts
    - Fill information into registration assistant program
    - Click "Refresh Cookie" to complete configuration
> ⚠️ Note:
> - It's recommended to deploy your own moemail service for stability
> - Promptly download and delete account information from Artifacts
> - Securely store the generated token

##### Method 3: Register with Temporary Email (Simple but Unstable)
1. Prepare temporary email address (like temp-mail.org, 10minutemail.com, etc.)
2. In the program:
    - Enter temporary email address
    - Check "Manual Verification" or "Auto Verification" option
    - Click "Auto Register" button
3. Verification steps:
    - Wait for registration email
    - Check verification code in temporary email
    - Manually enter verification code into program
    - Wait for registration to complete
> ⚠️ Note:
> - Some temporary email services may be blocked by Cursor
> - Ensure you can receive and enter verification code promptly
> - Verification codes have short validity periods, quick action required

##### Method 4: Register with Your Own Domain (Stable and Reliable)
1. Domain configuration:
    - Prepare an available domain
    - Configure DNS and email forwarding in Cloudflare
2. Registration process:
    - Click "Generate Account" to get random email and password
    - Check "Manual Verification" or "Auto Verification" option
    - Click "Auto Register" button
3. Verification steps:
    - Wait for registration email to be sent to domain email
    - Get verification code from forwarded email
    - Manually enter verification code into program
    - Wait for registration to complete
> ⚠️ Note:
> - Ensure domain email forwarding is configured correctly
> - Verification codes have short validity periods, check and enter promptly
> - If verification code not received, check email forwarding settings

#### 2️⃣ Login Credentials Configuration

After registration, the program will automatically:
- Get account Cookie information
- Fill Cookie into corresponding input field
- Update .env configuration file
- Click "Refresh Cookie" button to enable auto-login for local Cursor

#### 3️⃣ ID Reset and Update Protection

After registration completion:
- Click "Reset ID" button
- The program will automatically:
    - Reset device machine code
    - Disable auto-update function
    - Ensure normal account usage

### ⚙️ Additional Notes

- The program will automatically disable Cursor's auto-update function to prevent updates to unsupported new versions
- Recommend regularly backing up the .env configuration file in case reconfiguration is needed

### ❓ Frequently Asked Questions (FAQ)

#### 1. Why is using your own domain recommended over temporary email?

- Well-known temporary email services (like temp-mail.org, 10minutemail.com) may be blocked by Cursor, causing
  registration failure
- Your own domain can be used stably long-term and won't be identified as temporary email
- Using your own domain allows generating multiple random email accounts, providing more flexibility

#### 2. What to do if registration with temporary email fails?

- Try using less common temporary email services
- Recommend switching to own domain registration method, which is the most stable and reliable solution
- If you must use temporary email, try several different temporary email services

#### 3. What to do if auto-registration is unavailable?

- You can complete the registration process manually in browser
- After successful registration, get Cookie from browser developer tools:
    1. Open browser developer tools (F12)
    2. Go to Network tab
    3. Visit cursor.sh website and register/login
    4. Search for `WorkosCursorSessionToken` in requests to find request containing complete Cookie information
    5. Copy Cookie value
- Paste the obtained Cookie into the program
- Click "Update Account Info" button to update login information

## 📖 Detailed Tutorial

Semi-automatic registration is recommended.

A complete usage tutorial has been published at [Cursor Registration Assistant Usage Guide](https://www.ktovoz.com/blog/%E6%95%99%E5%AD%A6/Cursor%E6%B3%A8%E5%86%8C%E5%8A%A9%E6%89%8B%E9%A3%9F%E7%94%A8%E6%8C%87%E5%8D%97)

If you have any questions, you can join the group chat:

<img src="assets/wx_20250215215655.jpg" width="300" height="450" alt="Join Group Chat" style="float: left; margin-right: 20px;">

## 🙏 Acknowledgments

Special thanks to the following open source projects:

- [cursor-auto-free](https://github.com/chengazhen/cursor-auto-free)
- [go-cursor-help](https://github.com/yuaotian/go-cursor-help)
- [CursorRegister](https://github.com/JiuZ-Chn/CursorRegister)
- [moemail](https://github.com/beilunyang/moemail) - Provides stable and reliable temporary email service

## 📜 License and Disclaimer

### License

This project is licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/), which allows you
to:

- ✅ Share — copy and redistribute the material in any medium or format

With the following restrictions:

- ❌ No commercial use
- ❌ No modifications to the original work
- ✅ Must provide attribution to the original author

### Disclaimer

> ⚠️ Important Notice:
> - This project is for learning and communication purposes only, commercial use is strictly prohibited
> - Users are responsible for any consequences arising from using this project
> - The author is not responsible for any issues that may occur during use 