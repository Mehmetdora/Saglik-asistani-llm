import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re, time, os
import pandas as pd
from tqdm import tqdm


soup = None





def load_html(url):
    global soup
    html = requests.get(url).text
    soup = BeautifulSoup(html, "lxml")


def get_tag_with_classname(tagName, className):
    global soup
    return soup.find_all(tagName, {"class": className})


def get_second_p_in_div(div):
    second_p = div.select_one("p:nth-of-type(2)")
    return second_p.get_text(strip=True)


def find_tag_includes_text(div, tag, text):
    if div != None:
        tag = div.find(tag, string=re.compile(text))
        if tag:
            return tag
    else:
        return 0


def get_next_tag(tag, next_tag_name):
    if tag != 0 and tag != None:
        if tag.find_next(next_tag_name) != None:
            return tag.find_next(next_tag_name).get_text(strip=True)
    else:
        return ""


def follow_and_find(link, target_tag, target_class):

    # yeni sayfaya git
    new_html = requests.get(link).text
    new_soup = BeautifulSoup(new_html, "lxml")

    return new_soup.find(target_tag, {"class": target_class})


def save_table(data, path, fmt="csv"):
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if fmt == "csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")
    elif fmt in ("xlsx", "excel"):
        df.to_excel(path, index=False, engine="openpyxl")
    else:
        raise ValueError("Desteklenmeyen format: " + fmt)
    print(f"[OK] {path} kaydedildi.")


if __name__ == "__main__":
    start_url_liv = "https://www.livhospital.com/liv-tibbi-branslari"
    start_url = "https://www.livhospital.com/hastaliklar-ve-tedavileri"

    load_html(start_url)
    a_tags = get_tag_with_classname("a", "clinical-service-redirect")

    full_link_list = []
    full_data_list = []
    branch_desc = {}
    for tag in a_tags:
        link = tag.get("href")
        branch_desc = {
            "hastalık": tag.get_text(strip=True),
            "nedir": "",
            "belirtiler": "",
        }

        full_data_list.append(branch_desc)

        if link.startswith("/"):
            # relatif linkleri absolute yap
            full_link = urljoin(start_url, link)

            print("Gidilecek tam link:", full_link)
            full_link_list.append(full_link)

    for i in range(len(full_link_list)):
        full_div = follow_and_find(full_link_list[i], "div", "branch-detail-content")

        if full_div == None:
            full_div = follow_and_find(
                full_link_list[i], "div", "health-corner-detail-column-right"
            )

        nedir_tag_h2 = find_tag_includes_text(full_div, "h2", "Nedir")
        nedir_desc = get_next_tag(nedir_tag_h2, "p")

        full_data_list[i]["nedir"] = nedir_desc

        belirtiler_tag_h2 = find_tag_includes_text(
            full_div, "h2", "Belirtileri Nelerdir?"
        )
        belirtiler_desc = get_next_tag(belirtiler_tag_h2, "p")
        if (
            belirtiler_tag_h2 != 0
            and belirtiler_tag_h2 != None
            and belirtiler_tag_h2.find_next("ul") != None
        ):
            belirtiler_desc = (
                belirtiler_desc
                + " "
                + belirtiler_tag_h2.find_next("ul").get_text(strip=True)
            )

        full_data_list[i]["belirtiler"] = belirtiler_desc

        print(nedir_desc, "\n")
        print(belirtiler_desc, "\n")



    save_table(full_data_list, "output/hastalik_nedir_belirtiler_listesi.csv")

