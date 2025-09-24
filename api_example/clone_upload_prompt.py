url = f'https://api.minimaxi.com/v1/files/upload?GroupId={group_id}'
headers1 = {
    'authority': 'api.minimaxi.com',
    'Authorization': f'Bearer {api_key}'
}

data = {
    'purpose': 'prompt_audio'
}

files = {
    'file': open('prompt.mp3', 'rb')
}
response = requests.post(url, headers=headers1, data=data, files=files)
file_id = response.json().get("file").get("file_id")
print(file_id)

