# encoding=utf-8
import argparse
import datetime
import json
import random
import pytz
import smtplib
from bs4 import BeautifulSoup
from login import login
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 加载全局配置
with open("./config.json", "r", encoding="utf-8") as f:
    configs = f.read()
configs = json.loads(configs)

def sendmail(flag):
    msg_from = '***@***.com'  # 发送方邮箱
    passwd = '***'            # 授权码
    to = [configs['user']['user'+str(cnt)]['email']] # 接受方邮箱
    #设置邮件内容
    msg = MIMEMultipart()
    if(flag == 0):
        content = "[√] 打卡成功！"
    else:
        content = "[*] 打卡失败！"
    #把内容加进去
    msg.attach(MIMEText(content,'plain','utf-8'))
    #设置邮件主题
    msg['Subject'] = "东大信息化每日自动打卡"
    #发送方信息
    msg['From'] = msg_from
    #通过SSL方式发送，服务器地址和端口
    s = smtplib.SMTP_SSL("smtp.qq.com", 465)
    # 登录邮箱
    s.login(msg_from, passwd)
    s.sendmail(msg_from,to,msg.as_string())
    print("邮件发送成功\n")

def load_params(ss, mode):
    json_form = get_report_data(ss)  # 获取昨日填报信息
    params = {
        "DZ_JSDTCJTW": 36.5,         # 晨检体温
        "DZ_DBRQ": "%Y-%m-%d",       # 对比日期，取昨天
        "CZRQ": "%Y-%m-%d %H:%M:%S", # 操作日期
        "CREATED_AT": "%Y-%m-%d %H:%M:%S",# 创建时间
        "NEED_CHECKIN_DATE": "%Y-%m-%d"   # 校验时间
    }
    params["DZ_JSDTCJTW"] = 36 + random.randint(1, 7) / 10
    if mode != '':
        try:
            local = configs['dailyReport'][mode]
            params.update(local)         # 配置文件覆盖掉昨日信息
        except Exception:
            print("[加载本地配置失败，使用昨日信息进行填报]")
    else:
        print("[使用昨日信息进行填报]")

    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)

    today_list = ['CZRQ', 'CREATED_AT', 'NEED_CHECKIN_DATE']
    yesterday_list = ['DZ_DBRQ']
    for key in params.keys():
        # 填充日期
        if key in yesterday_list:
            params[key] = yesterday.strftime(params[key])
        elif key in today_list:
            params[key] = today.strftime(params[key])
        json_form[key] = params[key]
    # print(params)
    return json_form

def doReport(session, mode=''):
    # 进入填报页面(获取sessionid)
    session.get("http://ehall.seu.edu.cn/appShow?appId=5821102911870447") # 健康打卡

    url = 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/mobile/dailyReport/T_REPORT_EPIDEMIC_CHECKIN_SAVE.do'

    json_form = load_params(session, mode)

    res = session.post(url, data=json_form)
    try:
        if json.loads(res.text)['datas']['T_REPORT_EPIDEMIC_CHECKIN_SAVE'] == 1:
            print("填报成功！")
            return 0
        else:
            print("填报失败！")
            return 1
    except Exception:
        soup = BeautifulSoup(res.text, "html.parser")
        tag = soup.select('.underscore.bh-mt-16')
        if len(tag) > 1:
            print(tag[0].text.replace('\n', ''))
        else:
            print(res.text)
        print("填报失败！")

# 获取昨日填报信息
def get_report_data(ss):
    # 进入填报页面sessionid
    ss.get("http://ehall.seu.edu.cn/appShow?appId=5821102911870447")
    latest_url = "http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/modules/dailyReport/getLatestDailyReportData.do"
    wid_url = "http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/mobile/dailyReport/getMyTodayReportWid.do" 
    userinfo_url = "http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/api/base/getUserDetailDB.do" 
    last_res = ss.get(latest_url)
    wid_res = ss.get(wid_url)
    userinfo_res = ss.post(userinfo_url)
    try:
        tempFormData = {}
        userInfo = json.loads(userinfo_res.text)['data']
        # 载入当天填报模板
        try:
            wid_data = json.loads(
                wid_res.text)['datas']['getMyTodayReportWid']['rows'][0]
            tempFormData.update(last_report)
            tempFormData['DZ_DQWZ_QX'] = last_report['LOCATION_COUNTY_CODE_DISPLAY']
            tempFormData['DZ_DQWZ_SF'] = last_report['LOCATION_PROVINCE_CODE_DISPLAY']
            tempFormData['DZ_DQWZ_CS'] = last_report['LOCATION_CITY_CODE_DISPLAY']
            tempFormData['DZ_DQWZ'] = last_report['LOCATION_PROVINCE_CODE_DISPLAY'] + ', ' + last_report['LOCATION_CITY_CODE_DISPLAY'] + ', ' + last_report['LOCATION_COUNTY_CODE_DISPLAY']

        except Exception:
            print('【getMyTodayReportWid FAILED】')

        # 载入昨日填报信息
        try:
            last_report = json.loads(
                last_res.text)['datas']['getLatestDailyReportData']['rows'][0]
            tempFormData.update(last_report)
        except Exception:
            print('getLatestDailyReportData FAILED】')
            raise

        # 载入用户信息
        tempFormData['USER_ID'] = configs['user']['user'+ str(cnt)]['cardnum']
        # tempFormData['PHONE_NUMBER'] = userInfo['PHONE_NUMBER']
        tempFormData['IDCARD_NO'] = userInfo['IDENTITY_CREDENTIALS_NO']
        tempFormData['GENDER_CODE'] = userInfo['GENDER_CODE']
        # tempFormData['CLASS_CODE'] = userInfo['CLASS_CODE']
        # tempFormData['CLASS'] = userInfo['CLASS']
        tempFormData['RYSFLB'] = userInfo['RYSFLB']        # 身份类别
        tempFormData['USER_NAME'] = userInfo['USER_NAME']
        tempFormData['DEPT_CODE'] = userInfo['DEPT_CODE']  # 学院编号
        tempFormData['DEPT_NAME'] = userInfo['DEPT_NAME']
    except Exception as e:
        print(e)
        print("[获取填报信息失败，请手动填报]")
        exit()
    # print(tempFormData)
    return tempFormData

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test for argparse')
    parser.add_argument(
        '--config', '-c', help='采用的配置名称 如 school, home', default='')
    parser.add_argument(
        '--user', '-u', help='一卡通号', default='')
    parser.add_argument(
        '--password', '-p', help='密码', default='')

    args = parser.parse_args()
    cnt = 1
    # 覆盖账号信息
    if args.user != '' and args.password != '':
        configs['user']['user'+ str(cnt)]['cardnum'] = args.user
        configs['user']['user'+ str(cnt)]['password'] = args.password

    today = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
    print(today)
    try:
        while(configs['user']['user'+ str(cnt)]):
            ss = login(configs['user']['user'+ str(cnt)]['cardnum'], configs['user']['user'+ str(cnt)]['password'])
            if ss:
                # doReport(ss,args.config)
                sendmail(doReport(ss, args.config))
            cnt+=1
    except Exception:
        print("[*] 打卡完成，共"+str(cnt-1)+"个用户.")
        exit(0)
