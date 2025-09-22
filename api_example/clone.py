import requests
import json

group_id = "YOUR_GROUP_ID_HERE"
api_key = "YOUR_MINIMAX_API_KEY_HERE"


url = f'https://api.minimax.chat/v1/files/upload?GroupId={group_id}'
headers1 = {
    'authority': 'api.minimax.chat',
    'Authorization': f'Bearer {api_key}'
}
data = {
    'purpose': 'voice_clone'
}
files = {
    'file': open('./temp/input_audio.wav', 'rb')  # 将使用临时文件路径
}

response = requests.post(url, headers=headers1, data=data, files=files)
file_id = response.json().get("file").get("file_id")
print(file_id)
print(response.json())

#音频复刻
url = f"https://api.minimax.chat/v1/voice_clone?GroupId={group_id}"
payload2 = json.dumps({
  "file_id": file_id,
  "voice_id": "ectest006", ##请修改VoiceID
  "text": "你好啊", 
  "model":"speech-2.5-hd-preview",
  "language_boost":"Chinese,Yue", 
  "need_volumn_normalization": True
})
headers2 = {
  'authorization': f'Bearer {api_key}',
  'content-type': 'application/json'
}
response = requests.request("POST", url, headers=headers2, data=payload2)
print(response.text)