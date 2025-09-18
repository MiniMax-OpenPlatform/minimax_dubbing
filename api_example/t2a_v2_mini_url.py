import requests
import json

group_id = '1747179187841536150'
api_key = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLmnZzno4oiLCJVc2VyTmFtZSI6IuadnOejiiIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxNzQ3MTc5MTg3ODQ5OTI0NzU4IiwiUGhvbmUiOiIxMzAyNTQ5MDQyMyIsIkdyb3VwSUQiOiIxNzQ3MTc5MTg3ODQxNTM2MTUwIiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiZGV2aW5AbWluaW1heGkuY29tIiwiQ3JlYXRlVGltZSI6IjIwMjQtMTItMjMgMTE6NTE6NTQiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.szVUN2AH7lJ9fQ3EYfzcLcamSCFAOye3Y6yO3Wj_tlNhnhBIYxEEMvZsVgH9mgOe6uhRczOqibmEMbVMUD_1DqtykrbD5klaB4_nhRnDl8fbaAf7m8B1OTRTUIiqgXRVglITenx3K_ugZ6teqiqypByJoLleHbZCSPWvy1-NaDiynb7qAsGzN1V6N4BOTNza1hL5PYdlrXLe2yjQv3YW8nOjQDIGCO1ZqnVBF0UghVaO4V-GZu1Z_0JnkLa7x_2ZXKXAe-LWhk9npwGFzQfLL3aH4oUzlsoEDGnuz3RZdZsFCe95MUiG8dCWfsxhVqlQ5GoFM3LQBAXuLZyqDpmSgg'


url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"

payload = json.dumps({
  "model": "speech-01-turbo",
  "text": "师傅您好,我是小明",
  "language_boost":"Chinese",
  "output_format":"url",
  "voice_setting": {
    "voice_id": "male-qn-qingse",
    "speed": 1.2
  }

})
headers = {
  'Authorization': f'Bearer {api_key}',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)
parsed_json = json.loads(response.text)

# 先打印完整响应结构以便调试
print("完整响应:", json.dumps(parsed_json, indent=2, ensure_ascii=False))

# 检查响应状态
if 'data' in parsed_json and parsed_json['data'] and 'audio' in parsed_json['data']:
    audio_url = parsed_json['data']['audio']
    print(f"音频URL: {audio_url}")
    
          
    
    if 'trace_id' in parsed_json:
        print(f"trace_id: {parsed_json['trace_id']}")
    
    # 下载音频文件
    audio_response = requests.get(audio_url)
    with open('./temp/output_audio.mp3', 'wb') as f:
        f.write(audio_response.content)
        print("音频文件已保存到 ./temp/output_audio.mp3")
else:
    print("响应中未找到音频数据，请检查API参数或响应格式")
