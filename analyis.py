# coding=utf-8
import pandas as pd
import re
import jieba
import collections
import numpy as np
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS
import matplotlib.pyplot as plt
from PIL import Image
import pymongo
from os import path
from collections import Iterable
from bs4 import BeautifulSoup

import URLS

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["bili"]

dblist = myclient.list_database_names()
videoCol = mydb["videoList"]
danmucol = mydb["danmu"]
uppercol = mydb["upper"]

print(dblist)
if "bili" in dblist:
    print("数据库已存在！")
else:
    print("不存在")


def getItemVideoDanMu(mid):
    myquery = {"mid": mid}

    upper = uppercol.find_one(myquery)

    x = danmucol.find(myquery)
    videoAllDanmu = ''
    index = 0

    for t in x:
        if (index > 200):
            return videoAllDanmu
        if t["danmuList"] is None:
            continue
        maxDcount = 500
        dIndex = 0
        for q in t["danmuList"]:
            if (dIndex > maxDcount):
                break
            videoAllDanmu = videoAllDanmu + q["content"]
            dIndex += 1
        index += 1
    print(videoAllDanmu)
    return videoAllDanmu
    # analysis(index, upper["name"], videoAllDanmu)


def analysis(count, videoAllDanmu):
    pattern = re.compile(u'\t|\n|\.|-|:|;|\)|\(|\?|"')
    data = re.sub(pattern, '', videoAllDanmu)

    # 文本分词--精确模式分词
    seg_list_exact = jieba.cut(data, cut_all=False)
    object_list = []
    # 自定义常见去除词库
    remove_words = [u'美利坚', u'的', u'啊', u'哈', u'，', u'和', u'是', u'随着', u'对于', u'对', u'等', u'能', u'都', u'。', u' ', u'、',
                    u'中',
                    u'在', u'了',
                    u'通常', u'如果', u'我们', u'需要']
    for word in seg_list_exact:
        if word not in remove_words:
            object_list.append(word)

    # 去除单个词
    for i in range(len(object_list) - 1, -1, -1):
        if (len(object_list[i]) < 2):
            object_list.pop(i)

    # 对分词做词频统计
    word_counts = collections.Counter(object_list)
    # 获取前100最高频的词
    word_counts_top100 = word_counts.most_common(count)
    # print(word_counts_top100)
    # for i in word_counts_top100:
    #     print(i)
    return word_counts_top100


def image(interTime, maskImage, outSvg, outImage, word_counts_top100, wordCount):
    # 绘制词云
    d = path.dirname(__file__)

    alice_coloring = np.array(Image.open(path.join(d, maskImage)))
    my_wordcloud = WordCloud(
        background_color='white',  # 设置背景颜色
        mask=alice_coloring,  # 背景图片
        max_words=wordCount,  # 设置最大显示的词数
        stopwords=STOPWORDS,  # 设置停用词
        # 设置字体格式，字体格式 .ttf文件需自己网上下载，最好将名字改为英文，中文名路径加载可能会出现问题。
        font_path='sans.otf',
        max_font_size=35,  # 设置字体最大值
        # random_state=100,  # 设置随机生成状态，即多少种配色方案
        ##提高清晰度
        width=1920, height=1080,
        repeat=True,
        min_font_size=8,
    ).generate_from_frequencies(word_counts_top100)
    image_colors = ImageColorGenerator(alice_coloring)

    # 显示生成的词云图片
    plt.imshow(my_wordcloud.recolor(color_func=image_colors), interpolation="bilinear")
    plt.axis('off')
    plt.show()
    svg = my_wordcloud.to_svg(interTime)

    file = open(path.join(d, outSvg), "w", encoding="utf-8")
    file.write(svg)
    file.close()
    my_wordcloud.to_file(outImage)
    return svg


def LoadDanmuByUser():
    index = 0
    svg = ""
    REURLe = URLS.allUpper[::-1]
    for mid in REURLe:
        # if index == 10:
        #     break
        print(mid)
        myquery = {"mid": mid}
        upper = uppercol.find_one(myquery)
        # urllib_download(upper["pic"], mid, upper["name"])
        maskimage = 'face/process/big/{}-{} 拷贝.png'.format(mid, upper["name"])
        outsvg = 'face/process/svg/{}-{}.svg'.format(mid, upper["name"])

        outPic = 'face/process/pic/{}-{}.png'.format(mid, upper["name"])

        videoAllDanmu = getItemVideoDanMu(mid)
        word_counts_top100 = analysis(2000, videoAllDanmu)
        word_counts_top100.insert(0, (upper["name"], 9999999999))
        myd = dict(word_counts_top100)

        tsvg = image(index * 30, maskimage, outsvg, outPic, myd, wordCount=2000)

        tsvg += '<text x="1920" y="900" font-size="60" style="fill: WHITE"><animate attributeName="x" attributeType="XML" to="100" begin="{begin1:f}" dur="20s" fill="freeze"></animate><animate attributeName="x" attributeType="XML" to="-1920.000000" begin="{begin2:f}" dur="20s" fill="freeze"></animate>{name}</text>'.format(
            begin1=index * 30, begin2=index * 30 + 40, name=upper["name"])

        svg += tsvg
        index += 1

    file = open("final.svg", "w", encoding="utf-8")
    file.write(svg)
    file.close()

#下载图片
def urllib_download(IMAGE_URL, mid, name):
    from urllib.request import urlretrieve
    print(IMAGE_URL[-3:])
    urlretrieve(IMAGE_URL, 'face/{}-{}.{}'.format(mid, name, IMAGE_URL[-3:]))


def readsvg(fileName, newfileName, timeRedece):
    oldFile = open(fileName, encoding="utf-8")
    content = oldFile.read()
    oldFile.close()
    newFile = open(newfileName, "w", encoding="utf-8")
    bs = BeautifulSoup(content)
    a = bs.find_all(name="animate")
    for item in a:
        # item.get("begin")
        old = item.get("begin")
        new = "{}s".format(float(item.get("begin")[:-1]) - timeRedece)
        # print(new)
        content = content.replace(old, new)
    newFile.write(content)
    newFile.close()
    return content


def mofisvg():
    index = 0
    svg = ""
    REURLe = URLS.allUpper[::-1]
    svgContent10 = ""
    for mid in REURLe:
        # if index == 2:
        #     break
        myquery = {"mid": mid}
        upper = uppercol.find_one(myquery)
        # urllib_download(upper["pic"], mid, upper["name"])
        outsvg = 'face/process/svg/{}-{}.svg'.format(mid, upper["name"])
        outsvg2 = 'face/process/svgprocess/{}-{}.svg'.format(mid, upper["name"])

        d = path.dirname(__file__)
        oldSVg = path.join(d, outsvg)
        newSVg = path.join(d, outsvg2)
        retime=0
        if index>=10:
            retime = int(index/10)*10*30
        else:
            retime = 0

        print(retime,"**********************************")
        tsvg = readsvg(oldSVg, newSVg, retime, ).replace("</svg>", "")
        tsvg += '<text x="1920" y="900" font-size="60" style="fill: WHITE"><animate attributeName="x" attributeType="XML" to="100" begin="{begin1:f}" dur="20s" fill="freeze"></animate><animate attributeName="x" attributeType="XML" to="-1920.000000" begin="{begin2:f}" dur="20s" fill="freeze"></animate>{name}</text>'.format(
            begin1=(index%10 )* 30, begin2=(index%10 )*30+40, name=upper["name"])

        svgContent10 += tsvg
        if (index >= 9 and index % 9 == 0) or index == (len(REURLe) - 1):
            print(index,"-------------------------------------")
            svgContent10 = svgContent10.replace(
                '''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" style='font-family: "Noto Sans CJK"; font-weight: normal; font-style: normal'>''',
                "").replace('''<rect width="100%" height="100%" style="background: white"></rect>''', "")
            svgContent10='''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" style='font-family: "Noto Sans CJK"; font-weight: normal; font-style: normal'>'''+'''<rect width="100%" height="100%" style="background: white"></rect>'''+svgContent10
            svgContent10 += "</svg>"
            outsvg10 = 'face/process/svg10/{}-{}.svg'.format(100 - index + 10, 100 - index)
            newSVg10 = path.join(d, outsvg10)
            fileNewSVg10 = open(newSVg10, "w", encoding="utf-8")
            fileNewSVg10.write(svgContent10)
            svgContent10 = ""
        svg += tsvg
        index += 1

    file = open("final.svg", "w", encoding="utf-8")
    file.write(svg)
    file.close()
def makeend():
    # 绘制词云
    d = path.dirname(__file__)
    maskImage="face/process/end.png"
    outSvg="face/process/endsvg.svg"
    outImage="face/process/endout.png"
    alice_coloring = np.array(Image.open(path.join(d, maskImage)))
    my_wordcloud = WordCloud(
        # background_color='white',  # 设置背景颜色
        mask=alice_coloring,  # 背景图片
        max_words=10000000,  # 设置最大显示的词数
        stopwords=STOPWORDS,  # 设置停用词
        # 设置字体格式，字体格式 .ttf文件需自己网上下载，最好将名字改为英文，中文名路径加载可能会出现问题。
        font_path='sans.otf',
        max_font_size=30,  # 设置字体最大值
        random_state=100,  # 设置随机生成状态，即多少种配色方案
        ##提高清晰度
        width=1920, height=1080,
        repeat=True,
        min_font_size=10,
    ).generate_from_text("哔哩哔哩 (゜-゜)つロ 干杯~-bilibili")

    image_colors = ImageColorGenerator(alice_coloring)

    # 显示生成的词云图片
    plt.imshow(my_wordcloud.recolor(color_func=image_colors), interpolation="bilinear")
    plt.axis('off')
    plt.show()
    svg = my_wordcloud.to_svg(0)

    file = open(path.join(d, outSvg), "w", encoding="utf-8")
    file.write(svg)
    file.close()
    my_wordcloud.to_file(outImage)

# LoadDanmuByUser()
# mofisvg()
makeend()

# readsvg()
# print(int(22/10))
# for index in range(100):
#     retime = index * 30 + index % 10 * 10
#     print(retime)
