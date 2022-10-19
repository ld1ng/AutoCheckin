# encoding=utf-8
import requests
import json
from bs4 import BeautifulSoup
from encrypt import AESencrypt

# 登录信息门户
def login(cardnum, password):
    ss = requests.Session()
    form = {"username": cardnum}
    headers = {'Content-Type': 'application/x-www-form-urlencoded',
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}
    ss.headers = headers

    #  获取登录页面表单，解析隐藏值
    url = "https://newids.seu.edu.cn/authserver/login?goto=http://my.seu.edu.cn/index.portal"
    res = ss.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    attrs = soup.select('[tabid="01"] input[type="hidden"]')
    for k in attrs:
        if k.has_attr('name'):
            form[k['name']] = k['value']
        elif k.has_attr('id'):
            form[k['id']] = k['value']
    form['password'] = AESencrypt(password, form['pwdDefaultEncryptSalt'])
    # 登录认证
    res = ss.post(url, data=form)

    # 登录综合服务大厅sessionid
    res = ss.get('http://ehall.seu.edu.cn/login?service=http://ehall.seu.edu.cn/new/index.html')
    # print(res)
    # 获取登录信息
    res = ss.get('http://ehall.seu.edu.cn/jsonp/userDesktopInfo.json')

    json_res = json.loads(res.text)
    try:
        name = json_res["userName"]
        if(name):
            print("[*] " + time.strftime("%Y-%m-%d %H:%M:%S") ,name[0], "** 登陆成功！")
            return ss
        else:
            return False
    except Exception as e:
        print(repr(e))
        print("认证失败！")
        return False
