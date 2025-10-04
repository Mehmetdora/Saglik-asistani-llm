import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import re, time, os
import pandas as pd
from tqdm import tqdm
import cloudscraper


soup = None


""" 

Hastalık isimleri ve bu isimlerin açıklamasından çıkarılan başlıklar ;
- nedir?
- belirtileri nelerdir?
- türleri nelerdir ?
- nasıl teşhis edilir?
- nasıl tedavi edilir? 

"""


def load_base_html(url):
    global soup
    scraper = cloudscraper.create_scraper()  # Cloudflare bypass
    html = scraper.get(url)
    soup = BeautifulSoup(html.text, "lxml")


def get_tag_with_classname(tagName, className):
    global soup
    return soup.find_all(tagName, {"class": className})


def get_tag_with_id(tagName, id):
    global soup
    return soup.find(tagName, id=id)


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
    scraper = cloudscraper.create_scraper()  # Cloudflare bypass
    html = scraper.get(link)
    new_soup = BeautifulSoup(html.text, "lxml")

    return new_soup.find(target_tag, {"class": target_class})


##-------------- ** -------------


def get_full_desc(main_div, search_text):

    h2_tag = main_div.find("h2", string=re.compile(search_text))

    if h2_tag == None:
        return ""
    else:
        paragraphs = []
        for sib in h2_tag.next_siblings:
            if isinstance(sib, Tag):
                if sib.name == "h2":
                    break  # sonraki h2 geldi -> çık
                if sib.name == "p":
                    paragraphs.append(sib.get_text(strip=True))
        return paragraphs


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

    start_url = "https://www.memorial.com.tr/hastaliklar"

    load_base_html(start_url)
    main_div = get_tag_with_id("div", id="illnessList")
    hastaliklar_div_tags = main_div.find_all("div", recursive=False)

    full_link_list = []
    full_data_list = []

    for tag in hastaliklar_div_tags:
        a_tag = tag.find("a", recursive=False)
        hastalik = a_tag.get("title")
        full_link = ""
        href = a_tag.get("href")

        if href.startswith("/"):
            # relatif linkleri absolute yap
            full_link = urljoin(start_url, href)
            full_link_list.append(full_link)
            print("Gidilecek tam link:", full_link)

        dict_item = {
            "hastalık": hastalik,
            "nedir": "",
            "belirtiler": "",
            "türleri": "",
            "teshis": "",
            "tedavi": "",
            "link": full_link,
        }
        full_data_list.append(dict_item)

    for i in range(len(full_link_list)):

        # hastalığın sayfasına git ve oradaki temel alınacak tag i al
        full_div = follow_and_find(full_link_list[i], "div", "article")

        # Nedir kısmını topla
        nedir_desc = " ".join(get_full_desc(full_div, "Nedir?"))

        # Belirtiler kısmını topla
        belirtiler_desc = " ".join(get_full_desc(full_div, "Belirtileri Nelerdir?"))
        belirtiler_desc = belirtiler_desc + " ".join(
            get_full_desc(full_div, "Neden Olur?")
        )

        # Türleri kısmını topla
        turleri_desc = " ".join(get_full_desc(full_div, "Türleri Nelerdir?"))

        # Teşhisi kısmını topla
        teshisi_desc = " ".join(get_full_desc(full_div, "Nasıl Teşhis Edilir?"))

        # Teşhisi kısmını topla
        tedavi_desc = " ".join(get_full_desc(full_div, "Tedavisi Nasıl Yapılır?"))
        tedavi_desc = tedavi_desc + " ".join(
            get_full_desc(full_div, "Nasıl Tedavi Edilir?")
        )

        full_data_list[i]["nedir"] = nedir_desc
        full_data_list[i]["belirtiler"] = belirtiler_desc
        full_data_list[i]["türleri"] = turleri_desc
        full_data_list[i]["teshis"] = teshisi_desc
        full_data_list[i]["tedavi"] = tedavi_desc

        print(nedir_desc, "\n")
        print(belirtiler_desc, "\n")

    save_table(full_data_list, "output/hastaliklar_detayli_listesi.csv")
