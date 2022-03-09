# Notifier

Notifier is a Python Script to send emails to Mac users with pending updates (according to Jamf patch 
management) using the Jamf API and SMTP!

## How it works

1. Grab API username and password the `JAMFREPORTUSER` and `JAMFREPORTPASS` environment variables.
2. Get a bearer token from the Jamf server.  This is used for all further authentication.
3. Gets a list of all Patch Management titles on the Jamf server
4. For each Patch Management title, get a list of every version
5. Record the first version number, skip any computers on this version (they're up to date!)
6. Skip any computers with an Unknown version.  Usually this means a version newer than what Jamf has an update for.
7. Get a count of computers on each version
8. If there's exactly one computer, record the information in the computer definition 
9. If there's more than one computer, record each into the definition sequentially (Jamf provides a different data structure for single computers)
10. Add the Full Name and Email Address assigned to each computer in Jamf to the computer definition
11. Connect to your SMTP server
12. Fill in all the fields in the email
13. Add each patch to the body of the email, with an installed and expected version.
14. Cap it off with a friendly closer
15. Send the emails!

# Requirements
The requirements.txt file can be fed to PIP to download all the prerequisites for the project using the command:

```python3 -m pip -r requirements.txt```

# importrequests

This is a standalone tool to get a Jamf bearer token.  We made this during the same Hackathon.  It was merged into Notifier, but it's still a handy tool for testing.  Just remember not to commit your API key! 😅
