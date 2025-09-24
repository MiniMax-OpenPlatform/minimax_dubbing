"""
本示例用于快速克隆。注意：需要先将密钥信息写入环境变量 `MINIMAX_API_KEY`
"""
import requests
import json
import os

api_key = os.getenv("MINIMAX_API_KEY")
url = 'https://api.minimaxi.com/v1/voice_clone'

payload = json.dumps({
  "file_id": <file_id of cloned voice>,
  "voice_id": "<voice_id>",
  "clone_prompt":{
    "prompt_audio": <file_id of the prompt audio>,
    "prompt_text": "这个声音效果挺自然的，听起来很舒服。",
  },
  "text":"微风拂过柔软的草地，清新的芳香伴随着鸟儿的歌唱。",
  "model":"speech-2.5-hd-preview",
  "accuracy": 0.7,
  "need_noise_reduction": False,
  "need_volumn_normalization": False,
  "aigc_watermark": False,
})
headers = {
  'Authorization': f'Bearer {api_key}',
  'content-type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

