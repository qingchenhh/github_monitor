import sqlite3
import requests, time, os
import warnings
warnings.filterwarnings('ignore')

# 以下需要配置以下！
# -----------------------------------
tools_path = "tools.txt" # 工具列表文件
github_token = "xxx" # GitHub token
server_key = "xxx" # server酱的SendKey
# -----------------------------------

def create_db():
    if os.path.exists('data.db'):
        print('数据库已存在！')
        # os.remove('data.db')
        conn = sqlite3.connect('data.db')
        return conn.cursor(),conn
        # return True
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS tools
                (tools_name varchar(255),
                commit_date_timestamp varchar(255),
                tools_url varchar(255),
                releases varchar(255),
                releases_time varchar(255),
                author varchar(255));''')
        print("工具表创建成功！")
    except Exception as e:
        print("工具表创建出错啦！报错：",e)
    conn.commit()
    return c,conn

def get_timestamp(date):
    date = date.replace('T', ' ')
    date = date.replace('Z', '')
    date_strptime = time.strptime(date, '%Y-%m-%d %H:%M:%S')
    date_timestamp = str(int(time.mktime(date_strptime)))
    return date_timestamp

def get_github_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
        'Authorization': "token {}".format(github_token)
    }
    proxies = {
        'http':'http://127.0.0.1:8080'
    }
    dic = {}
    try:
        rep1 = requests.get(url, headers=headers, verify=False).json()
        # print(rep1)
        dic['tools_name'] = rep1['name']
        dic['tools_url'] = rep1['html_url']
        dic['author'] = rep1['owner']['login']
        rep = requests.get(url+"/commits", headers=headers, verify=False).json()
        dic['html_url'] = rep[0]['html_url']
        commit_date = rep[0]['commit']['committer']['date']
        commit_message = rep[0]['commit']['message']
        dic['commit_message'] = str(commit_message).replace('#',"%23")

        # print(tools_name,tools_url,html_url,commit_date,commit_message)
        dic['commit_date_timestamp'] = get_timestamp(commit_date)

        dic['releases'] = "0"
        dic['releases_time'] = "0"
        dic['releases_url'] = "0"
        release_rep = requests.get(url+"/releases", headers=headers, verify=False).json()
        if release_rep :
            dic['releases'] = release_rep[0]['tag_name']
            dic['releases_time'] = get_timestamp(release_rep[0]['published_at'])
            dic['releases_url'] = release_rep[0]['html_url']

        # print(tools_name,tools_url,html_url,commit_date_timestamp,commit_message,releases,releases_time,releases_url)
        # print(dic)
        return dic

    except Exception as e:
        print("获取GitHub API数据时出错啦！报错：", e)

def send_server(title,msg):
    try:
        print("===========================")
        print(title)
        print(msg)
        uri = 'https://sc.ftqq.com/{}.send?text={}&desp={}'.format(server_key, title, msg)
        requests.get(uri)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    db,conn = create_db()
    if not os.path.exists(tools_path):
        print("没有找到要监测的工具的列表文件！")
        exit()
    # print(get_github_data("https://api.github.com/repos/jeroennijhof/vncpwd"))
    # print(get_github_data("https://api.github.com/repos/x0rz4/vncpwd"))
    while True:
        with open(tools_path,mode='r',encoding='utf-8') as f:
            for i in f:
                api_url = i.replace('\n','')
                tools_data = get_github_data(api_url)
                # 排除工具404的情况
                if tools_data == None:
                    continue
                query_sql = "select tools_name,commit_date_timestamp,tools_url,releases,releases_time,author from tools where tools_name='{}' and author='{}'".format(tools_data['tools_name'],tools_data['author'])
                db.execute(query_sql)
                query_result = db.fetchall()
                # print(query_result)
                if query_result != []:
                    query_result = query_result[0]
                if not query_result:
                    print("数据库中不存在" + tools_data['tools_name'] + "工具，将会插入数据！")
                    insert_sql = "insert into tools (tools_name,commit_date_timestamp,tools_url,releases,releases_time,author) values ('{}','{}','{}','{}','{}','{}')".format(tools_data['tools_name'],tools_data['commit_date_timestamp'],tools_data['tools_url'],tools_data['releases'],tools_data['releases_time'],tools_data['author'])
                    # print(insert_sql)
                    db.execute(insert_sql)
                    conn.commit()
                elif (int(query_result[1]) < int(tools_data['commit_date_timestamp'])):
                    if tools_data['releases'] == "0":
                        title = "**" + tools_data['tools_name'] + "**更新啦！"
                        msg = "工具地址为：" + tools_data['tools_url'] + " ，更新消息为：" + tools_data['commit_message'] + " ，更新详情查看：" + tools_data['html_url'] + " ，工具不存在release版本！"
                        update_sql = "update tools set commit_date_timestamp='{}' where tools_name='{}' and author='{}'".format(tools_data['commit_date_timestamp'],tools_data['tools_name'],tools_data['author'])
                    elif int(query_result[4]) < int(tools_data['releases_time']):
                        title = "**" + tools_data['tools_name'] + "**更新啦！"
                        msg = "工具地址为：" + tools_data['tools_url'] + " ，更新消息为：" + tools_data['commit_message'] + " ，更新详情查看：" + \
                              tools_data['html_url'] + " 。工具存在release版本，且版本也更新啦！release最新版本为：" + tools_data[
                                  'releases'] + " ，下载地址为：" + tools_data['releases_url']
                        update_sql = "update tools set commit_date_timestamp='{}',releases='{}',releases_time='{}' where tools_name='{}' and author='{}'".format(
                            tools_data['commit_date_timestamp'], tools_data['releases'], tools_data['releases_time'],
                            tools_data['tools_name'],tools_data['author'])
                    else:
                        title = "**" + tools_data['tools_name'] + "**更新啦！"
                        msg = "工具地址为：" + tools_data['tools_url'] + " ，更新消息为：" + tools_data['commit_message'] + " ，更新详情查看：" + \
                              tools_data['html_url'] + " ，工具存在release版本，但release版本未更新！"
                        print(tools_data['commit_date_timestamp'])
                        update_sql = "update tools set commit_date_timestamp='{}' where tools_name='{}' and author='{}'".format(
                            tools_data['commit_date_timestamp'], tools_data['tools_name'], tools_data['author'])
                    send_server(title, msg)
                    db.execute(update_sql)
                    conn.commit()
                elif int(query_result[4]) < int(tools_data['releases_time']):
                    title = "**" + tools_data['tools_name'] + "**更新啦！"
                    msg = "该工具没有commits，但release版本更新啦！release最新版本为：" + tools_data[
                                  'releases'] + " ，下载地址为：" + tools_data['releases_url']
                    update_sql = "update tools set releases='{}',releases_time='{}' where tools_name='{}' and author='{}'".format(tools_data['releases'], tools_data['releases_time'], tools_data['tools_name'], tools_data['author'])
                    send_server(title, msg)
                    db.execute(update_sql)
                    conn.commit()
        time.sleep(60*3)
