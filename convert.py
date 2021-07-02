import re
import requests

ALPHABET = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
    "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
]

def convert(url):
    # 无论如何，微博是不会愿意把链接跳到电脑端的
    # 但是由于国际版链接混乱的跳转机制，就在这里先等它跳转完
    r = requests.head(url, allow_redirects=True)
    urls = []
    for req in r.history:
        urls.append(req.url)
    urls.append(url)
    for i, url in enumerate(urls):
        # 桌面端url，最好的情况了
        if re.search(r"weibo.com/\d+?/[0-9a-zA-Z]+", url):
            return url
        # 这个链接目前不会跳转，且一定指向国际版页面
        if "share.api.weibo.c" in url:
            return convert_intl(url)
        # 这个链接不一定指向国际版页面，可能存在跳转，非最后一次跳转不按照国际版处理
        if "weibointl.api.weibo.c" in url and i == len(urls)-1:
            return convert_intl(url)
        # 看到第一次立刻拿走，有可能是老国际版链接跳转
        if "m.weibo.cn" in url:
            # 手机版链接，（可能）需要一次访问以获取 uid
            return convert_m(url)
    
def convert_intl(url, r=None):
    r = requests.get(url)
    # 国际版链接提取 mid
    if (match := re.search(r"weibo_id=(\d+)", url)):
        # url 中已给出 mid，直接利用 mid 转换
        mid = match.group(1)
    else:
        # 实验性特性：在 url 中未给出 mid 时，使用“App 内打开”按钮获取 mid
        mid_pattern = r"<a .*?href=\"javascript:void\(0\)\" .*?onclick=\"forward\(0,(\d+),''\)\".*?><span.*?>App 内打开</span>.*?</a>"
        if (match := re.search(mid_pattern, r.text)):
            mid = match.group(1)
        else:
            raise ValueError("This url is not supported.")

    if (match := re.search(r"<header.*>.*?</header>", r.text)):
        header_content = match.group(0)
        uid_pattern = r"<a .*?href=\"javascript:void\(0\)\" .*?onclick=\"forward\((\d+),0,''\)\".*?><img.*?>.*?</img>.*?</a>"
        if (match := re.search(uid_pattern, header_content)):
            uid = match.group(1)
        else:
            uid = get_uid_from_m_page(mid)
    else:
        uid = get_uid_from_m_page(mid)
    return generate_url(uid, convert_mid(mid))

def convert_m(url, r=None):
    # 手机版链接
    # 情况1.1：手机版链接自带uid，数字mid，只需简单转换mid即可返回
    if (match := re.search(r"(\d+)/(\d{16})", url)):
        uid, mid = match.group(1), match.group(2)
        return generate_url(uid, convert_mid(mid))
    # 情况1.2：手机版链接自带uid，字母数字混合mid，只需简单拼接即可返回
    if (match := re.search(r"(\d+)/([0-9a-zA-Z]{9})", url)):
        uid, weibo_id = match.group(1), match.group(2)
        return generate_url(uid, weibo_id)
    # 情况2：链接为形如"status/mid"形式，需访问页面获取uid
    if "status/" in url:
        # 情况2.1：数字mid
        if (match := re.search(r"status/(\d{16})", url)):
            mid = match.group(1)
            return generate_url(uid=get_uid_from_m_page(mid), weibo_id=convert_mid(mid))
        # 情况2.2：字母数字混合mid
        if (match := re.search(r"status/([0-9a-zA-Z]{9})", url)):
            weibo_id = match.group(1)
            return generate_url(uid=get_uid_from_m_page(weibo_id), weibo_id=weibo_id)
    raise ValueError("This url is not supported.")

def get_uid_from_m_page(mid):
    # 访问手机版 url 获取博主 uid
    url_template = "https://m.weibo.cn/status/{mid}"
    r = requests.get(url_template.format(mid=mid))
    pattern = r"m.weibo.cn/u/(.*?)\?"
    if (match := re.search(pattern, r.text)):
        uid = match.group(1)
        return uid
    raise ValueError("Invalid mid")

def int_to_base(i, alphabet=ALPHABET, padded_length=4):
    base = len(alphabet)
    if not isinstance(i, int):
        raise TypeError("Only integers are supported.")
    if i<0:
        raise ValueError("Only positive integers are supported")
    result = []
    while i>0:
        result.append(i % base)
        i //= base
    while len(result) < padded_length:
        result.append(0)
    result.reverse()
    return "".join(alphabet[i] for i in result)

def convert_mid(mid):
    # 将 mid 转换成微博 id
    mid_groups = [*map(int, (mid[:2], mid[2:9], mid[9:16]))]
    mid_groups = [int_to_base(mid_groups[0], padded_length=1), int_to_base(mid_groups[1], padded_length=4), int_to_base(mid_groups[2], padded_length=4)]
    return "".join(mid_groups)

def generate_url(uid, weibo_id):
    return f"https://weibo.com/{uid}/{weibo_id}"
