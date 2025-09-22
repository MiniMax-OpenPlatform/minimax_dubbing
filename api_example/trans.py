import requests
import json

# ===== 全局参数配置 =====
ORIGINAL_TEXT = ""  # 原文
CURRENT_TRANSLATION = "妈妈需要做肾透析，我们真的没钱了"  # 当前译文
TARGET_LANGUAGE = "中文"  # 目标语种
CURRENT_AUDIO_LENGTH = 3.5  # 当前音频长度（秒）
TARGET_AUDIO_LENGTH = 2.5  # 目标音频长度（秒）
CURRENT_CHAR_COUNT = len(CURRENT_TRANSLATION)  # 自动计算当前字符数
TARGET_CHAR_COUNT = int(CURRENT_CHAR_COUNT * TARGET_AUDIO_LENGTH / CURRENT_AUDIO_LENGTH)  # 自动计算目标字符数
# =========================

api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLmnZzno4oiLCJVc2VyTmFtZSI6IuadnOejiiIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzQ3MTc5MTg3ODQ5OTI0NzU4IiwiUGhvbmUiOiIxMzAyNTQ5MDQyMyIsIkdyb3VwSUQiOiIxNzQ3MTc5MTg3ODQxNTM2MTUwIiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiZGV2aW5AbWluaW1heGkuY29tIiwiQ3JlYXRlVGltZSI6IjIwMjQtMTItMjMgMTE6NTE6NTQiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.szVUN2AH7lJ9fQ3EYfzcLcamSCFAOye3Y6yO3Wj_tlNhnhBIYxEEMvZsVgH9mgOe6uhRczOqibmEMbVMUD_1DqtykrbD5klaB4_nhRnDl8fbaAf7m8B1OTRTUIiqgXRVglITenx3K_ugZ6teqiqypByJoLleHbZCSPWvy1-NaDiynb7qAsGzN1V6N4BOTNza1hL5PYdlrXLe2yjQv3YW8nOjQDIGCO1ZqnVBF0UghVaO4V-GZu1Z_0JnkLa7x_2ZXKXAe-LWhk9npwGFzQfLL3aH4oUzlsoEDGnuz3RZdZsFCe95MUiG8dCWfsxhVqlQ5GoFM3LQBAXuLZyqDpmSgg"

url = f"https://api.minimaxi.com/v1/text/chatcompletion_v2"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
  "model": "MiniMax-Text-01",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "system",
      "content": "你是一个翻译优化专家"
    },
    {
      "role":"user",
      "name":"用户", # 选填字段
      "content":f"你的任务是翻译优化，原文\"{ORIGINAL_TEXT}\"当前\"{TARGET_LANGUAGE}\"翻译\"{CURRENT_TRANSLATION}\"，你需要缩短翻译的文字，同时保持口语化表达，当前字符数是{CURRENT_CHAR_COUNT}个字，需要精简成少于{TARGET_CHAR_COUNT}个字，翻译如下："
      }
  ]
}

responst= requests.post(url, headers=headers, json=payload)

# 解析JSON响应并只打印翻译结果
try:
    response_data = response.json()
    if response.status_code == 200 and 'choices' in response_data:
        translation_result = response_data['choices'][0]['message']['content']
        print(translation_result)
    else:
        print(f"请求失败: {response.status_code}")
        print(response.text)
except json.JSONDecodeError:
    print("响应格式错误")
    print(response.text)
