import sqlite3
import requests, time, os, json,base64,re
from datetime import datetime, timedelta
# from multiprocessing.dummy import Pool
import warnings
warnings.filterwarnings('ignore')

# 以下需要配置以下！
# -----------------------------------
github_token = "" # GitHub token
server_key = "" # server酱的SendKey
webhook_key="" # 企业微信机器人key
send_type = "Webhook" # 指定推送方式：ServerChan(server酱）、Webhook(企业微信机器人)
# -----------------------------------

update_repositories = []
update_issues = []
new_date = int(time.time())
current_date = datetime.now()
previous_date = current_date - timedelta(days=2)
issues_temp = []
issue_data = "/tmp/issue_data.txt"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
    'Authorization': "token {}".format(github_token)
}

def get_github_repositories(cve="cve-"):
    for page in range(1,4):
        url = "https://api.github.com/search/repositories?q={}&sort=updated&per_page=100&page={}".format(cve,page)
        # print(url)
        try:
            rep1 = requests.get(url, headers=headers, verify=False).json()
            for i in range(100):
                dic = {}
                dic['p_name'] = rep1['items'][i]['name']
                dic['p_description'] = rep1['items'][i]['description']
                p_name = str(dic['p_name']).upper()
                p_description = str(dic['p_description']).upper()
                cve_re = re.compile(".*CVE-[0-9]{4}-[0-9]+.*")
                cve1 = cve_re.match(p_name)
                cve2 = cve_re.match(p_description)
                if cve1!=None:
                    dic['cve'] = cve1.group()
                elif cve2!=None:
                    dic['cve'] = cve2.group()
                else:
                    continue
                dic['p_url'] = rep1['items'][i]['html_url']
                p_pushed_at = str(rep1['items'][i]['pushed_at'])
                p_pushed_at = p_pushed_at.replace('T', ' ')
                p_pushed_at = p_pushed_at.replace('Z', '')
                dic['p_pushed_at'] = p_pushed_at
                date_strptime = time.strptime(p_pushed_at, '%Y-%m-%d %H:%M:%S')
                date_timestamp = int(time.mktime(date_strptime))
                # print(dic)
                if (new_date - date_timestamp) <= 86400:
                    update_repositories.append(dic)
        except Exception as e:
            print("["+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"]","获取GitHub API数据时出错啦！报错：", e, url)

def get_github_issues():
    for words in ('SQL Injection','Remote Code Execution','Remote Command Execution','command injection','file upload',' RCE ','vulnerability','Unauthorized','leakage','代码执行','命令执行','SQL注入','未授权','漏洞'):
        for page in range(1,11):
            time.sleep(1.5)
            url = "https://api.github.com/search/issues?q={}&sort=created&per_page=100&page={}".format("updated:>"+previous_date.strftime("%Y-%m-%d")+"+"+words,page)
            try:
                rep1 = requests.get(url, headers=headers, verify=False,timeout=20).json()
                for i in range(100):
                    dic = {}
                    dic['i_title'] = rep1['items'][i]['title']
                    dic['i_body'] = rep1['items'][i]['body']
                    user_login = rep1['items'][i]['user']['login']
                    lower_title = str(dic['i_title']).lower()
                    lower_words = words.lower()
                    if (lower_words not in lower_title) or ("401" in lower_title) or ("error" in lower_title) or ("错误" in lower_title) or ("exception" in lower_title) or ("命令执行报错" in lower_title) or ("[securityweek]" in lower_title) or ("[bug]" in lower_title) or ("同学，您这个项目引入了" in lower_title) or ("502:" in lower_title) or ("403 forbidden:" in lower_title):
                        continue
                    dic['i_url'] = rep1['items'][i]['html_url']
                    dic['words'] =  words
                    # print(rep1['items'][i])
                    # exit()
                    i_updated_at = str(rep1['items'][i]['updated_at'])
                    i_updated_at = i_updated_at.replace('T', ' ')
                    i_updated_at = i_updated_at.replace('Z', '')
                    dic['i_updated_at'] = i_updated_at
                    date_strptime = time.strptime(i_updated_at, '%Y-%m-%d %H:%M:%S')
                    date_timestamp = int(time.mktime(date_strptime))
                    # print(dic)
                    if (new_date - date_timestamp) <= 86400 and (dic['i_url'] not in issues_temp) and ("/pull/" not in dic['i_url'])  and (user_login != "magicalmouse") and ("WDavid404/OSCP/issues" not in dic['i_url']) and ("apiTesterTR/TestRepo" not in dic['i_url']) and (user_login != "rbhanda") and ("SecOpsNews/news" not in dic['i_url']) and ("[bot]" not in user_login) and ("google/tsunami-security-scanner-plugins" not in dic['i_url']):
                        update_issues.append(dic)
                        issues_temp.append(dic['i_url'])
            except Exception as e:
                print("["+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"]","获取GitHub API数据时出错啦！报错：", e, url)

def send_server(title,msg):
    if server_key != "":
        try:
            data = {"title":title,"desp":msg}
            url = 'https://sc.ftqq.com/{}.send'.format(server_key)
            requests.post(url,data=data,verify=False)
        except Exception as e:
            print("["+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"]",e)
    else:
        print('未指定server酱的key，请配置！')
        exit()
    if webhook_key != "":
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
                'Content-Type': "application/json"
            }
            msg = msg.replace('更新消息为：', '更新消息为：\n')
            msg = msg.replace('\n', '\n>')
            data = {"msgtype": "markdown","markdown": {"content":title + "\n" + ">" + msg}}
            url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={}'.format(webhook_key)
            requests.post(url,headers=headers,json=data,verify=False)
        except Exception as e:
            print("["+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"]",e)
    else:
        print('未指定企业微信机器人的key，请配置！')
        exit()

if __name__ == '__main__':
    get_github_repositories()
    get_github_issues()
    if update_issues != []:
        title = "GitHub CVE issues更新监测！"
        msg = ""
        count = 1
        count_all = 1
        with open(issue_data, mode='a', encoding='utf-8') as f:
            f.write('\n=============='+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+'==============\n')
            for i in update_issues:
                msg += "-------------------------\n"
                # msg += str(count_all) + ". CVE编号：" + str(i['cve']) + "，\n"
                msg += str(count_all) + ". issue标题：" + str(i['i_title']) + "，\n"
                msg += "issue地址：" + str(i['i_url']) + " ，\n"
                msg += "匹配关键字：" + str(i['words']) + "，\n"
                msg += "更新时间：" + str(i['i_updated_at']) + "。\n"
                if count == 10:
                    f.write(msg)
                    send_server(title,msg)
                    count = 0
                    msg = ""
                count += 1
                count_all += 1
            if msg != "":
                f.write(msg)
                send_server(title,msg)

    if update_repositories != []:
        title = "GitHub CVE POC更新监测！"
        msg = ""
        count = 1
        count_all = 1
        for i in update_repositories:
            msg += "-------------------------\n"
            msg += str(count_all) + ". CVE编号：" + str(i['cve']) + "，\n"
            msg += "项目名称：" + str(i['p_name']) + "，\n"
            msg += "项目地址：" + str(i['p_url']) + " ，\n"
            msg += "项目描述：" + str(i['p_description']) + "，\n"
            msg += "更新时间：" + str(i['p_pushed_at']) + "。\n"
            if count == 10:
                send_server(title,msg)
                count = 0
                msg = ""
            count += 1
            count_all += 1
        if msg != "":
            send_server(title,msg)

    print("===========================")
    print(update_repositories)
    print("===========================")
    print(update_issues)
    end_time = int(time.time())
    print('===========================\n['+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+']程序执行了',(end_time - new_date),'秒\n')

