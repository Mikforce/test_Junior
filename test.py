import requests

response = requests.get("https://jservice.io/api/random?count=1")

if response.status_code == 200:
    json_data = response.json()
    if json_data:
        question = json_data[0]['question']
        print(question)
    else:
        print("No data available")
else:
    print("Request failed with status code:", response.status_code)