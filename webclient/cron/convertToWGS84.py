import json
import logging

import requests

logger = logging.getLogger("django_cron")


def get_transform_to_wgs84(cy, cx):
    url = "https://geoportal.cuzk.cz/(S(k10mxdjzq1pv5tkgcghghohf))/WCTSHandlerhld.ashx"
    query = (
        "source=Coordinates&"
        "sourceSRS=urn%3Aogc%3Adef%3Acrs%2Ccrs%3AEPSG%3A%3A2065%2Ccrs%3AEPSG%3A%3A5705&"
        "targetSRS=urn%3Aogc%3Adef%3Acrs%3AEPSG%3A%3A4979&"
        "sourceXYorder=yx&"
        "targetXYorder=xy&"
        "sourceSixtiethView=false&"
        "targetSixtiethView=false&"
        "coordinates=" + str(cy) + "+" + str(cx) + "+300"
        "&time=2022-05-20"
    )

    headers = {
        "Host": "geoportal.cuzk.cz",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "content-type": "application/x-www-form-urlencoded",
        "x-requested-with": "XMLHttpRequest",
        "Origin": "https://geoportal.cuzk.cz",
        "Connection": "keep-alive",
        "Referer": "https://geoportal.cuzk.cz/(S(k10mxdjzq1pv5tkgcghghohf))/Default.aspx?head_tab=sekce-01-gp&mode=TextMeta&text=wcts&menu=19",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
    }
    try:
        # logger.debug(url)
        # logger.debug(query)
        r = requests.post(url, data=query, headers=headers)
        # logger.debug(r.status_code)
        # logger.debug(r.text)
        body = json.loads(r.text)["Coordinates"].split(" ")
        return [body[0], body[1]]
    except IndexError:
        logger.error("Error during transformation")
        return None


def get_multi_transform_to_wgs84(jtsk_points):
    # logger.debug("get_multi_transform_towgs84")

    url = "https://geoportal.cuzk.cz/(S(k10mxdjzq1pv5tkgcghghohf))/WCTSHandlerhld.ashx"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
        "Content-Type": "multipart/form-data; boundary=amcr-multipart-block",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    query = (
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="source"\r\n\r\nFile\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="sourceSRS"\r\n\r\nurn:ogc:def:crs,crs:EPSG::2065,crs:EPSG::5705\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="targetSRS"\r\n\r\nurn:ogc:def:crs:EPSG::4979\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="sourceXYorder"\r\n\r\nyx\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="targetXYorder"\r\n\r\nxy\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="sourceSixtiethView"\r\n\r\nfalse\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="targetSixtiethView"\r\n\r\false\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="time"\r\n\r\n2022-05-20\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="wcts_fileType"\r\n\r\ntext\r\n'
        "--amcr-multipart-block\r\n"
        'Content-Disposition: form-data; name="wcts_file1"; filename="test.souradnice2.txt"\r\n'
        "Content-Type: text/plain\r\n\r\n"
    )
    incr = 0
    for p in jtsk_points:
        incr += 1
        query = (
            query
            + "PP"
            + str(incr)
            + "     "
            + str(p[0])
            + "    "
            + str(p[1])
            + "    300\r\n"
        )  # "TB02     646860.290    1060814.217    669.262   nepovinný popis\r\n" \
    query = query + "--amcr-multipart-block--\r\n"

    try:
        # logger.debug(url)
        # logger.debug(query)
        r = requests.post(url, data=query, headers=headers)
        # logger.debug(r.status_code)
        # logger.debug(r.text)
        points = []
        for line in r.text.split("\n"):
            if len(line) > 5:
                p = line.split("\t")[1].split(" ")
                # logger.debug(p)
                points.append([p[0], p[1]])

        return points
    except IndexError:
        logger.error("Error during transformation")
        return None
