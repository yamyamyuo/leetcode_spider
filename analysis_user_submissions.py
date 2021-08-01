import requests
import json
import csv
import time
from requests_toolbelt import MultipartEncoder
check_timestamp = time.time() - 24*60*60

user_agent = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
username = ""
password = ""
cn_leetcode_url = 'https://leetcode-cn.com'
us_leetcode_url = 'https://leetcode.com'
user_slug_map = dict()
US_REGION = "us"

daily_report = dict()

def load_user_slugs():
    with open("markdowns/user_slug.csv", "r") as fopen:
        rows = csv.reader(fopen)
        for row in rows:
            user_slug_map[row[0]] = [row[1], row[2]]


def get_login_session(base_url, username, password, csrftoken=None):
    session = requests.Session()
    cookies = session.get(base_url).cookies
    for cookie in cookies:
        if cookie.name == 'csrftoken':
            csrftoken = cookie.value

    url = base_url + "/accounts/login"
        
    params_data = {
        'csrfmiddlewaretoken': csrftoken if not None else '',
        'login': username,
        'password':password,
        'next': 'problems'
    }
    headers = {'User-Agent': user_agent, 'Connection': 'keep-alive', 'Referer': url + '/', "origin": base_url}
    m = MultipartEncoder(params_data)   

    headers['Content-Type'] = m.content_type
    session.post(url, headers = headers, data = m, timeout = 10, allow_redirects = False)
    is_login = session.cookies.get('LEETCODE_SESSION') != None
    print("is login: %s" % is_login)
    return session


def get_submissions(base_url, session, user, slug):
    url = base_url + "/graphql"
    request_params = {
    "operationName": "recentSubmissions",
    "variables": {"userSlug": slug},
    "query": """query recentSubmissions($userSlug: String!) {
    recentSubmissions(userSlug: $userSlug) {
        status
        lang
        question {
        questionFrontendId
        title
        translatedTitle
        titleSlug
        __typename
        }
        submitTime
        __typename
    }
    }
    """
    }
    json_data = json.dumps(request_params).encode('utf8')

    headers = {'User-Agent': user_agent, 'Connection': 'keep-alive', 'Referer': base_url + "/accounts/login/",
        "Content-Type": "application/json"}  
    resp = session.post(url, data = json_data, headers = headers, timeout = 10)
    content = resp.json()
    # print(content)
    submissions = content['data']['recentSubmissions']
    timed_submissions = list(filter(lambda s: s['submitTime'] >= check_timestamp, submissions))
    success_submissions = list(filter(lambda s: s['status'] == 'A_10', timed_submissions))
    distinct_success_subs = set(map(lambda s: s['question']['questionFrontendId'], success_submissions))
    success_submissions_cnt = len(distinct_success_subs)
    if success_submissions:
        latest_title = success_submissions[0]['question']['translatedTitle']
    else:
        latest_title = None
    
    daily_report[user] = dict(success_cnt=success_submissions_cnt,
                            latest_title=latest_title)




cn_session = get_login_session(cn_leetcode_url, username, password)
us_session = get_login_session(us_leetcode_url, username, password)
# get_submissions()
load_user_slugs()

for user in user_slug_map:
    slug, region = user_slug_map[user]
    if region == US_REGION:
        get_submissions(us_leetcode_url, us_session, user, slug)
    else:
        get_submissions(cn_leetcode_url, cn_session, user, slug)

print(json.dumps(daily_report, indent=4))
print("用户名\t\t成功提交次数\t最近一道题目")
for user in daily_report:
    print("%s\t\t%s\t\t%s" % (user, daily_report[user]["success_cnt"], daily_report[user]["latest_title"]))
