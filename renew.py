import os, sys, time, urllib.request, subprocess, json
import speech_recognition as sr
from seleniumbase import SB

# ==========================================
# 💡 核心配置
# ==========================================
TARGET_URL = "https://game4free.net/fbrav"
# 支持从环境变量读取，如果没有则默认使用 "ghjop8"
MC_USERNAME = os.getenv("MC_USERNAME", "ghjop8")

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")
MAX_RETRIES = 50  # 最大换 IP 重试次数

def send_tg(msg):
    if TG_TOKEN and TG_CHAT:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": TG_CHAT, "text": f"🤖 G4F 自动续期:\n{msg}"}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=10)
        except:
            pass

def restart_warp():
    """执行系统命令重启 WARP 以更换 IP"""
    print("🔄 正在断开 WARP...")
    subprocess.run(['warp-cli', '--accept-tos', 'disconnect'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    
    print("🔄 正在重新连接 WARP 以获取新 IP...")
    subprocess.run(['warp-cli', '--accept-tos', 'connect'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("⏳ 等待 WARP 隧道建立并分配新 IP (10秒)...")
    time.sleep(10)
    
    print("🌍 检查当前新 IP:")
    os.system("curl -s -x socks5://127.0.0.1:40000 https://api.ipify.org || echo '⚠️ IP获取失败'")
    print("\n")

print(f"\n===== 🚀 开始执行极速续期 (WARP 换 IP 强力抗封锁版) =====")

# 🌟 必须加回来：指定本地 WARP SOCKS5 代理
proxy_str = "socks5://127.0.0.1:40000"

for attempt in range(1, MAX_RETRIES + 1):
    print(f"\n=========================================")
    print(f"   🔄 第 {attempt}/{MAX_RETRIES} 次尝试续期")
    print(f"=========================================")
    
    success = False
    
    with SB(uc=True, proxy=proxy_str, headless=False) as sb:
        try:
            print("🌐 正在通过 WARP SOCKS5 代理访问目标...")
            sb.open(TARGET_URL)
            sb.sleep(2)

            print("🛡️ 锁定 reCAPTCHA 框架...")
            sb.switch_to_frame('iframe[title*="reCAPTCHA"]')
            
            print("🖱️ 点击人机验证复选框...")
            sb.wait_for_element('.recaptcha-checkbox-border', timeout=15)
            sb.click('.recaptcha-checkbox-border')
            sb.sleep(4)

            sb.switch_to_default_content()
            sb.switch_to_frame('iframe[title*="reCAPTCHA"]')
            is_checked = sb.get_attribute('#recaptcha-anchor', 'aria-checked')
            
            if is_checked == 'true':
                print("⏩ 运气爆表！IP 干净，验证码秒过。")
            else:
                print("⚠️ 触发挑战，正在尝试通过音频破解...")
                sb.switch_to_default_content()
                sb.switch_to_frame('iframe[title*="recaptcha challenge"]')

                if sb.is_element_visible('#recaptcha-audio-button'):
                    sb.click('#recaptcha-audio-button')
                    sb.sleep(3)

                    if sb.is_text_visible("Try again later"):
                        print("❌ 抽到“黑人” IP，Google 拒绝下发音频。")
                        raise Exception("IP Blocked: Try again later") # 主动触发异常进入重试
                    else:
                        print("📥 正在抓取音频数据流...")
                        audio_src = None
                        if sb.is_element_visible('#audio-source'):
                            audio_src = sb.get_attribute('#audio-source', 'src')
                        elif sb.is_element_visible('.rc-audiochallenge-tdownload-link'):
                            audio_src = sb.get_attribute('.rc-audiochallenge-tdownload-link', 'href')

                        if audio_src:
                            urllib.request.urlretrieve(audio_src, 'payload.mp3')
                            subprocess.run(['ffmpeg', '-i', 'payload.mp3', 'payload.wav', '-y'], 
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                            print("🧠 AI 正在解析语音内容...")
                            r = sr.Recognizer()
                            with sr.AudioFile('payload.wav') as source:
                                audio_data = r.record(source)
                            try:
                                text = r.recognize_google(audio_data)
                                print(f"✅ 识别成功: [{text}]")
                                
                                sb.type('#audio-response', text)
                                sb.click('#recaptcha-verify-button')
                                sb.sleep(4)
                            except sr.UnknownValueError:
                                print("❌ 引擎无法识别音频内容。")
                                raise Exception("Audio recognition failed")
                            except sr.RequestError as e:
                                print(f"❌ 语音引擎请求错误: {e}")
                                raise Exception("Audio engine request error")
                        else:
                            print("❌ 未能获取到音频链接。")
                            raise Exception("Audio link not found")
                else:
                    print("❌ 当前 IP 无法加载音频，可能被 Google 临时屏蔽。")
                    raise Exception("Audio button not found")
            
            # 验证结束，彻底切回最外层，准备填表单
            sb.switch_to_default_content()
            print(f"✍️ 填入服务器名: {MC_USERNAME}")
            
            # 填入用户名
            sb.wait_for_element('input[type="text"]', timeout=10)
            sb.type('input[type="text"]', MC_USERNAME)

            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot(f"screenshots/1_filled_att_{attempt}.png")

            print("🚀 提交续期请求...")
            sb.wait_for_element('#submit-button', timeout=10)
            sb.js_click('#submit-button') 
            print("🖱️ 成功执行模拟点击 Renew 按钮！")
            
            print("⏳ 等待服务器响应...")
            sb.sleep(5)
            sb.save_screenshot(f"screenshots/2_result_att_{attempt}.png")

            if sb.is_text_visible("The server has been renewed.") or sb.is_text_visible("renewed"):
                print("🎉 读取到成功提示: The server has been renewed.")
                print("✅ 续期大成功！")
                send_tg(f"✅ 服务器 [{MC_USERNAME}] 续期成功！\n(于第 {attempt} 次更换 WARP IP 后成功)")
                success = True
            else:
                print("⚠️ 按钮已点，但未读取到成功横幅。视作失败并准备重试。")
                raise Exception("Success message not found")

        except Exception as e:
            print(f"❌ 本次尝试发生致命错误或 IP 受限: {e}")
            os.makedirs("screenshots", exist_ok=True)
            try:
                sb.save_screenshot(f"screenshots/error_att_{attempt}.png")
            except:
                pass

    # ================= 判断是否成功，决定是否循环 =================
    if success:
        print("🎉 任务最终完成，退出轮询脚本。")
        break  # 成功，跳出最多 50 次的循环
    else:
        if attempt < MAX_RETRIES:
            print(f"⚠️ 本次任务失败，准备断开并重新连接 WARP 以更换 IP...")
            restart_warp()
        else:
            print("❌ 已经达到了最大重试次数 (50次)，彻底放弃。")
            send_tg(f"❌ 自动续期崩溃：已重试更换 IP 50 次，均未能成功。")
