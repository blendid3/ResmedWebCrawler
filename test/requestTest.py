import requests
website = "http://127.0.0.1:5000/"
response = requests.get(website + "12");
print(response.json())