
from urllib.parse import urlencode
import requests
from pyquery import PyQuery as pq
import pymongo
from multiprocessing import Pool
client = pymongo.MongoClient('localhost')
db = client['wechat']

headers = {
        "Cookie":"SUV=1530457850134756; SMYUV=1530457850144486; UM_distinctid=164566581db55b-041fd0d58d549a-47e1039-1fa400-164566581dd287; IPLOC=CN4201; SUID=D42A97755118910A000000005B48D04E; ABTEST=0|1535720678|v1; weixinIndexVisited=1; sct=2; JSESSIONID=aaa6T8_oNz9HheeVaEBvw; PHPSESSID=53008ncfgsjl3dqch3g1eev5m0; SUIR=2FFB27CBBEBACA046B39C4EFBF48A4ED; SNUID=F622FE12676213DB7E5BB7B567435E0B; ppinf=5|1535731477|1536941077|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToxOlR8Y3J0OjEwOjE1MzU3MzE0Nzd8cmVmbmljazoxOlR8dXNlcmlkOjQ0Om85dDJsdVBtX0dlbERyamEtczMtTDJzOElVTk1Ad2VpeGluLnNvaHUuY29tfA; pprdig=Inoly7HSuZWpshBBjiaL36xV0rwoZ1JV8Rdd4DIuXAM7OkdbBxRVUc_zflQfQzbXT7Sejo27K5noYoCstIsXBBZlNCIa-fig5DrGzhoQ1pqaPP-T2lOj4wkK8I0heRR43xgHkq-fYPmiYOuDRWT_J88GjUDfuS4JjloUCTVHPSo; sgid=20-36870753-AVuJZxXFIoCdHtOnZv8xpYo; ppmdig=153573147700000082de4215367513c256505ebd540c56e4",
        "Host":"weixin.sogou.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
        "X-Requested-With":"XMLHttpRequest"
    }
wechat_url = "http://weixin.sogou.com/weixin?"
proxy = None
Max_count = 10
def get_proxies():
    try:
        response = requests.get("http://127.0.0.1:5555/random")
        if response.status_code == 200:
            return response.text
        return get_proxies()
    except ConnectionError:
        return get_proxies()
def get_text(url,count = 1):
    print("请求地址",url)
    print("请求次数",count)
    global proxy
    # if count >= Max_count:
    #     print("请求失败超过最大值")
    #     return None
    try:
        if proxy:
            proxys = {
                'http':'http://' + proxy
            }
            response = requests.get(url,allow_redirects=False,headers=headers,proxies=proxys)
        else:
            response = requests.get(url, allow_redirects=False, headers=headers)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            print(response.status_code)
            proxy = get_proxies()
            if proxy:
                print("使用代理:", proxy)
                return get_text(url,count)
            else:
                print("获取代理失败")
                return None
    except Exception as e:
        print("Error",e.args)
        count +=1
        proxy = get_proxies()
        return get_text(url,count)
def create_url(TITLE,PAGE):
    if TITLE and PAGE:
        data = {
            "query":TITLE,
            "type":2,
            "page":PAGE,
            'ie':'utf8'
        }
        url = wechat_url + urlencode(data)
        return url
def parse_text(text):
    if text:
        doc = pq(text)
        items = doc('.news-box .news-list .txt-box h3 a').items()
        for item in items:
            yield item.attr('href')

def get_article(item):
    if item:
        response = requests.get(item)
        if response.status_code == 200:
            return response.text
        return None
def parser_article(html):
    if html:
        apq = pq(html)
        title = apq(".rich_media_title").text()
        authoer = apq(".rich_media_meta a").text()
        article = apq(".rich_media_content").text()
        return {
            "title":title,
            "authoer":authoer,
            "article":article,
        }
def save_to_mongo(result):
    if db['wechat_massage'].update({'title':result['title']},{'$set':result},True):
        print("数据存储到数据库成功",result['title'])
    else:
        print("数据存储失败",result['title'])

def main(PAGES):
    TITLE = "风景"
    url = create_url(TITLE, PAGES)
    text = get_text(url)
    items = parse_text(text)
    get_queue(items)
def get_queue(items):
    if items:
        for item in items:
            html = get_article(item)
            result = parser_article(html)
            save_to_mongo(result)
if __name__ == "__main__":
    pool = Pool(3)
    for i in range(1, 101):
         result = pool.apply_async(main,(i,))
    result.wait()
    pool.close()
    pool.join()