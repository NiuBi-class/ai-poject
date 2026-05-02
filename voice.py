import speech_recognition as sr

recognizer = sr.Recognizer()

def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("請說話...")
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio, language="zh-TW")
        print(f"你說：{text}")
        return text
    except Exception as e:
        print(f"錯誤：{e}")
        return None
print(listen())