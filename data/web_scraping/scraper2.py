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
hastalik_bolum_eslesme = [
    (1, 20),
    (2, 6),
    (3, 17),
    (4, 8),
    (5, 17),
    (6, 8),
    (7, 2),
    (8, 12),
    (9, 14),
    (10, 17),
    (11, 16),
    (12, 5),
    (13, 4),
    (14, 4),
    (15, 4),
    (16, 14),
    (17, 4),
    (18, 14),
    (19, 13),
    (20, 3),
    (21, 6),
    (22, 13),
    (23, 13),
    (24, 5),
    (25, 9),
    (26, 17),
    (27, 15),
    (28, 2),
    (29, 17),
    (30, 2),
    (31, 4),
    (32, 16),
    (33, 12),
    (34, 17),
    (35, 1),
    (36, 3),
    (37, 2),
    (38, 10),
    (39, 16),
    (40, 12),
    (41, 12),
    (42, 18),
    (43, 11),
    (44, 25),
    (45, 25),
    (46, 18),
    (47, 13),
    (48, 10),
    (49, 25),
    (50, 12),
    (51, 4),
    (52, 9),
    (53, 6),
    (54, 3),
    (55, 4),
    (56, 1),
    (57, 12),
    (58, 9),
    (59, 1),
    (60, 2),
    (61, 5),
    (62, 3),
    (63, 22),
    (64, 7),
    (65, 11),
    (66, 5),
    (67, 18),
    (68, 18),
    (69, 3),
    (70, 8),
    (71, 9),
    (72, 8),
    (73, 3),
    (74, 19),
    (75, 19),
    (76, 19),
    (77, 19),
    (78, 16),
    (79, 3),
    (80, 3),
    (81, 3),
    (82, 7),
    (83, 3),
    (84, 2),
    (85, 17),
    (86, 2),
    (87, 22),
    (88, 22),
    (89, 2),
    (90, 12),
    (91, 19),
    (92, 11),
    (93, 17),
    (94, 3),
    (95, 12),
    (96, 3),
    (97, 3),
    (98, 3),
    (99, 15),
    (100, 15),
    (101, 14),
    (102, 7),
    (103, 14),
    (104, 15),
    (105, 1),
    (106, 2),
    (107, 4),
    (108, 4),
    (109, 4),
    (110, 4),
    (111, 17),
    (112, 5),
    (113, 1),
    (114, 17),
    (115, 12),
    (116, 3),
    (117, 9),
    (118, 3),
    (119, 6),
    (120, 19),
    (121, 13),
    (122, 2),
    (123, 17),
    (124, 16),
    (125, 14),
    (126, 7),
    (127, 17),
    (128, 19),
    (129, 5),
    (130, 6),
    (131, 17),
    (132, 3),
    (133, 20),
    (134, 9),
    (135, 3),
    (136, 20),
    (137, 17),
    (138, 19),
    (139, 19),
    (140, 19),
    (141, 19),
    (142, 19),
    (143, 19),
    (144, 19),
    (145, 19),
    (146, 24),
    (147, 5),
    (148, 2),
    (149, 12),
    (150, 2),
    (151, 16),
    (152, 18),
    (153, 3),
    (154, 6),
    (155, 17),
    (156, 11),
    (157, 14),
    (158, 11),
    (159, 3),
    (160, 5),
    (161, 12),
    (162, 2),
    (163, 20),
    (164, 20),
    (165, 20),
    (166, 20),
    (167, 20),
    (168, 20),
    (169, 20),
    (170, 5),
    (171, 15),
    (172, 4),
    (173, 3),
    (174, 17),
    (175, 17),
    (176, 2),
    (177, 14),
    (178, 5),
    (179, 3),
    (180, 1),
    (181, 3),
    (182, 17),
    (183, 9),
    (184, 16),
    (185, 17),
    (186, 15),
    (187, 5),
    (188, 8),
    (189, 7),
    (190, 2),
    (191, 16),
    (192, 7),
    (193, 7),
    (194, 14),
    (195, 16),
    (196, 2),
    (197, 25),
    (198, 15),
    (199, 3),
    (200, 6),
    (201, 9),
    (202, 18),
    (203, 16),
    (204, 1),
    (205, 19),
    (206, 3),
    (207, 17),
    (208, 5),
    (209, 5),
    (210, 19),
    (211, 16),
    (212, 5),
    (213, 19),
    (214, 19),
    (215, 17),
    (216, 17),
    (217, 22),
    (218, 14),
    (219, 17),
    (220, 5),
    (221, 6),
    (222, 22),
    (223, 10),
    (224, 18),
    (225, 18),
    (226, 21),
    (227, 10),
    (228, 14),
    (229, 10),
    (230, 6),
    (231, 17),
    (232, 6),
    (233, 2),
    (234, 16),
    (235, 9),
    (236, 21),
    (237, 12),
    (238, 11),
    (239, 9),
    (240, 6),
    (241, 5),
    (242, 9),
    (243, 18),
    (244, 2),
    (245, 13),
    (246, 5),
    (247, 13),
    (248, 18),
    (249, 17),
    (250, 17),
    (251, 17),
    (252, 17),
    (253, 16),
    (254, 13),
    (255, 7),
    (256, 9),
    (257, 6),
    (258, 6),
    (259, 25),
    (260, 3),
    (261, 10),
    (262, 19),
    (263, 2),
    (264, 2),
    (265, 2),
    (266, 2),
    (267, 7),
    (268, 17),
    (269, 16),
    (270, 5),
    (271, 5),
    (272, 12),
    (273, 17),
    (274, 15),
    (275, 6),
    (276, 22),
    (277, 14),
    (278, 14),
    (279, 13),
    (280, 1),
    (281, 1),
    (282, 1),
    (283, 1),
    (284, 1),
    (285, 25),
    (286, 13),
    (287, 18),
    (288, 3),
    (289, 3),
    (290, 25),
    (291, 18),
    (292, 5),
    (293, 14),
    (294, 5),
    (295, 5),
    (296, 5),
    (297, 18),
    (298, 1),
    (299, 5),
    (300, 14),
    (301, 11),
    (302, 3),
    (303, 7),
    (304, 8),
    (305, 18),
    (306, 8),
    (307, 9),
    (308, 8),
    (309, 10),
    (310, 10),
    (311, 10),
    (312, 9),
    (313, 5),
    (314, 1),
    (315, 9),
    (316, 9),
    (317, 8),
    (318, 10),
    (319, 5),
    (320, 17),
    (321, 17),
    (322, 2),
    (323, 11),
    (324, 5),
    (325, 16),
    (326, 9),
    (327, 11),
    (328, 11),
    (329, 12),
    (330, 20),
    (331, 17),
    (332, 5),
    (333, 17),
    (334, 17),
    (335, 3),
    (336, 3),
    (337, 3),
    (338, 11),
    (339, 9),
    (340, 14),
    (341, 3),
    (342, 3),
    (343, 5),
    (344, 14),
    (345, 4),
    (346, 5),
    (347, 14),
    (348, 14),
    (349, 14),
    (350, 1),
    (351, 1),
    (352, 13),
    (353, 14),
    (354, 5),
    (355, 5),
    (356, 18),
    (357, 7),
    (358, 9),
    (359, 14),
    (360, 14),
    (361, 9),
    (362, 17),
    (363, 2),
    (364, 1),
    (365, 2),
    (366, 17),
    (367, 17),
    (368, 12),
    (369, 14),
    (370, 2),
    (371, 2),
    (372, 5),
    (373, 14),
    (374, 12),
    (375, 12),
    (376, 3),
    (377, 12),
    (378, 12),
    (379, 19),
    (380, 9),
    (381, 19),
    (382, 14),
    (383, 3),
    (384, 3),
    (385, 3),
    (386, 3),
    (387, 19),
    (388, 3),
    (389, 13),
    (390, 3),
    (391, 3),
    (392, 17),
    (393, 9),
    (394, 9),
    (395, 9),
    (396, 9),
    (397, 17),
    (398, 17),
    (399, 17),
    (400, 17),
    (401, 17),
    (402, 2),
    (403, 12),
    (404, 17),
    (405, 17),
    (406, 4),
    (407, 17),
    (408, 18),
    (409, 16),
    (410, 16),
    (411, 16),
    (412, 13),
    (413, 11),
    (414, 7),
    (415, 6),
    (416, 4),
    (417, 13),
    (418, 3),
    (419, 12),
    (420, 2),
    (421, 19),
    (422, 3),
    (423, 3),
    (424, 3),
    (425, 8),
    (426, 8),
    (427, 1),
    (428, 1),
    (429, 1),
    (430, 1),
    (431, 1),
    (432, 13),
    (433, 14),
    (434, 13),
    (435, 5),
    (436, 1),
    (437, 14),
    (438, 5),
    (439, 5),
    (440, 1),
    (441, 14),
    (442, 1),
    (443, 16),
    (444, 5),
    (445, 14),
    (446, 3),
    (447, 3),
    (448, 3),
    (449, 9),
    (450, 17),
    (451, 17),
    (452, 9),
    (453, 17),
    (454, 2),
    (455, 2),
    (456, 8),
    (457, 14),
    (458, 5),
    (459, 11),
    (460, 8),
    (461, 17),
    (462, 2),
    (463, 12),
    (464, 12),
    (465, 2),
    (466, 5),
    (467, 2),
    (468, 14),
    (469, 18),
    (470, 3),
    (471, 1),
    (472, 1),
    (473, 12),
    (474, 6),
    (475, 5),
    (476, 17),
    (477, 2),
    (478, 2),
    (479, 2),
    (480, 2),
    (481, 13),
    (482, 14),
    (483, 2),
    (484, 3),
    (485, 3),
    (486, 3),
    (487, 3),
    (488, 18),
    (489, 3),
    (490, 3),
    (491, 17),
    (492, 13),
    (493, 14),
    (494, 3),
    (495, 17),
    (496, 9),
    (497, 17),
    (498, 12),
    (499, 17),
    (500, 8),
    (501, 12),
    (502, 8),
    (503, 8),
    (504, 6),
    (505, 12),
    (506, 2),
    (507, 6),
    (508, 10),
    (509, 10),
    (510, 1),
    (511, 1),
    (512, 10),
    (513, 1),
    (514, 17),
    (515, 3),
    (516, 3),
    (517, 3),
    (518, 13),
    (519, 14),
    (520, 14),
    (521, 3),
    (522, 7),
    (523, 7),
    (524, 7),
    (525, 10),
    (526, 16),
    (527, 18),
    (528, 3),
    (529, 2),
    (530, 2),
    (531, 2),
    (532, 2),
    (533, 2),
    (534, 2),
    (535, 2),
    (536, 11),
    (537, 17),
    (538, 5),
    (539, 5),
    (540, 5),
    (541, 14),
    (542, 8),
    (543, 8),
    (544, 8),
    (545, 8),
    (546, 2),
    (547, 19),
    (548, 10),
    (549, 3),
    (550, 10),
    (551, 10),
    (552, 19),
    (553, 19),
    (554, 14),
    (555, 3),
    (556, 10),
    (557, 3),
    (558, 3),
    (559, 3),
    (560, 9),
    (561, 1),
    (562, 16),
    (563, 3),
    (564, 3),
    (565, 3),
    (566, 1),
    (567, 9),
    (568, 9),
    (569, 9),
    (570, 9),
    (571, 17),
    (572, 17),
    (573, 17),
    (574, 3),
    (575, 11),
    (576, 11),
    (577, 11),
    (578, 11),
    (579, 19),
    (580, 21),
    (581, 9),
    (582, 11),
    (583, 16),
    (584, 17),
    (585, 4),
    (586, 16),
    (587, 4),
    (588, 4),
    (589, 8),
    (590, 18),
    (591, 14),
    (592, 14),
    (593, 8),
    (594, 8),
    (595, 14),
    (596, 18),
    (597, 14),
    (598, 15),
    (599, 10),
    (600, 10),
    (601, 10),
    (602, 19),
    (603, 19),
    (604, 2),
    (605, 3),
    (606, 7),
    (607, 14),
    (608, 7),
    (609, 3),
    (610, 7),
    (611, 7),
    (612, 7),
    (613, 3),
    (614, 3),
    (615, 20),
    (616, 17),
    (617, 21),
    (618, 5),
    (619, 2),
    (620, 12),
    (621, 14),
    (622, 19),
    (623, 1),
    (624, 2),
    (625, 4),
    (626, 17),
]

# Bölüm isimleri
bolumler = {
    1: "Kardiyoloji (Kalp-Damar)",
    2: "Nöroloji (Beyin-Sinir)",
    3: "Ortopedi (Kemik-Eklem)",
    4: "Göğüs Hastalıkları",
    5: "Gastroenteroloji (Sindirim)",
    6: "Endokrinoloji (Hormon)",
    7: "Üroloji (İdrar Yolları)",
    8: "Kadın Hastalıkları ve Doğum",
    9: "Dermatoloji (Cilt)",
    10: "Göz Hastalıkları (Oftalmoloji)",
    11: "Kulak Burun Boğaz (KBB)",
    12: "Psikiyatri (Ruh Sağlığı)",
    13: "Hematoloji (Kan Hastalıkları)",
    14: "Onkoloji (Kanser)",
    15: "Nefroloji (Böbrek)",
    16: "Romatoloji (Eklem-Otoimmün)",
    17: "Enfeksiyon Hastalıkları",
    18: "Genel Cerrahi",
    19: "Çocuk Sağlığı (Pediatri)",
    20: "Diş Hekimliği",
    21: "Göğüs Cerrahisi",
    22: "Beyin Cerrahisi",
    23: "Plastik Cerrahi",
    24: "Anestezi ve Reanimasyon",
    25: "Kalp Damar Cerrahisi",
}


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
def get_bolum_by_hastalik_no(hastalik_no):
    for hastalik, bolum in hastalik_bolum_eslesme:
        if hastalik == hastalik_no:
            return bolumler.get(bolum, "Bilinmeyen Bölüm")
    return "Hastalık bulunamadı"


def get_full_desc(main_div, search_text):

    h2_tag = main_div.find("h2", string=re.compile(search_text, re.IGNORECASE))

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
                if sib.name == "ul":
                    li_texts = [li.get_text(strip=True) for li in sib.find_all("li")]
                    paragraphs.append(", ".join(li_texts))
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
            "bolum": "",
            "link": full_link,
        }
        full_data_list.append(dict_item)

    for i in range(len(full_link_list)):

        # hastalığın sayfasına git ve oradaki temel alınacak tag i al
        full_div = follow_and_find(full_link_list[i], "div", "article")

        # Nedir kısmını topla
        nedir_desc = " ".join(get_full_desc(full_div, "nedir?"))

        # Belirtiler kısmını topla
        belirtiler_desc = " ".join(get_full_desc(full_div, "belirtileri nelerdir?"))
        belirtiler_desc = belirtiler_desc + " ".join(
            get_full_desc(full_div, "bulguları nelerdir?")
        )
        belirtiler_desc = belirtiler_desc + " ".join(
            get_full_desc(full_div, "neden Olur?")
        )

        # Türleri kısmını topla
        turleri_desc = " ".join(get_full_desc(full_div, "Türleri Nelerdir?"))

        # Teşhisi kısmını topla
        teshisi_desc = " ".join(get_full_desc(full_div, "nasıl teşhis edilir?"))
        teshisi_desc = teshisi_desc + " ".join(
            get_full_desc(full_div, "teşhisi nasıldır?")
        )
        teshisi_desc = teshisi_desc + " ".join(
            get_full_desc(full_div, "tanısı nasıl konulur?")
        )

        # Teşhisi kısmını topla
        tedavi_desc = " ".join(get_full_desc(full_div, "tedavisi Nasıl Yapılır?"))
        tedavi_desc = tedavi_desc + " ".join(
            get_full_desc(full_div, "Nasıl Tedavi Edilir?")
        )

        full_data_list[i]["nedir"] = nedir_desc
        full_data_list[i]["belirtiler"] = belirtiler_desc
        full_data_list[i]["türleri"] = turleri_desc
        full_data_list[i]["teshis"] = teshisi_desc
        full_data_list[i]["tedavi"] = tedavi_desc
        full_data_list[i]["bolum"] = get_bolum_by_hastalik_no(i + 1)

        print(nedir_desc, "\n")

    save_table(full_data_list, "output/hastaliklar_detayli_listesi.csv")
