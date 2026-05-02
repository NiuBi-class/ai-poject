import json
import datetime
model = "deepseek/deepseek-v3.2"

memory = []
try:
    with open(r"setting\memory.json", "r", encoding="utf-8") as f:
        memory = json.load(f)
    with open(r"setting\status.json", "r", encoding="utf-8") as f:
        status = json.load(f)
except:
    status = {
        "熟悉度": 0,
        "開心": 50,
        "傷心": 10,
        "生氣": 5,
        "平靜": 35,
        "上次聊天": "第一次聊天"
    }
    memory = []

def save_memory():
    with open(r"setting\memory.json", "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def save_status():
    with open(r"setting\status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

def compress_memory():
    global memory
    summaries = [m for m in memory if "[對話摘要" in m.get("content", "")]
    normal = [m for m in memory if "[對話摘要" not in m.get("content", "")]

    if len(normal) <= 30:
        return

    old_messages = normal[:10]
    memory = summaries + normal[10:]
    
    from openai import OpenAI
    compress_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="你的api key"
    )
    
    prompt = "以下是10筆對話，請把每一筆壓縮成一句話，格式是一行一句，共10句，不要加編號：\n"
    for msg in old_messages:
        prompt += f"{msg['role']}：{msg['content']}\n"
    
    compress_response = compress_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    summary = compress_response.choices[0].message.content
    now = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M')
    memory.insert(0, {"role": "system", "content": f"[對話摘要 {now}]：{summary}"})
    save_memory()

def dominant_mood_key(h, s, a, p):
    stats = {"開心": h, "傷心": s, "生氣": a, "平靜": p}
    mx = max(stats.values())
    for k in ("生氣", "傷心", "開心", "平靜"):
        if stats[k] == mx:
            return k

def normalize_emotion_label(emotion_cn, h, s, a, p):
    """依四軸數值校正情緒標籤，避免模型無視數字、一律填害羞。"""
    dominant = dominant_mood_key(h, s, a, p)
    allowed = {
        "開心": frozenset({"開心", "感動", "撒嬌", "驚訝"}),
        "傷心": frozenset({"傷心", "委屈", "疲憊", "緊張"}),
        "生氣": frozenset({"生氣", "嫉妒", "火大"}),
        "平靜": frozenset({"平靜", "無聊", "思考", "冷淡"}),
    }
    default = {"開心": "開心", "傷心": "傷心", "生氣": "生氣", "平靜": "平靜"}
    if emotion_cn in allowed[dominant]:
        return emotion_cn
    return default[dominant]

def cooling_down():
    # 每次對話時，讓極端情緒往「平靜」靠攏
    if status["生氣"] > 5: status["生氣"] -= 1
    if status["傷心"] > 5: status["傷心"] -= 1
    if status["平靜"] < 50: status["平靜"] += 1
    save_status()

# --- 重點修正：現在接收兩個參數了 ---
def personal(isla_happiness, user_message):
    # 0. 先執行情緒冷卻
    cooling_down()

    # 1. 讀取設定檔
    try:
        with open("setting/personal.txt", "r", encoding="utf-8") as f:
            text_personal = f.read()
        with open("setting/rule.txt", "r", encoding="utf-8") as f:
            text_rule = f.read()
        with open("setting/emotion.txt", "r", encoding="utf-8") as f:
            text_emotion = f.read()
    except FileNotFoundError:
        print("警告：設定檔缺失！")
        text_personal, text_rule, text_emotion = "你是艾拉", "", ""

    # 2. 記憶壓縮邏輯
    compress_memory()
    
    # 3. 準備時間與心情資訊
    now = datetime.datetime.now()
    last_chat = status.get("上次聊天", "很久以前")
    time_info = f"現在時間：{now.strftime('%Y年%m月%d日 %H:%M')}，上次聊天：{last_chat}"

    # 這裡使用傳入的 isla_happiness 讓 AI 知道它當下的狀態
    current_status_desc = (
        f"目前心情狀態：開心 {isla_happiness}, 傷心 {status['傷心']}, "
        f"生氣 {status['生氣']}, 平靜 {status['平靜']}。熟悉度：{status['熟悉度']}"
    )

    # 4. 構建 System Prompt
    system_prompt = (
        f"{text_personal}\n"
        f"你的行為準則：{text_rule}\n"
        f"情緒反應機制：{text_emotion}\n"
        f"{current_status_desc}\n"
        f"{time_info}\n"
        "請注意：回覆時必須包含情緒數值。如果提到重要事項，請標註 [重要]。"
    )

    # 5. 更新對話紀錄
    memory.append({"role": "user", "content": user_message}) 
    
    # 6. 更新上次聊天時間
    status["上次聊天"] = now.strftime('%Y年%m月%d日 %H:%M')
    save_status()
    
    brain_data = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + memory
    }
    
    return brain_data