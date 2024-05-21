
import browser_cookie3
import requests
import asyncio


def extract_cookies(choice=None):
    # Call once to get cookies for github.com from your browser sign in
    if choice == None:
        while True:
            ans = input(
                "What browser are you signed into github.com with? (Only tested with firefox on linux)\n1) Firefox\n2) Chrome\n3) Chromium\n4) Brave")
            try:
                choice = int(ans)
            except:
                print("Please enter a valid number")
                continue
            if choice == 0 or choice > 4:
                print("Please enter a valid number")
                continue
            break

    cookiejar = None
    match choice:
        case 1:
            cookiejar = browser_cookie3.firefox(domain_name='github.com')
        case 2:
            cookiejar = browser_cookie3.chrome(domain_name='github.com')
        case 3:
            cookiejar = browser_cookie3.chromium(domain_name='github.com')
        case 4:
            cookiejar = browser_cookie3.brave(domain_name='github.com')
    return cookiejar


# once you've called get_cookies, can access github uploaded assets
def get_authorized_resource(path, cookiejar):
    resp = requests.get(path, cookies=cookiejar)
    return resp
