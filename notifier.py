import requests
import base64
import xmltodict
import json
import smtplib
import os
from email.message import EmailMessage

baseurl = "https://[yoururl].jamfcloud.com/"
url = baseurl+"JSSResource/"
testurl = baseurl+"test.jamfcloud.com/JSSResource"

computers = "computers"
patchtitles = "patchsoftwaretitles"
patchreports = "patchreports/patchsoftwaretitleid/"
token = "beep"



def parsepc(title, install, new):
    return {
        "name": title["patch_report"]["name"],
        "installver": install["software_version"],
        "newver": new
        }

def managepcnotify(pcnotify, pc, pcid):
    if pcid in pcnotify:
        pcnotify[pcid].append(pc)
    else:
        pcnotify[pcid] = [pc]   

def sendmail(msgcontents):
    #smtpuser = os.environ["SMTPUSER"]
    #smtppass = os.environ["SMTPPASS"]
    smtpserv = "[your.mailserver.your.tld]"
    smtpobj = smtplib.SMTP(smtpserv, 587)
    smtpobj.starttls()
    # uncomment this for authenticated SMTP
    # smtpobj.login(smtpuser,smtppass)
    smtpobj.send_message(msgcontents)
    smtpobj.quit()

def gettoken():
    username = os.environ["JAMFREPORTUSER"]
    pwd = os.environ["JAMFREPORTPASS"]

    tokenurl = baseurl+"/api/v1/auth/token"
    
    credential = F"{username}:{pwd}"
    cred64 = base64.b64encode(credential.encode("utf-8"))
    
    headers = {"Accept": "application/json", "Authorization": F"Basic {str(cred64, 'utf-8')}"}

    response = requests.request("POST", url, headers=headers)
    return json.loads(response.text)["token"]
    

def main():
    patchids = webrequest(url, patchtitles) 
    #print(json.dumps(patchids))

    pcnotify = dict()
    print("Checking patches")
    for patch in patchids["patch_software_titles"]["patch_software_title"]:
        swtitle = webrequest(url, patchreports+patch["id"])
        #print(json.dumps(swtitle))
        for idx, version in enumerate(swtitle["patch_report"]["versions"]["version"]):
            #print(json.dumps(version))
            if idx == 0:
                currentver = version["software_version"]
                continue
            pccount = version["computers"]["size"]
            if pccount == "1":
                managepcnotify(pcnotify, parsepc(swtitle, version, currentver), version["computers"]["computer"]["id"])
            elif pccount != "0":
                for pc in version["computers"]["computer"]:
                    managepcnotify(pcnotify, parsepc(swtitle, version, currentver), pc["id"])
    print("Composing emails")
    for key in pcnotify.keys():
        formatsendmail(key, pcnotify[key])
    print("Done!")
    

def formatsendmail(pcid, patches):
    computerinfo = webrequest(url, computers+"/id/"+pcid)
    #print(json.dumps(computerinfo))
    emailaddr = computerinfo["computer"]["location"]["email_address"]
    #emailaddr = YOUR_EMAIL
    fullname = computerinfo["computer"]["location"]["realname"]
    pcname = computerinfo["computer"]["general"]["name"]
    email = EmailMessage()
    email['from'] = "[your email]"
    email['to'] = emailaddr
    email['subject'] = 'Action Needed: Please Patch Your Mac! (Automated)'
    mailtext = F'Hi {fullname}!\nYour Mac, {pcname} needs these applications to be updated:\n\n'
    #print(mailtext)
    for patch in patches:
        mailtext += (F'    - {patch["name"]} has been updated to {patch["newver"]}, you have {patch["installver"]} installed!\n')
    mailtext += (F'\nIf you have any questions about how to update these, please reach out to the IT Team!\n\n-ReportBot via Jamf Pro!')
    email.set_content(mailtext)
    #print("----------------")
    #print(email)
    sendmail(email)

 



def webrequest(uri, endpoint):
    headers = {"Accept": "application/xml", "Authorization": F"Bearer {token}"}
    response = requests.request("GET", uri+endpoint, headers=headers)
    return xmltodict.parse(response.text)



if __name__ == "__main__":
    token = gettoken()
    main()