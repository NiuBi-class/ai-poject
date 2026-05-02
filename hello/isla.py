import set
import tkinter as tk 
from tkinter import ttk, scrolledtext
import voice
from openai import OpenAI


# --- 1. 系統啟動提示 ---
print("ai")

# OpenRouter 設定
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="你的api key",
)

root = tk.Tk()
root.state("zoomed")
root.title("ai")

# --- UI 佈局 ---
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

right_frame = tk.Frame(root, width=250, bg="#f0f0f0")
right_frame.pack(side=tk.RIGHT, fill=tk.Y)

# 情緒條佈置
def create_stat_bar(parent, label_text):
    tk.Label(parent, text=label_text, font=("微軟正黑體", 12), bg="#f0f0f0").pack(pady=(20,0))
    bar = ttk.Progressbar(parent, length=180, maximum=100)
    bar.pack(pady=5)
    return bar

happy_bar = create_stat_bar(right_frame, "開心 😊")
sad_bar = create_stat_bar(right_frame, "傷心 😢")
angry_bar = create_stat_bar(right_frame, "生氣 💢")
peace_bar = create_stat_bar(right_frame, "平靜 🍃")

def update_bars():
    happy_bar["value"] = set.status.get("開心", 50)
    sad_bar["value"] = set.status.get("傷心", 0)
    angry_bar["value"] = set.status.get("生氣", 0)
    peace_bar["value"] = set.status.get("平靜", 50)

update_bars()

emotion_label = tk.Label(right_frame, text="情緒：讀取中...", font=("微軟正黑體", 16, "bold"), bg="#f0f0f0")
emotion_label.pack(pady=30)

chat_window = scrolledtext.ScrolledText(left_frame, width=100, height=35, font=("微軟正黑體", 12))
chat_window.pack(padx=20, pady=20)

input_frame = tk.Frame(left_frame)
input_frame.pack(fill=tk.X, padx=20)

entry = tk.Entry(input_frame, font=("微軟正黑體", 14))
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

# --- 核心邏輯 ---

def send():
    message = entry.get()
    if not message: return
    
    # 顯示玩家的話
    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, f"【你】：{message}\n", "user_color")
    chat_window.tag_config("user_color", foreground="blue")

    # 準備呼叫 AI (傳入目前心情值)
    current_happiness = set.status.get("開心", 50)
    chat_order = set.personal(current_happiness, message)
    
    try:
        response = client.chat.completions.create(**chat_order)
        full_content = response.choices[0].message.content
        set.memory.append({"role": "assistant", "content": full_content})
        
        # 解析情緒數據
        lines = full_content.splitlines()
        
        # 抓取數值與標籤 (假設 AI 遵守格式)
        try:
            set.status["開心"] = int(lines[0].split("：")[-1].strip())
            set.status["傷心"] = int(lines[1].split("：")[-1].strip())
            set.status["生氣"] = int(lines[2].split("：")[-1].strip())
            set.status["平靜"] = int(lines[3].split("：")[-1].strip())
            emotion_cn = lines[4].split("：")[-1].strip()
            reply = lines[6].strip() if len(lines) > 6 else full_content
            emotion_cn = set.normalize_emotion_label(
                emotion_cn,
                set.status["開心"],
                set.status["傷心"],
                set.status["生氣"],
                set.status["平靜"],
            )
        except:
            emotion_cn = "平靜"
            reply = full_content

        # --- 情緒標籤輸出至文字檔 ---
        emotion_map = {
            # 開心類 (Happy)
            "開心": "happy", "感動": "happy", "撒嬌": "happy", "驚訝": "happy", "害羞": "happy",
            
            # 傷心/委屈類 (Sad)
            "傷心": "sad", "委屈": "sad",  "疲憊": "sad", "緊張": "sad",
            
            # 生氣/緊張類 (Mad)
            "生氣": "mad", "嫉妒": "mad",   "火大": "mad",
            
            # 平靜類 (Chill)
            "平靜": "chill", "無聊": "chill", "思考": "chill", "冷淡": "chill"
        }
        led_tag = emotion_map.get(emotion_cn, "chill")
        # 寫入設定檔資料夾中的 aila_mood.txt
        try:
            with open("setting/aila_mood.txt", "w", encoding="utf-8") as f:
                f.write(led_tag)
            print(f">>> ai目前心情標籤：{led_tag}")
        except Exception as file_err:
            print(f"寫入心情檔失敗: {file_err}")

    except Exception as e:
        print(f"API 呼叫失敗: {e}")
        emotion_cn = "思考中"
        reply = "（ai似乎在斷網的邊緣...）"

    # 更新 UI
    update_bars()
    emotion_label.config(text=f"情緒：{emotion_cn}")
    
    chat_window.insert(tk.END, f"【ai】：{reply}\n\n", "aila_color")
    chat_window.tag_config("aila_color", foreground="#d63384")

    chat_window.config(state=tk.DISABLED)
    entry.delete(0, tk.END)
    chat_window.see(tk.END)
    
    set.save_memory()
    set.save_status()
    full_content = response.choices[0].message.content
    print("=== AI 回傳 ===")
    print(full_content)
    print("===============")

def voice_send():
    text = voice.listen()
    if text:
        entry.delete(0, tk.END)
        entry.insert(0, text)
        send()

# 按鈕與綁定
send_button = tk.Button(input_frame, text="傳送", command=send, font=("微軟正黑體", 12), width=10)
send_button.pack(side=tk.LEFT)
voice_button = tk.Button(input_frame, text="🎤", command=voice_send, font=("", 12), width=5)
voice_button.pack(side=tk.LEFT, padx=5)

entry.bind("<Return>", lambda event: send())

def on_close():
    set.save_memory()
    set.save_status()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()