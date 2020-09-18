from bs4 import BeautifulSoup
from requests_html import HTMLSession
from urllib.parse import urljoin
import webbrowser
import datetime
import time
import os
import sys

LOGIN_URL = "https://pointage.adp.com/"
CLOCKING_URL = "https://pointage.adp.com/ipclogin/1/loginform.fcc"

session = HTMLSession()

def get_all_forms(url):
    """Returns all form tags found on a web page's `url` """
    # GET request
    res = session.get(url)

    soup = BeautifulSoup(res.html.html, "html.parser")
    return soup.find_all("form")

def get_form_details(form):
    """Returns the HTML details of a form,
    including action, method and list of form controls (inputs, etc)"""
    details = {}
    # get the form action (requested URL)
    action = form.attrs.get("action").lower()
    # get the form method (POST, GET, DELETE, etc)
    # if not specified, GET is the default in HTML
    method = form.attrs.get("method", "get").lower()
    # get all form inputs
    inputs = []
    for input_tag in form.find_all("input"):
        # get type of input form control
        input_type = input_tag.attrs.get("type", "text")
        # get name attribute
        input_name = input_tag.attrs.get("name")
        # get the default value of that input tag
        input_value =input_tag.attrs.get("value", "")
        # add everything to that list
        inputs.append({"type": input_type, "name": input_name, "value": input_value})
    # put everything to the resulting dictionary
    details["action"] = action
    details["method"] = method
    details["inputs"] = inputs
    return details

def ask_credentials(creds_path):
    user_id = input("Username: ")
    user_pwd = input("Password: ")
    save = input("Save credentials? (y/n) ")
    if save == 'y' or save == 'Y':
        with open(creds_path, 'w') as cred_file:
            cred_file.write(user_id + "\n" + user_pwd)
        print("Saving credentials to: " + creds_path)
    return user_id, user_pwd

def get_user_data():
    creds_path = "creds.txt"
    if os.path.exists(creds_path):
        with open(creds_path, 'r') as cred_file:
            try:
                user_id = cred_file.readlines(1)
                user_pwd = cred_file.readlines(2)
            except:
                user_id, user_pwd = ask_credentials(creds_path)
    else:
        user_id, user_pwd = ask_credentials(creds_path)
    return user_id, user_pwd

def login():
    user_id, user_pwd = get_user_data()
    first_form = get_all_forms(LOGIN_URL)[0]
    # extract all form details
    form_details = get_form_details(first_form)

    # the data body we want to submit
    data = {}
    for input_tag in form_details["inputs"]:
        if input_tag["type"] == "hidden":
            # if it's hidden, use the default value
            data[input_tag["name"]] = input_tag["value"]
        elif input_tag["name"] == "USER":
            data[input_tag["name"]] = user_id
        elif input_tag["name"] == "PASSWORD":
            data[input_tag["name"]] = user_pwd
        elif input_tag["type"] != "submit":
            print('Error, exiting...')
            sys.exit()

    res = session.post(CLOCKING_URL, data=data)
    return res

def get_clocking_time():
    res = login()

    first_form = get_all_forms(res.url)[0]
    # extract all form details
    form_details = get_form_details(first_form)

    data = {}
    for input_tag in form_details["inputs"]:
        if input_tag["name"] == "ACTION":
            data[input_tag["name"]] = "POI_CONS"
        elif input_tag["name"] == "GMT_DATE":
            data[input_tag["name"]] = input_tag["value"]
        elif input_tag["name"] == "USER_OFFSET":
            data[input_tag["name"]] = "MTIw"
        elif input_tag["name"] == "FONCTION":
            data[input_tag["name"]] = ""
        elif input_tag["type"] != "submit":
            print('Error, exiting...')
            sys.exit()

    res = session.post(res.url, data=data)

    soup = BeautifulSoup(res.content, "html.parser")
    return soup

def main():
    soup = get_clocking_time()
    texts = soup.find_all(text=True)

    date = ''
    hours = []
    date_time_obj = []
    for element in texts:
        if '/' in element and '-' in element and ':' in element:
            atomic_element = element.split(' ')
            date = atomic_element[-3]
            hours.append(atomic_element[-1])
            date_time = date + ' ' + hours[-1]
            date_time_obj.append(datetime.datetime.strptime(date_time, '%d/%m/%Y %H:%M'))

    goal_time = datetime.timedelta(hours=7)
    if len(date_time_obj) < 1:
        print('Too few time registered for today')
    elif len(date_time_obj) == 1:
        print('You started your day at: ' + str(date_time_obj[0]))
    elif len(date_time_obj) == 2:
        total_worked_time_morning = date_time_obj[1] - date_time_obj[0]
        print('Total time worked this morning: ' + str(total_worked_time_morning))
        start_again_date_time = date_time_obj[1] + datetime.timedelta(minutes=40)
        remaining_time = goal_time - total_worked_time_morning
        finish_time = start_again_date_time + remaining_time
        print('With a break of 40 minutes, you should finish you day at: ' + str(finish_time))
    elif len(date_time_obj) == 3:
        total_worked_time_morning = date_time_obj[1] - date_time_obj[0]
        remaining_time = goal_time - total_worked_time_morning
        finish_time = date_time_obj[2] + remaining_time
        print('You finish your day at: ' + str(finish_time))
    elif len(date_time_obj) == 4:
        print('You finished your day at: ' + str(date_time_obj[-1]))
    else:
        print('Error, exiting...')
        sys.exit()

main()
os.system('pause')