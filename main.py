import re
import os
import sys
import json
import requests
from urllib.parse import quote, unquote
from requests import Session
from requests.exceptions import ConnectionError, TooManyRedirects
from requests.exceptions import Timeout, HTTPError, RequestException
from time import sleep
from random import randint
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from colorama import Fore, Back, Style, init

init(autoreset=True)

end = "\033[K"
res = Style.RESET_ALL
bg_red = Back.RED
red = Style.BRIGHT+Fore.RED
white = Style.BRIGHT+Fore.WHITE
magenta = Style.BRIGHT+Fore.MAGENTA
celeste = Style.BRIGHT+Fore.CYAN
green = Style.BRIGHT+Fore.GREEN
yellow = Style.BRIGHT+Fore.YELLOW

def clean_screen():
    os.system("clear" if os.name == "posix" else "cls")

def banner():
    clean_screen()
    line()
    print(f"{green}{sc_ver.center(50, ' ')}")
    line()

def wait(x, text='Please wait'):
    for i in range(x, -1, -1):
        col = yellow if i%2 == 0 else white
        animation = "⫸" if i%2 == 0 else "⫸⫸"
        m, s = divmod(i, 60)
        t = f"[00:{m:02}:{s:02}]"
        sys.stdout.write(f"\r  {white}{text} {col}{t} {animation}{res}{end}\r")
        sys.stdout.flush()
        sleep(1)

def carousel(message):
    def first_part(message, wait):
        animated_message = message.center(48)
        msg_effect = ""
        for i in range(len(animated_message) - 1):
            msg_effect += animated_message[i]
            sys.stdout.write(f"\r {msg_effect}{res} {end}")
            sys.stdout.flush()
            sleep(0.03)
        if wait:
            sleep(1)

    msg_effect = message[:47]
    wait = True if len(message) <= 47 else False
    first_part(msg_effect, wait)
    if len(message) > 47:
        for i in range(50, len(message)):
            msg_effect = msg_effect[1:] + message[i]
            if i > 1:
                sys.stdout.write(f"\r {msg_effect} {res}{end}")
                sys.stdout.flush()
            sleep(0.1)
    sleep(1)
    sys.stdout.write(f"\r{res}{end}\r")
    sys.stdout.flush()

def line(char='━'):
    print(f"{green}{char * 50}")

def action(action, not_print=False):
    now = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    total_length = len(action) + len(now) + 5
    space_count = 50 - total_length
    msg = f"[{action.upper()}] {now}{' ' * space_count}"
    if not_print:
        return f"{bg_red} {white}{msg}{res}{red}⫸{res}{end}"
    print(f"{bg_red} {white}{msg}{res}{red}⫸{res}{end}")
    
def user_banner(data_account):
    banner()
    print()
    max_length = max(map(len, data_account))
    for label, info in data_account.items():
        diff = max_length - len(label)
        print(f"{bg_red}{white} ๏ {res} {yellow}〔 {label} 〕{'.' * diff}: {white}{info}{res}{end}")
    print(f'{res}{end}')
    line()

def withdraw():
    print(f"{red} Option not implemented.!")
    exit()

def data_account(message=True):
    def check_nones(data):
        for value in data.values():
            if isinstance(value, dict):
                if check_nones(value):
                    return True
            elif value is None:
                return True
        return False
    
    global x_csrf_token
    attempts = 0
    max_attempts = 0
    while True:
        if message:
            carousel("Getting user info")
        url = f"https://api.{host}/user"
        headers = {
          'accept': 'application/json, text/plain, */*',
          'referer': f"https://www.{host}/",
          'user-agent': data_user['user_agent'],
          'x-requested-with': 'XMLHttpRequest'
        }
        response = curl(
            method='GET',
            url=url,
            name_host=host,
            headers=headers,
            session=data_user['session']
        )
        if response:
            x_csrf_token = response.cookies.get('XSRF-TOKEN', None)
            if x_csrf_token:
                x_csrf_token = unquote(x_csrf_token)
                info = {}
                try:
                    response = response.json()
                except Exception as e:
                    carousel(str(e))
                    attempts += 1
                    if attempts >= max_attempts:
                        print(f"{red}Check your credentials!")
                        exit()
                info['id'] = response['id']
                info['next_claim'] = response['next_claim']
                info['balance'] = response['balance']
                info['address'] = response['wallet_address']
                info['min_wd'] = response['wallet_currency']['min_withdraw']
                if not check_nones(info):
                    return info

def history_claims(section):
    url_history = {
        "task": f"https://api.{host}/profile/flamenews-tasks-history?page=1",
        "coupon": f"https://api.{host}/coupon/claimedByUser?page=1",
        "faucet": f"https://api.{host}/profile/faucet-history?page=1",
        "withdrawal": f"https://api.{host}/profile/withdrawals?page=1"
    }
    global x_csrf_token
    while True:
        carousel(f"Getting {section} history")
        data_account(message=False)
        headers = {
          'connection': 'keep-alive',
          'accept': '*/*',
          'referer': f"https://www.{host}/",
          'user-agent': data_user['user_agent'],
          'x-requested-with': 'XMLHttpRequest',
          'x-xsrf-token': x_csrf_token
        }
        response = curl(method='GET', url=url_history[section], headers=headers, name_host=host, session=data_user['session'])
        x_csrf_token = None
        history = []
        if response:
            response = response.json()
            if 'data' in response:
                if len(response['data']) > 0:
                    list_articles = response['data']
                    for article in list_articles:
                        if section == 'coupon':
                            history.append({'code': article['code'], 'date': article['date'], 'reward': article['reward']})
                        elif section == 'task':
                            history.append({'title': article['title'], 'code': article['code'], 'date': article['date'], 'reward': article['reward']})
                        elif section == 'faucet':
                            history.append({'date': article['date'], 'reward': article['reward']})
                    return history
                else:
                    carousel(f"Not have {section} history")
                    return history
            else:
                carousel(f"Error getting list {section} history")
                wait(30)
        else:
            carousel(f"Error getting {section} history")
            wait(30)
            
def faucet():
    global x_csrf_token
    while True:
        carousel("Go to faucet section")
        next_claim = data_account(message=False)['next_claim']
        if next_claim not in [0, -1, '0', '-1']:
            carousel('Faucet not available now')
            wait(int(next_claim))
            x_csrf_token = None
            continue
        while True:
            result_recaptcha = changelle(page=f'https://{host}', method='userrecaptcha', sitekey='6LdU8qEpAAAAAA7RFfDULrYr_rHNn0cutHPE4wEt')
            if result_recaptcha:
                break
        url = f"https://api.{host}/claim-faucet"
        headers = {
          'accept': 'application/json, text/plain, */*',
          'content-type': 'application/json',
          'referer': f"https://www.{host}/",
          'user-agent': data_user['user_agent'],
          'x-requested-with': 'XMLHttpRequest',
          'x-xsrf-token': x_csrf_token
        }
        payload = json.dumps({
            'recaptcha': result_recaptcha
        })
        response = curl(method='POST', url=url, headers=headers, form_data=payload, name_host=host, session=data_user['session'])
        x_csrf_token = None
        if response:
            response = response.json()
            if 'message' in response:
                if 'Successfully claimed' in response['message']:
                    carousel('Claim successfully')
                    info = data_account()
                    reward = int(re.search(r'\d+', response['message']).group())
                    action('FAUCET')
                    print(f" {red}◇ {white}Reward: {reward} FLAME{res}{end}")
                    print(f" {red}◇ {white}Balance: {green}{info['balance']}{white} FLAME{res}{end}")
                    print(f" {red}◇ {white}{response['message']}{res}{end}")
                    print(f" {red}◇ {white}Balance {data_solver['name'].capitalize()}: "
                          f"{green}{data_solver['balance']}{white} {data_solver['currency'].capitalize()}{res}  -  [ "
                          f"{red}{data_solver['failed']}{res} / "
                          f"{green}{data_solver['spent']}{res} ]{end}"
                    )
                    line()
                    continue
                else:
                    carousel(response['message'])
                    carousel('Claim faucet failed')
                    data_solver['failed'] += 1
                    if 'The google recaptcha is required' in response['message']:
                        wait(30)
                        continue
            print(response.text)
            exit()
        sleep(1)

def task():
    def find_code(_id):
        url = f"https://api.{host}/task-news/details/{_id}"
        response = curl(method='GET', url=url, headers=head_gift, name_host=host, session=data_user['session'])
        if response:
            response = response.json()
            list_articles = response['articles']
            for article in list_articles:
                headers = {'user-agent': data_user['user_agent']}
                carousel(f"Visiting article: {article['url']}")
                response = curl(method='GET', url=article['url'], headers=headers, name_host=host, session=Session())
                soup = BeautifulSoup(response.text, 'html.parser')
                span = soup.find('span', class_='text-gray-900 dark:text-white text-left')
                if span:
                    code = span.text.strip()
                    carousel(f"Code was found: {code}")
                    return code
                else:
                    carousel('No codes found in this article!')
                sleep(1)
        return None
                                    
    def claim_code(code, reward, date_task_id):
        while True:
            data_account(message=False)
            while True:
                result_recaptcha = changelle(page=f'https://{host}', method='userrecaptcha', sitekey='6LdU8qEpAAAAAA7RFfDULrYr_rHNn0cutHPE4wEt')
                if result_recaptcha:
                    break
            url = f"https://api.{host}/task-news/claim"
            payload = json.dumps({
              "articleCode": code,
              "recaptcha": result_recaptcha
            })
            headers = head_gift
            headers['x-xsrf-token'] = x_csrf_token
            headers['content-type'] = 'application/json'
            while True:
                response = curl(method='POST', url=url, headers=headers, form_data=payload, name_host=host, session=data_user['session'])
                if response:
                    break
                wait(5)
            response = response.json()
            if 'message' in response:
                if 'ok' in response['message'].lower():
                    carousel('Claim successfully')
                    info = data_account()
                    action('GITF CODE')
                    print(f" {red}◇ {white}Task: {celeste}{date_task_id}{res}{end}")
                    print(f" {red}◇ {white}Code: {yellow}{code}{res}{end}")
                    print(f" {red}◇ {white}Reward: {reward}{white} FLAME{res}{end}")
                    print(f" {red}◇ {white}Balance: {green}{info['balance']}{white} FLAME{res}{end}")
                    print(f" {red}◇ {white}Balance {data_solver['name'].capitalize()}: "
                          f"{green}{data_solver['balance']}{white} {data_solver['currency'].capitalize()}{res}  -  [ "
                          f"{red}{data_solver['failed']}{res} / "
                          f"{green}{data_solver['spent']}{res} ]{end}"
                    )
                    line()
                    return
                else:
                    carousel(response['message'])
                    carousel('Claim task failed')
                    data_solver['failed'] += 1
                    if any(keyword in response['message'].lower() for keyword in ['expired', 'already claimed', 'not found']):
                        return None
                    if 'the google recaptcha is required' in response['message'].lower():
                        wait(10)
                        continue
            print(response.text)
            exit()

    global x_csrf_token
    while True:
        carousel("Go to task section")
        data_account(message=False)
        url = f"https://api.{host}/task-news/list?page=1"
        head_gift = {
          'connection': 'keep-alive',
          'accept': '*/*',
          'referer': f"https://www.{host}/",
          'user-agent': data_user['user_agent'],
          'x-requested-with': 'XMLHttpRequest',
          'x-xsrf-token': x_csrf_token
        }
        response = curl(method='GET', url=url, headers=head_gift, name_host=host, session=data_user['session'])
        x_csrf_token = None
        if response:
            response = response.json()
            if 'data' in response:
                carousel(f"Total task found: ({len(response['data'])})")
                if len(response['data']) > 0:
                    list_articles = response['data']
                    history = history_claims('task')
                    for x in range(len(list_articles)):
                        exist_task = False
                        carousel(f"Task found: {list_articles[x]['title']}")
                        for his in history:
                            if list_articles[x]['title'] == his['title']:
                                exist_task = True
                        if exist_task:
                            carousel('This task has already been claimed!')
                            continue
                        else:
                            reward = list_articles[x]['reward']
                            code = find_code(list_articles[x]['id'])
                            if code:
                                claim_code(code, reward, list_articles[x]['title'])
                                wait(30)
                        sleep(1)
                    carousel('Not more articles for find gift codes')
                    wait(180)
                else:
                    carousel('Not availables articles this moment.!')
                    wait(180)
            else:
                carousel('Error getting list articles')
                wait(30)
        else:
            carousel('Error getting info articles')
            wait(30)

def coupon(url=None, code=None):
    def find_code(url):
        headers= {
          'connection': 'keep-alive',
          'accept': '*/*',
          'referer': f"https://www.{host}/",
          'user-agent': data_user['user_agent'],
          'x-requested-with': 'XMLHttpRequest',
          'x-xsrf-token': x_csrf_token
        }
        response = curl(method='GET', url=url, headers=headers, name_host=host, session=data_user['session'])
        if response:
            response = response.json()
            list_articles = response['articles']
            for article in list_articles:
                headers = {'user-agent': data_user['user_agent']}
                carousel(f"Visiting article: {article['url']}")
                response = curl(method='GET', url=article['url'], headers=headers, name_host=host, session=Session())
                soup = BeautifulSoup(response.text, 'html.parser')
                span = soup.find('span', class_='text-gray-900 dark:text-white text-left')
                if span:
                    code = span.text.strip()
                    carousel(f"Code was found: {code}")
                    return code
                else:
                    carousel('No codes found in this article!')
                sleep(1)
        return None
                                    
    def claim_coupon(code):
        global list_coupon_claimed
        while True:
            data_account(message=False)
            while True:
                result_recaptcha = changelle(page=f'https://{host}', method='userrecaptcha', sitekey='6LdU8qEpAAAAAA7RFfDULrYr_rHNn0cutHPE4wEt')
                if result_recaptcha:
                    break
            url = f"https://api.{host}/coupon/claim"
            headers= {
              'connection': 'keep-alive',
              'accept': '*/*',
              'referer': f"https://www.{host}/",
              'user-agent': data_user['user_agent'],
              'content-type': 'application/json',
              'x-requested-with': 'XMLHttpRequest',
              'x-xsrf-token': x_csrf_token
            }
            payload = json.dumps({
              "couponCode": code,
              "recaptcha": result_recaptcha
            })
            response = curl(method='POST', url=url, headers=headers, form_data=payload, name_host=host, session=data_user['session']).json()
            if 'message' in response:
                if 'ok' in response['message'].lower():
                    carousel('Claim successfully')
                    info = data_account()
                    act = action('COUPON', not_print=True)
                    history = history_claims('coupon')
                    for his in history:
                        if code == his['code']:
                            reward = his['reward']
                            break
                    coupon_claim = (
                        f"{act}\n"
                        f" {red}◇ {white}Code: {yellow}{code}{res}{end}\n"
                        f" {red}◇ {white}Reward: {reward}{white} FLAME{res}{end}\n"
                        f" {red}◇ {white}Balance: {green}{info['balance']}{white} FLAME{res}{end}\n"
                        f" {red}◇ {white}Balance {data_solver['name'].capitalize()}: "
                            f"{green}{data_solver['balance']}{white} {data_solver['currency'].capitalize()}{res}  -  [ "
                            f"{red}{data_solver['failed']}{res} / "
                            f"{green}{data_solver['spent']}{res} ]{end}"
                    )
                    list_coupon_claimed.append(coupon_claim)
                    return
                else:
                    carousel(response['message'])
                    carousel('Claim task failed')
                    data_solver['failed'] += 1
                    if any(keyword in response['message'].lower() for keyword in ['expired', 'already claimed', 'not found']):
                        return
                    if 'the google recaptcha is required' in response['message'].lower():
                        wait(10)
                        continue
            print(response.text)
            exit()

    global x_csrf_token
    while True:
        carousel("Go to claim coupon section")
        data_account(message=False)
        if url and not code:
            code = find_code(url)
        elif not code:
            carousel("Error code not provided")
            return
        history = history_claims('coupon')
        exist_code = False
        for his in history:
            if his['code'] == code:
                exist_code = True
        if not exist_code:
            claim_coupon(code)
        else:
            carousel('This coupon has already been claimed!')
        return

def changelle(page, method, **kwargs):
    def update_stats(action):
        def reset_attemps():
            data_solver['attempts'] = 0
            data_solver['total_attempts'] = 0
        
        if action == 'success':
            data_solver['spent'] += 1
            reset_attemps()
        elif action == 'failed':
            data_solver['failed'] += 1
            reset_attemps()
        elif action == 'increase_attemps':
            data_solver['attempts'] += 1
            data_solver['total_attempts'] += 1
        elif action == 'null':
            reset_attemps()
        else:
            print(f"Error action {action} for update stats solver {data_solver['name']}")
            exit()

    def get_balance():
        global data_solver
        while True:
            carousel(f"Getting current balance {data_solver['name']}")
            action = 'userinfo' if data_solver['name'] == 'multibot' else 'getbalance'
            response = curl(
                method='GET',
                url=f"{data_solver['url_base']}/res.php?action={action}&key={data_solver['key']}",
                name_host=data_solver['name'],
                session=data_solver['session']
            )
            if not response:
                carousel(f"Error getting balance {data_solver['name']}")
                continue
            try:
                if response.text == '[]':
                    print(f"Bad {data_solver['name']} key: {data_solver['key']}")
                    exit()
                if data_solver['name'] == 'multibot':
                    data_solver['balance'] = int(json.loads(response.text)['balance'])
                else:
                    data_solver['balance'] = float(response.text)
                if data_solver['balance'] < data_solver['minbal']:
                    print(f"Your balance {data_solver['name']} is: {data_solver['balance']}")
                    exit()
                break
            except Exception as e:
                print(f'{response.text}\n\nError: {e}')
                exit()

    def get_id_task(page, method, sitekey=None, images=None):
        carousel(f'Getting {method} id task')
        payload = {'key': data_solver['key'], 'method': method}
        if method == 'antibot':
            if images:
                payload.update(images)
            else:
                print('Images not provided')
                exit()
        elif method in ['userrecaptcha', 'hcaptcha']:
            payload['pageurl'] = page
            if sitekey:
                payload['sitekey'] = sitekey
            else:
                print('Sitekey not provided')
                exit()
        while True:
            response = curl(
                method='POST',
                url=f"{data_solver['url_base']}/in.php",
                form_data=payload,
                name_host=data_solver['name'],
                session=data_solver['session']
            )
            if not response or response and '|' not in response.text:
                carousel(f'Error creating {method} task')
                return None
            id_task = response.text.split('|')[1]
            carousel(f'Task id created successfully: {id_task}')
            return id_task

    def get_result(method, task_number, max_attempts=None):
        carousel(f'Getting {method} result')
        global data_solver
        max_attempts = 200 if not max_attempts else max_attempts
        action = 'action=get&' if data_solver['name'] == 'multibot' else ''
        while True:
            response = curl(
                method='GET',
                url=f"{data_solver['url_base']}/res.php?key={data_solver['key']}&{action}id={task_number}",
                name_host=data_solver['name'],
                session=data_solver['session']
            )
            if not response:
                carousel(f'Error getting {method} result')
                continue
            if '|' in response.text:
                carousel(f'Get {method} result successfully')
                update_stats('success')
                return response.text.split('|')[1]
            elif 'CAPCHA_NOT_READY' in response.text:
                update_stats('increase_attemps')
                carousel(f"Captcha not ready  ●  Attempts: [ {data_solver['attempts']}/{data_solver['total_attempts']} ]")
                if data_solver['attempts'] >= max_attempts:
                    update_stats('null')
                    carousel(f'Error getting {method} result')
                    return None
            elif ('WRONG_RESULT' in response.text or
                  'ERROR_NOT_CAPTCHA_ID' in response.text):
                update_stats('null')
                return None
            else:
                print(response.text)
                exit()

    sitekey = kwargs.get('sitekey', None)
    imgs = kwargs.get('imgs', None)
    get_balance()
    while True:
        task_number = get_id_task(page, method, sitekey=sitekey, images=imgs)
        if task_number:
            if get_result:
                return get_result(method, task_number)

def curl(method, url, **kwargs):
    def prints_errors(text, temp=True):
        if not temp:
            print(f'{red}{text}')
            exit()
        carousel(f'{white}{text}')
        
    global data_user
    n_host = kwargs.get('name_host', url)
    session = kwargs.get('session', None)
    headers = kwargs.get('headers', {})
    form_data = kwargs.get('form_data', {})
    json_data = kwargs.get('json_data', {})
    timeout = kwargs.get('timeout', 60)
    while True:
        try:
            if json_data:
                response = session.request(method, url, headers=headers, json=json_data, timeout=timeout)
            else:
                response = session.request(method, url, headers=headers, data=form_data, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if isinstance(e, ConnectionError):
                carousel(f'Reconnecting to {n_host}')
                wait(60)
                continue
            if isinstance(e, TooManyRedirects):
                carousel("Too many redirects")
                wait(60)
                continue
            if isinstance(e, Timeout):
                carousel("Timeout reached")
                wait(60)
                continue
            if isinstance(e, HTTPError):
                try:
                    if response.status_code in [500, 502, 503, 521, 522, 524]:
                        if response.status_code == 500:
                            prints_errors(f'Internal server {n_host} error')
                        if response.status_code == 502:
                            prints_errors(f'Bad gateway > {n_host}')
                        if response.status_code == 503:
                            prints_errors(f'Service {n_host} unavailable')
                        if response.status_code == 521:
                            prints_errors(f'Host {n_host} overloaded')
                        if response.status_code == 522:
                            prints_errors('Connection time out')
                        if response.status_code == 524:
                            prints_errors('A time out ocurred')
                        wait(randint(300,1000))
                        return None
                    elif response.status_code in [400, 401, 403, 404]:
                        if response.status_code == 400:
                            prints_errors('Bad request', temp=False)
                        if response.status_code == 401:
                            prints_errors('Unauthorized', temp=False)
                        if response.status_code == 403:
                            prints_errors('Access denied', temp=False)
                        if response.status_code == 404 or response.status_code == 422:
                            if url in [
                                f"https://api.{host}/coupon/claim",
                                f"https://api.{host}/claim-faucet",
                                f"https://api.{host}/task-news/claim"
                            ]:
                                return response
                            prints_errors('Resource not found', temp=False)
                    print(response.text)
                    prints_errors(f'Unexpected code {response.status_code}', temp=False)
                except AttributeError as e:
                    carousel(f'HTTPError code not found, Error: {str(e)}')
                    continue
            prints_errors(f'Unexpected response code: {e}', temp=False)
        except Exception as e:
            prints_errors(f'Unexpected error: {str(e)}', temp=False)

def delete_file(file):
    try:
        os.remove(file)
        print(f"{red}File {file} was deleted{end}")
    except FileNotFoundError:
        print(f"{red}File {file} not found{end}")
    exit()

def files(file):
    banner()
    def valid_input(name):
        condictions= {
            'Wallet Ltc': {'length': 20, 'phrase': ''},
            'Cookies': {'length': 20, 'phrase': '='},
            'User Agent': {'length': 10, 'phrase': 'Mozilla'},
            'Multibot': {'length': 10, 'phrase': ''},
            'Xevil': {'length': 10, 'phrase': ''}
        }
        prompt = ''
        key = f'Api-Key {name}' if name in ['Multibot', 'Xevil'] else name
        while (len(prompt) < condictions[name]['length'] or
               (condictions[name]['phrase'] and condictions[name]['phrase'] not in prompt)):
            prompt = input(f"{yellow}{key}{red}:{res} ")
        return prompt.strip()
    
    data = None
    try:
        with open(file, 'r') as f:
            data = f.read()
    except FileNotFoundError:
        data = valid_input(file)
        with open(file, 'w') as f:
            f.write(data)
    return data

def select_solver():
    banner()
    global data_solver
    option = input(
        f'{yellow}Select Solver{red}:{res}\n'
        f'{white}1.- {celeste}Multibot\n'
        f'{white}2.- {celeste}Xevil\n\n'
        f'{yellow}Input number{red}:{res} '
    )
    if option.isdigit() and 1 <= int(option) <= 2:
        data_solver['name'] = 'multibot' if option == '1' else 'xevil'
        data_solver['key'] = files(data_solver['name'].capitalize())
        data_solver['url_base'] = 'http://api.multibot.in' if option == '1' else 'http://goodxevilpay.pp.ua'
        data_solver['currency'] = 'tokens' if option == '1' else 'rublos'
        data_solver['minbal'] = 1 if option == '1' else 0.0006
        data_solver['balance'] = 0
        data_solver['spent'] = 0
        data_solver['failed'] = 0
        data_solver['attempts'] = 0
        data_solver['total_attempts'] = 0
        data_solver['session'] = Session()
    else:
        print(f"{red}Invalid option")
        exit()

sc_ver = 'FLAMEFAUCET [VIP] (v3.1)'
host = 'flamefaucet.com'

data_solver = {}
data_user = {}
data_user['session'] = Session()
data_user['cookies'] = files('Cookies')
cookies = {pair[0]: pair[1] for pair in (cookie.split('=') for cookie in data_user['cookies'].split('; '))}
data_user['session'].cookies.update(cookies)
data_user['user_agent'] = files('User Agent')

x_csrf_token = None

banner()
option = input(
    f'{yellow}Select Option{red}:{res}\n'
    f'{white}1.- {celeste}Faucet\n'
    f'{white}2.- {celeste}Task\n'
    f'{white}3.- {celeste}Coupon\n'
    f'{white}4.- {celeste}Withdrawal\n'
    f'{yellow}Input number{red}:{res} '
)
if option.isdigit() and 1 <= int(option) <= 3:
    option = int(option)
    select_solver()
    banner()
    info = data_account()
    user_banner({
        'ID': info['id'],
        'BALANCE': f"{info['balance']} FLAME"
    })
    text_wallet = '〔 LTC WALLET 〕'
    print(f"{yellow}{text_wallet.center(50)}{res}{end}")
    print(f"\n{white}{info['address'].center(50)}{res}{end}")
    line()
    list_coupon_claimed = []
    if option == 1:
        while True:
            faucet()
    if option == 2:
        while True:
            task()
    if option == 3:
        while True:
            coupon_type = input(
                f'{yellow}Select Coupon Method{red}:{res}\n'
                f'{white}1.- {celeste}Code\n'
                f'{white}2.- {celeste}Url blog\n'
                f'{yellow}Input number{red}:{res} '
            )
            print()
            if coupon_type.isdigit() and 1 <= int(coupon_type) <= 2:
                coupon_type = int(coupon_type)
                if coupon_type == 1:
                    code = input(f'{yellow}Code{red}:{res} ').strip()
                    coupon(code=code)
                else:
                    url = input(f'{yellow}Url blog{red}:{res} ').strip()
                    coupon(url=url)
            else:
                print(f'{red}Invalid option')
            banner()
            info = data_account()
            user_banner({
                'ID': info['id'],
                'BALANCE': f"{info['balance']} FLAME"
            })
            text_wallet = '〔 LTC WALLET 〕'
            print(f"{yellow}{text_wallet.center(50)}{res}{end}")
            print(f"\n{white}{info['address'].center(50)}{res}{end}")
            line()
            if list_coupon_claimed:
                for coupon_claim in list_coupon_claimed:
                    print(coupon_claim)
                    line()
            sleep(1)
    if option == 4:
        withdraw()
        exit()
else:
    print(f'{red}Invalid option')
    exit()
