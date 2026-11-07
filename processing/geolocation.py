import requests as http

from requests import Response

def geolocation(ip):
    response = http.get("https://ipinfo.io/"+ip+"/json")
    if response.status_code == 200:
        print(response.json())
        
if __name__ == '__main__':
    print(geolocation("88.147.152.239"))
    