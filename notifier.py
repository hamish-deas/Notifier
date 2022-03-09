import requests
import base64
import xmltodict
import json
import smtplib
import os
from email.message import EmailMessage

baseurl = "https://[yoururl].jamfcloud.com/" # candidate for config file (issue #2)
url = baseurl+"JSSResource/"

computers = "computers"
patchtitles = "patchsoftwaretitles"
patchreports = "patchreports/patchsoftwaretitleid/"

def gettoken():
    username = os.environ["JAMFREPORTUSER"]
    pwd = os.environ["JAMFREPORTPASS"]

    tokenurl = baseurl+"/api/v1/auth/token"

    credential = F"{username}:{pwd}"
    cred64 = base64.b64encode(credential.encode("utf-8"))

    headers = {"Accept": "application/json", "Authorization": F"Basic {str(cred64, 'utf-8')}"}
    response = requests.request("POST", tokenurl, headers=headers)
    print("Token acquired")
    return json.loads(response.text)["token"]

def webrequest(uri, endpoint):
    headers = {"Accept": "application/xml", "Authorization": F"Bearer {token}"}
    response = requests.request("GET", uri+endpoint, headers=headers)
    return xmltodict.parse(response.text)

def parsepc(title, install, new):
    return {
        "name": title["patch_report"]["name"],
        "installver": install["software_version"],
        "newver": new
        }

def managepcdefinition(pcdef, pc, pcid):
    if pcid in pcdef:
        pcdef[pcid].append(pc)
    else:
        pcdef[pcid] = [pc]   

def sendmail(msgcontents):
    # uncomment these for authenticated SMTP
    #smtpuser = os.environ["SMTPUSER"]
    #smtppass = os.environ["SMTPPASS"]
    smtpserv = "[your.mailserver.your.tld]" # candidate for config file (issue #2)
    smtpport = 587 # candidate for config file (issue #2)
    smtpobj = smtplib.SMTP(smtpserv, smtpport)
    smtpobj.starttls()
    # uncomment this for authenticated SMTP
    #smtpobj.login(smtpuser,smtppass)
    smtpobj.send_message(msgcontents)
    smtpobj.quit()

def formatsendmail(pcid, patches):
    computerinfo = webrequest(url, computers+"/id/"+pcid)
    # uncomment for a preview of what info is being pulled about each computer.  Probably too much info for debug mode (issue #3)
    #print(json.dumps(computerinfo))
    emailaddr = computerinfo["computer"]["location"]["email_address"]
    # uncomment to change the sending address to your email.  Good candidate for debug mode (issue #3)
    #emailaddr = YOUR_EMAIL
    fullname = computerinfo["computer"]["location"]["realname"]
    pcname = computerinfo["computer"]["general"]["name"]
    email = EmailMessage()
    email['from'] = "[your email]"
    email['to'] = emailaddr
    email['subject'] = 'Action Needed: Please Patch Your Mac! (Automated)'
    mailtext = F'Hi {fullname}!\nYour Mac, {pcname} needs these applications to be updated:\n\n'
    for patch in patches:
        mailtext += (F'    - {patch["name"]} has been updated to {patch["newver"]}, you have {patch["installver"]} installed!\n')
    mailtext += (F'\nIf you have any questions about how to update these, please reach out to the IT Team!\n\n-ReportBot via Jamf Pro!')
    email.set_content(mailtext)
    # uncomment to see a preview of the emails before they go out.  Good candidate for debug mode (issue #3)
    #print("----------------")
    #print(email)
    sendmail(email)

def main():
    patchids = webrequest(url, patchtitles) 
    # uncomment this to see a list of all the patche reporting titles.  Probably too much info for debug mode (issue #3)
    #print(json.dumps(patchids))
    pcdef = dict()
    print("Checking patches")
    for patch in patchids["patch_software_titles"]["patch_software_title"]:
        swtitle = webrequest(url, patchreports+patch["id"])
        # uncomment this to see all of the information for each individual patch title.  Definitely too much for debug mode (issue #3)
        #print(json.dumps(swtitle))
        for idx, version in enumerate(swtitle["patch_report"]["versions"]["version"]):
            if idx == 0:
                currentver = version["software_version"]
                continue
            if version["software_version"]  == "Unknown":
                print("Unknown skipped")
                continue
            pccount = version["computers"]["size"]
            if pccount == "1":
                managepcdefinition(pcdef, parsepc(swtitle, version, currentver), version["computers"]["computer"]["id"])
            elif pccount != "0":
                for pc in version["computers"]["computer"]:
                    managepcdefinition(pcdef, parsepc(swtitle, version, currentver), pc["id"])
    print("Composing emails")
    for key in pcdef.keys():
        formatsendmail(key, pcdef[key])
    print("Done!")

if __name__ == "__main__":
    token = gettoken()
    main()