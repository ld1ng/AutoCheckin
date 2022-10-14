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

def fetch_lecture(hd_wid: str, ss, ver_code):
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/yySave.do"
    data_json = {'HD_WID': hd_wid, 'vcode': ver_code}
    form = {"paramJson": json.dumps(data_json)}
    r = ss.post(url, data=form)
    result = r.json()
    if result['success'] is not False:
        print(result)
        # sys.exit(0)
    return result['code'], result['msg'], result['success']


def get_code(ss):
    c_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/vcode.do"
    c = ss.get(c_url)
    c_r = c.json()
    c_img = base64.b64decode(c_r['result'].split(',')[1])
    c = ocr.classification(c_img)
    return c, c_img

def get_lecture_list(ss):
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/*default/index.do#/hdyy"
    ss.get(url)
    # url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxs.do"
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/queryActivityList.do"
    form = {"pageIndex":1,"pageSize":10 ,"sortField": "YYKSSJ","sortOrder":"asc"}
    r = ss.post(url, data=form)
    response = r.json()
    rows = response['datas']
    return rows

# def get_lecture_info(w_id, ss):
#     url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxq_cx.do"
#     data_json = {'WID': w_id}
#     r = ss.post(url, data=data_json)
#     try:
#         result = r.json()['datas']['hdxxxq_cx']['rows'][0]
#         return result
#     except Exception:
#         print("信息获取失败")
#         return False

def checkdate(lecture):
    current_time = time.strftime("%Y-%m-%d")
    begin_time = lecture['YYKSSJ'].split(" ")[0]
    if(current_time == begin_time):
        return 1
    else:
        print("[" + current_time + "] " + "最近的线上讲座在" + begin_time)
        return 0


def startRob(s):
    lecture_list = get_lecture_list(s)
    for index, lecture in enumerate(lecture_list):
        print('序号：' + str(index))
        print("讲座wid：" + lecture['WID'])
        print("讲座名称：" + lecture['JZMC'])
        print("预约开始时间：" + lecture['YYKSSJ'])
        print("预约结束时间：" + lecture['YYJSSJ'])
        print("讲座时间：" + lecture['JZSJ'])
        print("讲座地点: " + lecture['JZDD'])
        print("==========================================")
        if(lecture['JZDD'] == "钉钉" or lecture['JZDD'] == "腾讯会议" or lecture['JZDD'] =="双创中心网站（https://www.seuiec.com）"):
            if(not checkdate(lecture)):
                print("预约未开放！")
                sys.exit(0)
            v_code, _ = get_code(s)
            # print(v_code)
            i = 1
            while True:
                if(int(lecture['YYRS'])>=int(lecture['HDZRS'])):
                    print("人数已满！")
                    break
                code, msg, success = fetch_lecture(lecture['WID'],s,v_code)
                print('第{}次请求,code：{},msg：{},success:{}'.format(i, code, msg, success))
                if success:
                    sendmail(0,"[*] 抢课成功!","***")
                    break
                if msg == '验证码错误！':
                    v_code = get_code(s)
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
                startRob(ss)
            cnt+=1
    except Exception:
        print("[*] 抢讲座完成，共"+str(cnt-1)+"个用户.\n")
        exit(0)
