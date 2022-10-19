import base64
import json
import argparse
import sys
import time
import ddddocr
from login import login
from dayReport import sendmail
ocr = ddddocr.DdddOcr()

with open("./config.json", "r", encoding="utf-8") as f:
    configs = f.read()
configs = json.loads(configs)

def get_code(ss):
    c_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/vcode.do"
    c = ss.get(c_url)
    c_r = c.json()
    c_img = base64.b64decode(c_r['result'].split(',')[1])
    c = ocr.classification(c_img)
    return c, c_img

def get_leclist(ss):
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/*default/index.do#/hdyy"
    ss.get(url)
    # url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxs.do"
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/queryActivityList.do"
    form = {"pageIndex":1,"pageSize":10 ,"sortField": "YYKSSJ","sortOrder":"asc"}
    r = ss.post(url, data=form)
    response = r.json()
    rows = response['datas']
    return rows

def catch_lec(hd_wid: str, ss, ver_code):
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/yySave.do"
    data_json = {'HD_WID': hd_wid, 'vcode': ver_code}
    form = {"paramJson": json.dumps(data_json)}
    r = ss.post(url, data=form)
    result = r.json()
    if result['success'] is True:
        print(result)
        # sendmail(0,"[*] 抢课成功!","***")
        sys.exit(0)
    return result['code'], result['msg'], result['success']

def checkdate(lecture):
    currtime = time.strftime("%Y-%m-%d")
    startime = lecture['YYKSSJ'].split(" ")[0]
    begintime = int(time.mktime(time.strptime(lecture['YYKSSJ'], "%Y-%m-%d %H:%M:%S")))
    if(currtime == startime):
        while(int(time.time()) < begintime):
            # print("请等待[" + str(begintime - int(time.time())) + "]秒，马上开始！")
            time.sleep(1)
        print(time.ctime(),"开始抢课！")
        return 1
    else:
        print("[" + currtime + "] " + "最近的线上讲座在" + startime)
        return 0

def lecINFO(idx,lec):
    print('序号：' + str(idx))
    print("讲座wid：" + lec['WID'])
    print("讲座名称：" + lec['JZMC'])
    print("预约开始时间：" + lec['YYKSSJ'])
    print("预约结束时间：" + lec['YYJSSJ'])
    print("讲座时间：" + lec['JZSJ'])
    print("讲座地点: " + lec['JZDD'])
    print("================================================")

def startRob(s):
    lecture_list = get_leclist(s)
    for idx, lecture in enumerate(lecture_list):
        lecINFO(idx,lecture)
        if(lecture['JZDD'] == "钉钉" or lecture['JZDD'] == "腾讯会议" or lecture['JZDD'] =="双创中心网站（https://www.seuiec.com）"):
            if(not checkdate(lecture)):
                print("[*] 预约未开放！\n")
                sys.exit(0)
            v_code, _ = get_code(s)
            # print(v_code)
            i = 1
            while (i<=11):
                if(int(lecture['YYRS'])==int(lecture['HDZRS'])):
                    print("[*] 人数已满！")
                    break
                code, msg, success = catch_lec(lecture['WID'],s,v_code)
                print('第{}次请求,code：{},msg：{},success:{}'.format(i, code, msg, success))
                if '验证码错误' in msg:
                    v_code, _ = get_code(s)
                time.sleep(0.5)
                i += 1

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
    try:
        while(configs['user']['user'+ str(cnt)]):
            ss = login(configs['user']['user'+ str(cnt)]['cardnum'], configs['user']['user'+ str(cnt)]['password'])
            if ss:
                try:
                    startRob(ss)
                except Exception as e:
                    print(repr(e))
                    continue
            else:
                continue
            cnt+=1
    except Exception as e:
        print(repr(e))
        print("[*] 抢讲座完成，共"+str(cnt-1)+"个用户.\n")
        exit(0)
