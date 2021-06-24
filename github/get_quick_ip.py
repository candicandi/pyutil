import datetime
import os
import time

import requests

DOHs = ["https://dns.alidns.com/resolve",
        "https://rubyfish.cn/dns-query",
        # cloudflare-dns.com 国内被墙, 换ip可以正常访问
        "https://1.1.1.1/dns-query",
        "https://doh.360.cn/query",
        "https://doh.pub/dns-query",
        # 国内被墙
        # "https://dns.google/resolve"
        ]

doh_header = {
    "user-source": "360se",
    "accept": "application/dns-json",
    "user-identity": "12345678901234567890123456789012345678901234",
}

sess = requests.session()


def getIpFromDoH(site, dohIndex=1):

    res = sess.get("%s?name=%s&type=1" % (DOHs[dohIndex], site), headers=doh_header, timeout=30)
    print(DOHs[dohIndex])
    for i in res.json()['Answer']:
        if i['type'] == 1:
            # print(i['data'])
            trueip = i['data']
            if check_ping(trueip):
                print("ok %s" % trueip)
            else:
                print("fail %s" % trueip)
                dohIndex = dohIndex + 1
                return getIpFromDoH(site, dohIndex % len(DOHs))

            return i['data']


def check_ping(server):
    response = os.system("ping -n 1 %s" % server)
    print("result: ", response)
    return response == 0


# 需要获取ip的网址
sites = [
    'avatars.githubusercontent.com',
    'codeload.github.com',
    'documentcloud.github.com',
    'github-cloud.s3.amazonaws.com',
    'github-com.s3.amazonaws.com',
    'github.githubassets.com',
    # 国内DNS已被污染严重,无法正常解析
    'github.global.ssl.fastly.net',
    'gist.github.com',
    'assets-cdn.github.com',
    'api.github.com',
    'githubapp.com',
    'github.io',
    'githubstatus.com',
    'live.github.com',
    'status.github.com',
    'collector.githubapp.com',
    'github.blog',
    'alive.github.com',
    'central.github.com',
    'desktop.githubusercontent.com',
]

# 相同ip映射表,减少网络请求数量
gp = {
    # githubusercontent
    "avatars.githubusercontent.com": ['avatars.githubusercontent.com',
                                      'camo.githubusercontent.com',
                                      'user-images.githubusercontent.com',
                                      'gist.githubusercontent.com',
                                      'raw.github.com',
                                      'raw.githubusercontent.com',
                                      'cloud.githubusercontent.com',
                                      'media.githubusercontent.com',
                                      'github.map.fastly.net',
                                      ],

    "github-cloud.s3.amazonaws.com": ['github-cloud.s3.amazonaws.com',
                                      'github-production-release-asset-2e65be.s3.amazonaws.com',
                                      'github-production-user-asset-6210df.s3.amazonaws.com'
                                      ],
    "gist.github.com": ['gist.github.com',
                        'github.com',
                        'www.github.com'],
    "github-com.s3.amazonaws.com": ['github-com.s3.amazonaws.com',
                                    'github-production-repository-file-5c1aeb.s3.amazonaws.com',
                                    ],
    "codeload.github.com": ['codeload.github.com',
                            'nodeload.github.com',
                            ],
    "github.githubassets.com": ['github.githubassets.com',
                                'help.github.com',
                                ],
    "documentcloud.github.com": ['documentcloud.github.com',
                                 'customer-stories-feed.github.com',
                                 ],
    "collector.githubapp.com": ['collector.githubapp.com'],
    "assets-cdn.github.com": ['assets-cdn.github.com', 'pages.github.com', 'training.github.com']

}

addr2ip = {}
hostLocation = r"hosts"


def dropDuplication(line):
    flag = False
    if "#*********************github" in line:
        return True
    for site in sites:
        if site in gp and gp[site]:
            for gsite in gp[site]:
                if gsite in line:
                    flag = flag or True
                else:
                    flag = flag or False
        else:
            flag = flag or site in line
    return flag


# 更新host, 并刷新本地DNS
def updateHost():
    print(sorted(sites, key=lambda i: i[0]))
    today = datetime.date.today()
    fail_ips = []
    ok = []

    while len(ok) != len(sites):
        a = [i for i in sites if i not in ok]
        # print(a)
        for site in a:
            trueip = getIpFromDoH(site)
            if trueip:
                if site in gp and gp[site]:
                    for gsite in gp[site]:
                        addr2ip[gsite] = trueip
                    # print(str(gp[site]) + "\t" + trueip)
                else:
                    addr2ip[site] = trueip
                    # print(site + "\t" + trueip)
                ok.append(site)
                print("进度 %d / %d" % (len(ok), len(sites)))
            else:
                fail_ips.append(site)
            # print("剩余 %d / %d" % (len(ok), len(sites)))
        time.sleep(3)

    with open(hostLocation, "r") as f1:
        f1_lines = f1.readlines()
        with open("temphost", "w") as f2:
            f2.write("#*********************github " +
                     str(today) + " update********************\n")
            for line in f1_lines:  # 为了防止 host 越写用越长，需要删除之前更新的含有github相关内容
                if not dropDuplication(line):
                    f2.write(line)

            for key in addr2ip:
                f2.write(addr2ip[key] + "\t" + key + "\n")
    os.remove(hostLocation)
    os.rename("temphost", hostLocation)


if __name__ == '__main__':
    updateHost()
    # check_ping("192.168.10.1")
    # getIpFromDoH("github.global.ssl.fastly.net", 4)
