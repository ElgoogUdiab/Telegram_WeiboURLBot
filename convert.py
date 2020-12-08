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
    if "weibointl.api.weibo.com" in url:
        # 国际版链接
        return convert_intl(url)
    elif "weibo.com" in url:
        # 电脑版链接，直接返回
        return url
    if "m.weibo.cn" in url:
        # 手机版链接
        return convert_m(url)

def convert_intl(url):
    # 国际版链接提取 mid
    if (match := re.search(r"weibo_id=(\d+)", url)):
        # url 中已给出 mid，直接利用 mid 转换
        mid = match.group(1)
        return generate_url(mid)
    else:
        # 实验性特性：在 url 中未给出 mid，加载页面并利用以下 pattern 获取 mid
        # TODO: 反爬（？）
        pattern = r"<a href=\"javascript:void\(0\)\" onclick=\"forward\(0,\d+\)\">"
        r = requests.get(url)
        if (match := re.search(pattern, r.text)):
            mid = match.group(1)
            return generate_url(mid)
        raise ValueError("This url is not supported.")

def convert_m(url):
    # 手机版链接，直接提取 url 最后的数字即可
    if (match := re.search(r"(\d+)\??$", url)):
        mid = match.group(1)
        return generate_url(mid)

def get_uid_from_mid(mid):
    # 访问手机版 url 获取博主 uid
    url_template = "https://m.weibo.cn/status/{mid}"
    r = requests.get(url_template.format(mid=mid))
    pattern = r"m.weibo.cn/u/(.*?)\?"
    if (match := re.search(pattern, r.text)):
        uid = match.group(1)
        return uid
    raise ValueError("Invalid mid")

def int_to_base(i, alphabet=ALPHABET):
    base = len(alphabet)
    if not isinstance(i, int):
        raise TypeError("Only integers are supported.")
    if i<0:
        raise ValueError("Only positive integers are supported")
    result = []
    while i>0:
        result.append(i % base)
        i //= base
    result.reverse()
    return "".join(alphabet[i] for i in result)

def convert_mid(mid):
    # 将 mid 转换成微博 id
    mid_groups = map(int_to_base, map(int, (mid[:2], mid[2:9], mid[9:16])))
    return "".join(mid_groups)

def generate_url(mid):
    return f"https://weibo.com/{get_uid_from_mid(mid)}/{convert_mid(mid)}"

if __name__ == "__main__":
    url = "http://weibointl.api.weibo.com/share/188665113.html?weibo_id=4579794677141574"
    print(url)
    print(convert(url))
