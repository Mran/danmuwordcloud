import requests
import json
import pymongo
import time
import URLS
import datetime
from bs4 import BeautifulSoup

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["bili"]

dblist = myclient.list_database_names()
videoCol = mydb["videoList"]
danmucol = mydb["danmu"]

print(dblist)
if "bili" in dblist:
    print("数据库已存在！")
else:
    print("不存在")
# 构建所有的url
allUrls = [
    # URLS.remenRid,
    URLS.donghuaRid,
    URLS.guochuangRid,
    URLS.yinyueRid,
    URLS.wudaoRid,
    URLS.youxiRid,
    URLS.kejiRid,
    URLS.shumaRid,
    URLS.shenghuoRid,
    URLS.guichuRid,
    URLS.shishangRid,
    URLS.yuleRid,
    URLS.yingshiRid,
]


def loadAllVideosList():
    urlTemplate = "https://api.bilibili.com/x/web-interface/ranking?rid=4&day=7&type=1&arc_type=0&jsonp=json"

    for rid in allUrls:
        print(rid)
        url = "https://api.bilibili.com/x/web-interface/ranking?rid={}&day=7&type=1&arc_type=0&jsonp=json".format(rid)
        print(url)
        # break
        respone = requests.get(url)
        videoList = respone.content.decode("utf-8")
        re = json.loads(videoList)
        print(re)
        index = 1
        for item in re["data"]["list"]:
            videoItem = {}

            videoItem["aid"] = item["aid"]
            # 作者
            videoItem["author"] = item["author"]
            # 硬币
            videoItem["coins"] = item["coins"]
            # 封面
            videoItem["pic"] = item["pic"]
            # 标题
            videoItem["title"] = item["title"]

            videoItem["cid"] = item["cid"]
            # 播放量
            videoItem["play"] = item["play"]
            # 平均得分
            videoItem["pts"] = item["pts"]
            # 弹幕量
            videoItem["video_review"] = item["video_review"]
            videoItem["rid"] = rid
            videoItem["timeStmp"] = "{}".format(datetime.date.today())
            videoItem["rank"] = index
            index += 1
            videoCol.insert_one(videoItem)
            loadDanmu(item["cid"])


def loadDanmu(oid):
    # oid就是av号，也就是cid
    allDanmuList = {}
    videoDanmu = {}

    # 获取7天的的弹幕
    for i in range(7):
        tagDate = datetime.date.today() - datetime.timedelta(days=i)
        urlTemplate = "https://api.bilibili.com/x/v2/dm/history?type=1&oid={}&date={}".format(oid, tagDate)
        re = requests.get(urlTemplate, headers={
            'Cookie': 'buvid3=AA4640DB-37B1-4A91-A9E6-3D30D2CEC7D640787infoc; LIVE_BUVID=AUTO3715658388108669; CURRENT_FNVAL=16; sid=a1zc5l64; stardustvideo=1; DedeUserID=9102496; DedeUserID__ckMd5=6b1cac7c8021d37f; SESSDATA=dc57a127%2C1568430868%2C01366a81; bili_jct=cfddfe05beed584e63efc4dce0a7e73a'})
        danmuXml = re.content.decode("utf-8")
        soup = BeautifulSoup(danmuXml, "html.parser")
        danmList = soup.find_all("d")
        for item in danmList:
            danmuDetail = {}
            res = item.get("p").split(",")
            danmuDetail["rid"] = oid
            danmuDetail["uid"] = res[3]
            danmuDetail["timeStamp"] = res[4]
            danmuDetail["did"] = res[7]
            danmuDetail["content"] = item.get_text()
            allDanmuList[res[7]] = danmuDetail
    videoDanmu["rid"] = oid
    kk = list(allDanmuList.values())

    videoDanmu["danmuList"] = kk

    x = danmucol.insert_one(videoDanmu)
    
    print(oid)


# 获取可用的弹幕月份
def loadDanmuMouth():
    print("loadDanmuMouth")
    # x = videoCol.insert_one(videoItem)


if __name__ == '__main__':
    # print(datetime.date.today() - datetime.timedelta(days=1))
    # loadAllVideosList()
    loadDanmu("108485733")
    print("ok")
