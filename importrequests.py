import requests
import json
import base64
from getpass import getpass

def main():
    url = ""

    username = input("Username: ")
    pwd = getpass(prompt="Password: ", stream=None)

    url = "https://[yourURL].jamfcloud.com/api/v1/auth/token"
    
    credential = F"{username}:{pwd}"
    cred64 = base64.b64encode(credential.encode("utf-8"))
    
    headers = {"Accept": "application/json", "Authorization": F"Basic {str(cred64, 'utf-8')}"}

    response = requests.request("POST", url, headers=headers)

    print(response.text)
    
if __name__ == "__main__":
    main()
