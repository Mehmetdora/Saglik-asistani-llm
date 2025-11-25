import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import re, time, os
import pandas as pd
from tqdm import tqdm
import cloudscraper


soup = None

# Bölüm isimleri
bolumler = {
    0: "Acil Tıp",
    1: "Alerji ve İmmünoloji",
    2: "Beyin ve Sinir Cerrahisi (Nöroşirürji)",
    3: "Çocuk Cerrahisi",
    4: "Çocuk Endokrinolojisi",
    5: "Çocuk Gastroenterolojisi",
    6: "Çocuk Göğüs Hastalıkları",
    7: "Çocuk Hematolojisi",
    8: "Çocuk İmmünolojisi",
    9: "Çocuk Kardiyolojisi",
    10: "Çocuk Nefrolojisi",
    11: "Çocuk Nörolojisi",
    12: "Çocuk Onkolojisi",
    13: "Çocuk Psikiyatrisi",
    14: "Çocuk Romatolojisi",
    15: "Çocuk Sağlığı ve Hastalıkları",
    16: "Çocuk Ürolojisi",
    17: "Dermatoloji (Cildiye)",
    18: "Enfeksiyon Hastalıkları",
    19: "Endokrinoloji (Hormon Hastalıkları)",
    20: "Fiziksel Tıp ve Rehabilitasyon",
    21: "Gastroenteroloji (Sindirim Sistemi)",
    22: "Genel Cerrahi",
    23: "Göğüs Cerrahisi",
    24: "Göğüs Hastalıkları",
    25: "Göz Hastalıkları",
    26: "Hematoloji (Kan Hastalıkları)",
    27: "İç Hastalıkları (Dahiliye)",
    28: "Jinekoloji ve Obstetrik (Kadın Doğum)",
    29: "Kadın Hastalıkları ve Doğum",
    30: "Kalp ve Damar Cerrahisi",
    31: "Kardiyoloji (Kalp Hastalıkları)",
    32: "Kulak Burun Boğaz (KBB)",
    33: "Nefroloji (Böbrek Hastalıkları)",
    34: "Nöroloji (Beyin ve Sinir Hastalıkları)",
    35: "Onkoloji (Kanser Hastalıkları)",
    36: "Ortopedi ve Travmatoloji",
    37: "Plastik, Rekonstrüktif ve Estetik Cerrahi",
    38: "Psikiyatri (Ruh Sağlığı)",
    39: "Radyoloji",
    40: "Romatoloji (Eklem ve Otoimmün Hastalıklar)",
    41: "Üroloji",
    42: "Diş Hekimliği",
}

hastalik_bolum_eslesmeleri = [
    (0, 42),  # 20'lik Diş -> Diş Hekimliği
    (1, 19),  # Addison Hastalığı -> Endokrinoloji
    (2, 18),  # Adenit -> Enfeksiyon Hastalıkları
    (3, 29),  # Adenomyozis -> Kadın Hastalıkları ve Doğum
    (4, 18),  # Adenovirüs Enfeksiyonu -> Enfeksiyon Hastalıkları
    (5, 29),  # Adet öncesi gerginlik sendromu (PMS) -> Kadın Hastalıkları ve Doğum
    (6, 34),  # Afazi -> Nöroloji
    (7, 38),  # Agorafobi -> Psikiyatri
    (8, 35),  # Ağız Kanseri -> Onkoloji
    (9, 18),  # AIDS-HIV -> Enfeksiyon Hastalıkları
    (10, 40),  # Ailesel Akdeniz Ateşi (Fmf) -> Romatoloji
    (11, 21),  # Akalazya (yutma güçlüğü) -> Gastroenteroloji
    (12, 24),  # Akciğer embolisi -> Göğüs Hastalıkları
    (13, 24),  # Akciğer Enfeksiyonu -> Göğüs Hastalıkları
    (14, 24),  # Akciğer Kanaması -> Göğüs Hastalıkları
    (15, 35),  # Akciğer Kanseri -> Onkoloji
    (16, 24),  # Akciğer sönmesi -> Göğüs Hastalıkları
    (17, 35),  # Akciğer Zarı Kanseri (Mezotelyoma) -> Onkoloji
    (18, 26),  # Akdeniz Anemisi (Talesemi) -> Hematoloji
    (19, 36),  # Akondroplazi -> Ortopedi
    (20, 19),  # Akromegali Hastalığı -> Endokrinoloji
    (21, 26),  # Akut Lenfoblastik Lösemi (ALL) -> Hematoloji
    (22, 26),  # Akut miyeloid lösemi (AML) -> Hematoloji
    (23, 21),  # Akut Pankreatit -> Gastroenteroloji
    (24, 17),  # Albino (Albinizm) -> Dermatoloji
    (25, 1),  # Alerji -> Alerji ve İmmünoloji
    (26, 33),  # Alport Sendromu -> Nefroloji
    (27, 34),  # ALS Hastalığı -> Nöroloji
    (28, 15),  # Altıncı Hastalık -> Çocuk Sağlığı ve Hastalıkları
    (29, 34),  # Alzheimer Hastalığı -> Nöroloji
    (30, 24),  # Amfizem -> Göğüs Hastalıkları
    (31, 27),  # Amiloidoz -> İç Hastalıkları
    (32, 38),  # Amok Hastalığı -> Psikiyatri
    (33, 1),  # Anafilaksi -> Alerji ve İmmünoloji
    (34, 30),  # Anevrizma -> Kalp ve Damar Cerrahisi
    (35, 36),  # Anevrizmal Kemik Kisti -> Ortopedi
    (36, 34),  # Angelman Sendromu -> Nöroloji
    (37, 25),  # Anizokori -> Göz Hastalıkları
    (38, 40),  # Ankilozan Spondilit -> Romatoloji
    (39, 38),  # Anksiyete -> Psikiyatri
    (40, 38),  # Anoreksiya Nervoza -> Psikiyatri
    (41, 22),  # Anorektal bölge selim hastalıkları -> Genel Cerrahi
    (42, 32),  # Anosmi (Koku Alamamak) -> KBB
    (43, 30),  # Aort Anevrizması -> Kalp ve Damar Cerrahisi
    (44, 31),  # Aort Kapak Darlığı -> Kardiyoloji
    (45, 22),  # Apandisit -> Genel Cerrahi
    (46, 26),  # Aplastik Anemi -> Hematoloji
    (47, 25),  # Arpacık -> Göz Hastalıkları
    (48, 9),  # ASD (Atriyal Septal Defekt) -> Çocuk Kardiyolojisi
    (49, 13),  # Asperger Sendromu -> Çocuk Psikiyatrisi
    (50, 24),  # Astım -> Göğüs Hastalıkları
    (51, 17),  # Aşırı Terleme -> Dermatoloji
    (52, 19),  # Aşırı Tüylenme (Hirsutizm) -> Endokrinoloji
    (53, 36),  # Aşil tendiniti -> Ortopedi
    (54, 24),  # Atelektazi -> Göğüs Hastalıkları
    (55, 31),  # Ateroskleroz -> Kardiyoloji
    (56, 38),  # Atipik Psikoz -> Psikiyatri
    (57, 17),  # Atopik Dermatit -> Dermatoloji
    (58, 31),  # Atriyal Fibrilasyon -> Kardiyoloji
    (59, 27),  # Atrofi -> İç Hastalıkları
    (60, 21),  # Auto Brewery Sendromu -> Gastroenteroloji
    (61, 36),  # Avasküler Nekroz (Osteonekroz) -> Ortopedi
    (62, 2),  # AVM Hastalığı -> Beyin ve Sinir Cerrahisi
    (63, 41),  # Azospermi -> Üroloji
    (64, 32),  # Bademcik Taşı (Tonsillolit) -> KBB
    (65, 18),  # Bağırsak Enfeksiyonu -> Enfeksiyon Hastalıkları
    (66, 22),  # Bağırsak Sarkması -> Genel Cerrahi
    (67, 22),  # Bağırsak Tıkanıklığı -> Genel Cerrahi
    (68, 36),  # Baker Kisti -> Ortopedi
    (69, 29),  # Bakteriyel Vajinozis -> Kadın Hastalıkları ve Doğum
    (70, 17),  # Balık Pulu Hastalığı -> Dermatoloji
    (71, 29),  # Bartholin Kisti -> Kadın Hastalıkları ve Doğum
    (72, 36),  # Başparmak çıkıntısı (Halluks valgus) -> Ortopedi
    (73, 32),  # Bebeklerde Burun Tıkanıklığı -> KBB
    (74, 15),  # Bebeklerde Konak -> Çocuk Sağlığı ve Hastalıkları
    (75, 15),  # Bebeklerde Pamukçuk -> Çocuk Sağlığı ve Hastalıkları
    (76, 4),  # Beckwith Wiedemann Sendromu -> Çocuk Endokrinolojisi
    (77, 40),  # Behçet Hastalığı -> Romatoloji
    (78, 20),  # Bel düzleşmesi -> Fiziksel Tıp ve Rehabilitasyon
    (79, 2),  # Bel Fıtığı -> Beyin ve Sinir Cerrahisi
    (80, 2),  # Bel Kayması -> Beyin ve Sinir Cerrahisi
    (81, 18),  # Bel Soğukluğu -> Enfeksiyon Hastalıkları
    (82, 2),  # Belde kanal daralması -> Beyin ve Sinir Cerrahisi
    (83, 27),  # Beriberi Hastalığı -> İç Hastalıkları
    (84, 18),  # BETA Enfeksiyonu -> Enfeksiyon Hastalıkları
    (85, 34),  # Beyin İltihabı -> Nöroloji
    (86, 2),  # Beyin Kanaması -> Beyin ve Sinir Cerrahisi
    (87, 2),  # Beyin Tümörü -> Beyin ve Sinir Cerrahisi
    (88, 34),  # Beyinde Damar Tıkanıklığı -> Nöroloji
    (89, 38),  # Bipolar Affektif Bozukluk -> Psikiyatri
    (90, 4),  # Biyotinidaz eksikliği -> Çocuk Endokrinolojisi
    (91, 21),  # Boğaz Reflüsü -> Gastroenteroloji
    (92, 18),  # Boğmaca -> Enfeksiyon Hastalıkları
    (93, 36),  # Boksör Kırığı -> Ortopedi
    (94, 38),  # Borderline Kişilik Bozukluğu -> Psikiyatri
    (95, 20),  # Boyun Ağrısı -> Fiziksel Tıp ve Rehabilitasyon
    (96, 20),  # Boyun Düzleşmesi -> Fiziksel Tıp ve Rehabilitasyon
    (97, 2),  # Boyun Fıtığı -> Beyin ve Sinir Cerrahisi
    (98, 33),  # Böbrek Büyümesi -> Nefroloji
    (99, 33),  # Böbrek İltihabı -> Nefroloji
    (100, 35),  # Böbrek Kanseri -> Onkoloji
    (101, 41),  # Böbrek Taşları -> Üroloji
    (102, 19),  # Böbrek üstü bezi kanseri -> Endokrinoloji
    (103, 33),  # Böbrek Yetmezliği -> Nefroloji
    (104, 31),  # Bradikardi (yavaş kalp hızı) -> Kardiyoloji
    (105, 34),  # Broca Afazisi -> Nöroloji
    (106, 6),  # Bronkopulmoner Displazi -> Çocuk Göğüs Hastalıkları
    (107, 24),  # Bronşektazi -> Göğüs Hastalıkları
    (108, 6),  # Bronşiolit -> Çocuk Göğüs Hastalıkları
    (109, 24),  # Bronşit -> Göğüs Hastalıkları
    (110, 18),  # Brusella -> Enfeksiyon Hastalıkları
    (111, 30),  # Budd-Chiari Sendromu -> Kalp ve Damar Cerrahisi
    (112, 30),  # Buerger Hastalığı -> Kalp ve Damar Cerrahisi
    (113, 18),  # Bulaşıcı Hastalıklar -> Enfeksiyon Hastalıkları
    (114, 38),  # Bulimia Nervoza -> Psikiyatri
    (115, 36),  # Bursit -> Ortopedi
    (116, 17),  # Büllöz Pemfigoid -> Dermatoloji
    (117, 36),  # Cam Kemik Hastalığı -> Ortopedi
    (118, 19),  # Carney Kompleksi -> Endokrinoloji
    (119, 3),  # Carpenter Sendromu -> Çocuk Cerrahisi
    (120, 35),  # Castleman Hastalığı -> Onkoloji
    (121, 34),  # Charcot Marie Tooth Hastalığı -> Nöroloji
    (122, 18),  # Chikungunya Virüsü -> Enfeksiyon Hastalıkları
    (123, 40),  # Churg-Strauss Sendromu -> Romatoloji
    (124, 35),  # Cilt Kanseri -> Onkoloji
    (125, 29),  # Cinsel İşlev Bozuklukları -> Kadın Hastalıkları ve Doğum
    (126, 18),  # Covid-19 (Koronavirüs) -> Enfeksiyon Hastalıkları
    (127, 11),  # Cri Du Chat Sendromu -> Çocuk Nörolojisi
    (128, 21),  # Crohn Hastalığı -> Gastroenteroloji
    (129, 19),  # Cushing Sendromu -> Endokrinoloji
    (130, 18),  # Cüzzam Hastalığı -> Enfeksiyon Hastalıkları
    (131, 36),  # Çapraz Bağ Kopması -> Ortopedi
    (132, 42),  # Çarpık diş -> Diş Hekimliği
    (133, 17),  # Çatlak Nedir? -> Dermatoloji
    (134, 36),  # Çekiç parmak -> Ortopedi
    (135, 32),  # Çene Eklemi Rahatsızlığı -> KBB
    (136, 18),  # Çiçek Hastalığı -> Enfeksiyon Hastalıkları
    (137, 18),  # Çocuk Felci -> Enfeksiyon Hastalıkları
    (138, 9),  # Çocuklarda Hipertansiyon -> Çocuk Kardiyolojisi
    (139, 16),  # Çocuklarda İdrar Kaçırma -> Çocuk Ürolojisi
    (140, 3),  # Çocuklarda Kasık Fıtığı -> Çocuk Cerrahisi
    (141, 36),  # Çocuklarda kemik kistleri -> Ortopedi
    (142, 4),  # Çocuklarda Obezite -> Çocuk Endokrinolojisi
    (143, 36),  # Çocuklarda Topallama -> Ortopedi
    (144, 6),  # Çocuklarda Uyku Apnesi -> Çocuk Göğüs Hastalıkları
    (145, 27),  # Çoklu Organ Yetmezliği -> İç Hastalıkları
    (146, 21),  # Çölyak Hastalığı -> Gastroenteroloji
    (147, 34),  # Deli Dana Hastalığı -> Nöroloji
    (148, 38),  # Deliryum -> Psikiyatri
    (149, 34),  # Demans -> Nöroloji
    (150, 40),  # Dermatomiyozit -> Romatoloji
    (151, 29),  # Dermoid Kist -> Kadın Hastalıkları ve Doğum
    (152, 36),  # Dev Hücreli Kemik Tümörü -> Ortopedi
    (153, 19),  # Diabetes Insipidus -> Endokrinoloji
    (154, 18),  # Difteri (Kuşpalazı) -> Enfeksiyon Hastalıkları
    (155, 32),  # Dil Bağı Hastalığı -> KBB
    (156, 35),  # Dil Kanseri -> Onkoloji
    (157, 32),  # Dil Ülseri -> KBB
    (158, 36),  # Dirsek Kırığı -> Ortopedi
    (159, 21),  # Dispepsi -> Gastroenteroloji
    (160, 38),  # Distimi (Kronik Depresyon) -> Psikiyatri
    (161, 34),  # Distoni -> Nöroloji
    (162, 42),  # Diş apsesi -> Diş Hekimliği
    (163, 42),  # Diş Eti Çekilmesi -> Diş Hekimliği
    (164, 42),  # Diş Eti Hastalıkları -> Diş Hekimliği
    (165, 42),  # Diş Eti İltihabı -> Diş Hekimliği
    (166, 42),  # Diş Kırılması -> Diş Hekimliği
    (167, 42),  # Diş Kökü İltihabı -> Diş Hekimliği
    (168, 42),  # Diş Sıkma (Bruksizm) -> Diş Hekimliği
    (169, 22),  # Divertikülit -> Genel Cerrahi
    (170, 33),  # Diyabetik Nefropati -> Nefroloji
    (171, 24),  # Diyafram Felci -> Göğüs Hastalıkları
    (172, 36),  # Diz Kireçlenmesi -> Ortopedi
    (173, 18),  # Dizanteri -> Enfeksiyon Hastalıkları
    (174, 18),  # Domuz Gribi -> Enfeksiyon Hastalıkları
    (175, 34),  # Duchenne Musküler Distrofi -> Nöroloji
    (176, 35),  # Dudak Kanseri -> Onkoloji
    (177, 21),  # Dumping Sendromu -> Gastroenteroloji
    (178, 36),  # Dupuytren Kontraktürü -> Ortopedi
    (179, 27),  # Düşük Tansiyon -> İç Hastalıkları
    (180, 36),  # Düztabanlık -> Ortopedi
    (181, 18),  # Ebola Virüsü -> Enfeksiyon Hastalıkları
    (182, 17),  # Egzama -> Dermatoloji
    (183, 40),  # Ehlers-Danlos Sendromu -> Romatoloji
    (184, 15),  # El Ayak Ağız Hastalığı -> Çocuk Sağlığı ve Hastalıkları
    (185, 27),  # Elektrolit dengesizliği -> İç Hastalıkları
    (186, 21),  # Emilim Bozukluğu -> Gastroenteroloji
    (187, 29),  # Endometriozis -> Kadın Hastalıkları ve Doğum
    (188, 41),  # Epididimit -> Üroloji
    (189, 34),  # Epilepsi -> Nöroloji
    (190, 40),  # Erişkin Still Hastalığı -> Romatoloji
    (191, 41),  # Erkeklerde Kısırlık -> Üroloji
    (192, 41),  # Erken Boşalma -> Üroloji
    (193, 36),  # Ewing Sarkomu -> Ortopedi
    (194, 26),  # Fabry Hastalığı -> Hematoloji
    (195, 34),  # Fahr Sendromu -> Nöroloji
    (196, 9),  # Fallot Tetralojisi -> Çocuk Kardiyolojisi
    (197, 33),  # Fanconi Sendromu -> Nefroloji
    (198, 20),  # Faset Eklem Sendromu -> Fiziksel Tıp ve Rehabilitasyon
    (199, 4),  # Fenilketonüri Hastalığı -> Çocuk Endokrinolojisi
    (200, 29),  # Ferç kaşıntısı -> Kadın Hastalıkları ve Doğum
    (201, 29),  # Fibroadenom -> Kadın Hastalıkları ve Doğum
    (202, 20),  # Fibromiyalji -> Fiziksel Tıp ve Rehabilitasyon
    (203, 30),  # Fil Hastalığı -> Kalp ve Damar Cerrahisi
    (204, 11),  # Frajil X Sendromu -> Çocuk Nörolojisi
    (205, 36),  # Freiber Hastalığı -> Ortopedi
    (206, 18),  # Frengi (Sifiliz) -> Enfeksiyon Hastalıkları
    (207, 21),  # Gastrit -> Gastroenteroloji
    (208, 21),  # Gastroenterit -> Gastroenteroloji
    (209, 3),  # Gastroşizis -> Çocuk Cerrahisi
    (210, 26),  # Gaucher Hastalığı -> Hematoloji
    (211, 21),  # Geçirgen Bağırsak Sendromu -> Gastroenteroloji
    (212, 36),  # Gelişimsel Kalça Çıkığı -> Ortopedi
    (213, 27),  # Genetik Hastalıklar -> İç Hastalıkları
    (214, 29),  # Genital Siğil -> Kadın Hastalıkları ve Doğum
    (215, 29),  # Genital Uçuk -> Kadın Hastalıkları ve Doğum
    (216, 2),  # Gergin Omurilik Sendromu -> Beyin ve Sinir Cerrahisi
    (217, 35),  # Gırtlak Kanseri -> Onkoloji
    (218, 18),  # Giardia -> Enfeksiyon Hastalıkları
    (219, 27),  # Gilbert Sendromu -> İç Hastalıkları
    (220, 19),  # Gizli Şeker -> Endokrinoloji
    (221, 2),  # Glial Tümör -> Beyin ve Sinir Cerrahisi
    (222, 25),  # Glokom -> Göz Hastalıkları
    (223, 22),  # Göbek Deliği İltihabı -> Genel Cerrahi
    (224, 22),  # Göbek Fıtığı -> Genel Cerrahi
    (225, 23),  # Göğüs Duvarı Tümörü -> Göğüs Cerrahisi
    (226, 25),  # Göz Enfeksiyonu -> Göz Hastalıkları
    (227, 35),  # Göz Kanseri -> Onkoloji
    (228, 34),  # Göz Migreni -> Nöroloji
    (229, 19),  # Graves Hastalığı -> Endokrinoloji
    (230, 18),  # Grip -> Enfeksiyon Hastalıkları
    (231, 19),  # Guatr -> Endokrinoloji
    (232, 34),  # Guillain-Barre Sendromu -> Nöroloji
    (233, 40),  # Gut Hastalığı -> Romatoloji
    (234, 17),  # Gül Hastalığı -> Dermatoloji
    (235, 36),  # Güvercin Göğsü -> Ortopedi
    (236, 38),  # Halüsinasyon -> Psikiyatri
    (237, 32),  # Hareket Hastalığı -> KBB
    (238, 17),  # Harlequin fetüs -> Dermatoloji
    (239, 19),  # Haşimato -> Endokrinoloji
    (240, 21),  # Helikobakter Pilori -> Gastroenteroloji
    (241, 17),  # Hemanjiom -> Dermatoloji
    (242, 22),  # Hematom -> Genel Cerrahi
    (243, 34),  # Hemipleji -> Nöroloji
    (244, 26),  # Hemoglobinopati -> Hematoloji
    (245, 26),  # Hemokromatozis -> Hematoloji
    (246, 26),  # Hemolitik Anemi -> Hematoloji
    (247, 22),  # Hemoroid -> Genel Cerrahi
    (248, 18),  # Hepatit A -> Enfeksiyon Hastalıkları
    (249, 18),  # Hepatit B -> Enfeksiyon Hastalıkları
    (250, 18),  # Hepatit C -> Enfeksiyon Hastalıkları
    (251, 18),  # Hepatit E -> Enfeksiyon Hastalıkları
    (252, 1),  # Herediter Anjiyoödem -> Alerji ve İmmünoloji
    (253, 26),  # Herediter Sferositoz -> Hematoloji
    (254, 29),  # Hermafrodit -> Kadın Hastalıkları ve Doğum
    (255, 2),  # Hidrosefali -> Beyin ve Sinir Cerrahisi
    (256, 34),  # Hipersomnia -> Nöroloji
    (257, 19),  # Hipertiroidizm -> Endokrinoloji
    (258, 31),  # Hipertrofik Kardiyomiyopati -> Kardiyoloji
    (259, 19),  # Hipofiz Tümörleri -> Endokrinoloji
    (260, 41),  # Hipospadias -> Üroloji
    (261, 19),  # Hipotiroidi -> Endokrinoloji
    (262, 3),  # Hirschsprung Hastalığı -> Çocuk Cerrahisi
    (263, 34),  # Horner Sendromu -> Nöroloji
    (264, 29),  # HPV -> Kadın Hastalıkları ve Doğum
    (265, 14),  # HSP Hastalığı -> Çocuk Romatolojisi
    (266, 34),  # Huntington hastalığı -> Nöroloji
    (267, 4),  # Hurler Sendromu -> Çocuk Endokrinolojisi
    (268, 21),  # Huzursuz Bağırsak Sendromu -> Gastroenteroloji
    (269, 34),  # Huzursuz Bacak Sendromu -> Nöroloji
    (270, 21),  # Inflamatuar Bağırsak Hastalığı -> Gastroenteroloji
    (271, 34),  # Insomnia -> Nöroloji
    (272, 32),  # İç Kulak İltihabı -> KBB
    (273, 41),  # İdrar Yolu Enfeksiyonu -> Üroloji
    (274, 41),  # İktidarsızlık -> Üroloji
    (275, 1),  # İlaç Alerjisi -> Alerji ve İmmünoloji
    (276, 18),  # İnfluenza -> Enfeksiyon Hastalıkları
    (277, 41),  # İnmemiş Testis -> Üroloji
    (278, 19),  # İnsülin Direnci -> Endokrinoloji
    (279, 24),  # İnterstisyel Akciğer Hastalığı -> Göğüs Hastalıkları
    (280, 26),  # İTP Hastalığı -> Hematoloji
    (281, 36),  # İyi Huylu Kemik Tümörleri -> Ortopedi
    (282, 11),  # Joubert Sendromu -> Çocuk Nörolojisi
    (283, 18),  # Kabakulak -> Enfeksiyon Hastalıkları
    (284, 27),  # Kaçış Sendromu -> İç Hastalıkları
    (285, 29),  # Kadınlarda İdrar Kaçırma -> Kadın Hastalıkları ve Doğum
    (286, 36),  # Kalça Kireçlenmesi -> Ortopedi
    (287, 36),  # Kalça Labrum Yırtığı -> Ortopedi
    (288, 31),  # Kalp Anevrizması -> Kardiyoloji
    (289, 31),  # Kalp Damar Plağı -> Kardiyoloji
    (290, 31),  # Kalp Kası İltihabı -> Kardiyoloji
    (291, 31),  # Kalp Romatizması -> Kardiyoloji
    (292, 31),  # Kalp Yetmezliği -> Kardiyoloji
    (293, 29),  # Kan uyuşmazlığı -> Kadın Hastalıkları ve Doğum
    (294, 35),  # Kanser -> Onkoloji
    (295, 26),  # Kansızlık -> Hematoloji
    (296, 18),  # Kara Mantar Hastalığı -> Enfeksiyon Hastalıkları
    (297, 35),  # Karaciğer Kanseri -> Onkoloji
    (298, 21),  # Karaciğer Sirozu -> Gastroenteroloji
    (299, 21),  # Karaciğer Yağlanması -> Gastroenteroloji
    (300, 21),  # Karaciğer Yetmezliği -> Gastroenteroloji
    (301, 35),  # Karın Zarı Kanseri -> Onkoloji
    (302, 34),  # Karpal Tünel Sendromu -> Nöroloji
    (303, 24),  # Kartagener Sendromu -> Göğüs Hastalıkları
    (304, 34),  # Kas ve Sinir Hastalıkları -> Nöroloji
    (305, 22),  # Kasık Fıtığı -> Genel Cerrahi
    (306, 17),  # Kasık Mantarı -> Dermatoloji
    (307, 25),  # Katarakt -> Göz Hastalıkları
    (308, 9),  # Kawasaki Hastalığı -> Çocuk Kardiyolojisi
    (309, 40),  # Kelebek Hastalığı -> Romatoloji
    (310, 26),  # Kemik İliği Kanseri -> Hematoloji
    (311, 36),  # Kemik İltihabı -> Ortopedi
    (312, 36),  # Kemik Kanseri -> Ortopedi
    (313, 25),  # Keratokonus -> Göz Hastalıkları
    (314, 22),  # Kıl Dönmesi -> Genel Cerrahi
    (315, 18),  # Kıl Kurdu -> Enfeksiyon Hastalıkları
    (316, 31),  # Kırık Kalp Sendromu -> Kardiyoloji
    (317, 29),  # Kısırlık -> Kadın Hastalıkları ve Doğum
    (318, 18),  # Kızamık -> Enfeksiyon Hastalıkları
    (319, 18),  # Kızamıkçık -> Enfeksiyon Hastalıkları
    (320, 18),  # Kızıl Hastalığı -> Enfeksiyon Hastalıkları
    (321, 36),  # Kireçlenme -> Ortopedi
    (322, 5),  # Kistik Fibrozis -> Çocuk Gastroenterolojisi
    (323, 38),  # Kişilik Bozuklukları -> Psikiyatri
    (324, 38),  # Kleptomani -> Psikiyatri
    (325, 4),  # Klinefelter sendromu -> Çocuk Endokrinolojisi
    (326, 38),  # Klostrofobi -> Psikiyatri
    (327, 24),  # KOAH -> Göğüs Hastalıkları
    (328, 18),  # Kolera -> Enfeksiyon Hastalıkları
    (329, 31),  # Kolesterol -> Kardiyoloji
    (330, 21),  # Kolit ve Ülseratif Kolit -> Gastroenteroloji
    (331, 35),  # Kolon Kanseri -> Onkoloji
    (332, 36),  # Kondromalazi patella -> Ortopedi
    (333, 31),  # Konjestif kalp yetmezliği -> Kardiyoloji
    (334, 25),  # Konjonktivit -> Göz Hastalıkları
    (335, 32),  # Konka Hipertrofisi -> KBB
    (336, 17),  # Kontakt Dermatit -> Dermatoloji
    (337, 41),  # Kordon Kisti Ve Hidrosel -> Üroloji
    (338, 31),  # Koroner Arter Hastalığı -> Kardiyoloji
    (339, 29),  # Koryoamniyonit -> Kadın Hastalıkları ve Doğum
    (340, 17),  # Köpek Memesi Hastalığı -> Dermatoloji
    (341, 25),  # Kreatit -> Göz Hastalıkları
    (342, 26),  # Kronik Lenfositik Lösemi -> Hematoloji
    (343, 26),  # Kronik Miyeloid Lösemi -> Hematoloji
    (344, 29),  # Kronik Pelvik Ağrı -> Kadın Hastalıkları ve Doğum
    (345, 30),  # Kronik Venöz Yetmezlik -> Kalp ve Damar Cerrahisi
    (346, 27),  # Kronik Yorgunluk Sendromu -> İç Hastalıkları
    (347, 6),  # Krup Hastalığı -> Çocuk Göğüs Hastalıkları
    (348, 34),  # Kubital Tünel Sendromu -> Nöroloji
    (349, 18),  # Kuduz Hastalığı -> Enfeksiyon Hastalıkları
    (350, 32),  # Kulak Nezlesi -> KBB
    (351, 41),  # Kum Dökme -> Üroloji
    (352, 36),  # Kunduracı Göğsü -> Ortopedi
    (353, 1),  # Kurdeşen -> Alerji ve İmmünoloji
    (354, 32),  # Küçük Dil Şişmesi -> KBB
    (355, 34),  # Küme Baş Ağrısı -> Nöroloji
    (356, 34),  # Lafora Hastalığı -> Nöroloji
    (357, 35),  # Langerhans Hücreli Histiositoz -> Onkoloji
    (358, 32),  # Larenjit -> KBB
    (359, 18),  # Lejyoner Hastalığı -> Enfeksiyon Hastalıkları
    (360, 35),  # Lenf Kanseri -> Onkoloji
    (361, 18),  # Leptospiroz -> Enfeksiyon Hastalıkları
    (362, 17),  # Liken Planus -> Dermatoloji
    (363, 17),  # Liken Skleroz -> Dermatoloji
    (364, 30),  # Lipödem -> Kalp ve Damar Cerrahisi
    (365, 18),  # Listeria Hastalığı -> Enfeksiyon Hastalıkları
    (366, 29),  # Lohusalık Humması -> Kadın Hastalıkları ve Doğum
    (367, 26),  # Lösemi -> Hematoloji
    (368, 18),  # Lyme Hastalığı -> Enfeksiyon Hastalıkları
    (369, 38),  # Majör Depresyon -> Psikiyatri
    (370, 22),  # Makat Çatlağı -> Genel Cerrahi
    (371, 37),  # Makrodaktili -> Plastik Cerrahi
    (372, 17),  # Mantar Hastalığı -> Dermatoloji
    (373, 15),  # Marasmus -> Çocuk Sağlığı ve Hastalıkları
    (374, 31),  # Marfan Sendromu -> Kardiyoloji
    (375, 29),  # Mastit -> Kadın Hastalıkları ve Doğum
    (376, 17),  # Mastositoz -> Dermatoloji
    (377, 18),  # Mavi Dil Hastalığı -> Enfeksiyon Hastalıkları
    (378, 38),  # Mazoşizm -> Psikiyatri
    (379, 26),  # Megaloblastik Anemi -> Hematoloji
    (380, 34),  # Meige Sendromu -> Nöroloji
    (381, 29),  # Meme Enfeksiyonu -> Kadın Hastalıkları ve Doğum
    (382, 35),  # Meme Kanseri -> Onkoloji
    (383, 34),  # Menenjit -> Nöroloji
    (384, 32),  # Meniere Hastalığı -> KBB
    (385, 36),  # Menisküs -> Ortopedi
    (386, 18),  # Mers Virüsü -> Enfeksiyon Hastalıkları
    (387, 35),  # Mesane Kanseri -> Onkoloji
    (388, 35),  # Metastaz -> Onkoloji
    (389, 26),  # Methemoglobinemi -> Hematoloji
    (390, 22),  # Mezenterik İskemi -> Genel Cerrahi
    (391, 35),  # Mide Kanseri -> Onkoloji
    (392, 34),  # Migren -> Nöroloji
    (393, 31),  # Mitral Kapak Yetmezliği -> Kardiyoloji
    (394, 26),  # Miyelofibrozis -> Hematoloji
    (395, 29),  # Miyom -> Kadın Hastalıkları ve Doğum
    (396, 36),  # Miyozitis Ossifikans -> Ortopedi
    (397, 34),  # Moebius Sendromu -> Nöroloji
    (398, 34),  # MS Hastalığı -> Nöroloji
    (399, 26),  # Multipl Miyelom -> Hematoloji
    (400, 34),  # Myastenia Gravis -> Nöroloji
    (401, 26),  # Myelodisplastik Sendrom -> Hematoloji
    (402, 34),  # Narkolepsi -> Nöroloji
    (403, 17),  # Nasır -> Dermatoloji
    (404, 35),  # Nazofarenks Kanseri -> Onkoloji
    (405, 33),  # Nefrotik Sendrom -> Nefroloji
    (406, 17),  # Netherton Sendromu -> Dermatoloji
    (407, 25),  # Nistagmus -> Göz Hastalıkları
    (408, 18),  # Norovirüs -> Enfeksiyon Hastalıkları
    (409, 12),  # Nöroblastom -> Çocuk Onkolojisi
    (410, 34),  # Nörofibromatozis -> Nöroloji
    (411, 34),  # Nöropati -> Nöroloji
    (412, 27),  # Obezite -> İç Hastalıkları
    (413, 41),  # Oligospermi -> Üroloji
    (414, 3),  # Omfalosel -> Çocuk Cerrahisi
    (415, 2),  # Omurga Tümörleri -> Beyin ve Sinir Cerrahisi
    (416, 36),  # Omuz Çıkığı -> Ortopedi
    (417, 36),  # Omuz Kireçlenmesi -> Ortopedi
    (418, 26),  # Orak hücre anemisi -> Hematoloji
    (419, 18),  # ORF Hastalığı -> Enfeksiyon Hastalıkları
    (420, 32),  # Orta Kulak İltihabı -> KBB
    (421, 36),  # Osteoartrit -> Ortopedi
    (422, 36),  # Osteoid Osteoma Tümörü -> Ortopedi
    (423, 36),  # Osteomalazi -> Ortopedi
    (424, 36),  # Osteoporoz -> Ortopedi
    (425, 36),  # Osteosarkom -> Ortopedi
    (426, 13),  # Otizm -> Çocuk Psikiyatrisi
    (427, 40),  # Otoimmün Hastalıklar -> Romatoloji
    (428, 32),  # Otoskleroz -> KBB
    (429, 18),  # Öpücük Hastalığı -> Enfeksiyon Hastalıkları
    (430, 21),  # Özofajit -> Gastroenteroloji
    (431, 36),  # Paget Hastalığı -> Ortopedi
    (432, 21),  # Pangastrit -> Gastroenteroloji
    (433, 35),  # Pankreas Kanseri -> Onkoloji
    (434, 25),  # Papilödem -> Göz Hastalıkları
    (435, 2),  # Parapleji -> Beyin ve Sinir Cerrahisi
    (436, 19),  # Paratiroid Bezi Hastalıkları -> Endokrinoloji
    (437, 34),  # Parkinson -> Nöroloji
    (438, 31),  # Patent Foramen Ovale -> Kardiyoloji
    (439, 29),  # Pelvik İnflamatuar Hastalık -> Kadın Hastalıkları ve Doğum
    (440, 29),  # Pelvik Konjesyon Sendromu -> Kadın Hastalıkları ve Doğum
    (441, 17),  # Pemfigus -> Dermatoloji
    (442, 41),  # Penis Eğrilikleri -> Üroloji
    (443, 35),  # Penis Kanseri -> Onkoloji
    (444, 22),  # Perianal Fistül -> Genel Cerrahi
    (445, 30),  # Periferik Damar Hastalığı -> Kalp ve Damar Cerrahisi
    (446, 34),  # Periferik Nöropati -> Nöroloji
    (447, 31),  # Perikardiyal Efüzyon -> Kardiyoloji
    (448, 40),  # Periyodik Ateş Sendromu -> Romatoloji
    (449, 26),  # Pernisiyöz Anemi -> Hematoloji
    (450, 14),  # PFAPA Sendromu -> Çocuk Romatolojisi
    (451, 34),  # Pick Hastalığı -> Nöroloji
    (452, 38),  # Pika Sendromu -> Psikiyatri
    (453, 3),  # Pilor Stenozu -> Çocuk Cerrahisi
    (454, 36),  # Piriformis Sendromu -> Ortopedi
    (455, 38),  # Piromani Hastalığı -> Psikiyatri
    (456, 24),  # Plevral Efüzyon -> Göğüs Hastalıkları
    (457, 24),  # Pnömokonyoz -> Göğüs Hastalıkları
    (458, 34),  # PolG Hastalığı -> Nöroloji
    (459, 37),  # Polidaktili -> Plastik Cerrahi
    (460, 33),  # Polikistik Böbrek Hastalığı -> Nefroloji
    (461, 29),  # Polikistik Over Sendromu -> Kadın Hastalıkları ve Doğum
    (462, 25),  # Polikoria -> Göz Hastalıkları
    (463, 40),  # Polimiyozit -> Romatoloji
    (464, 34),  # Polinöropati -> Nöroloji
    (465, 22),  # Polip -> Genel Cerrahi
    (466, 26),  # Polisitemi -> Hematoloji
    (467, 25),  # Prematüre Retinopatisi -> Göz Hastalıkları
    (468, 36),  # Prepatellar Bursit -> Ortopedi
    (469, 25),  # Presbiyopi -> Göz Hastalıkları
    (470, 4),  # Progeria -> Çocuk Endokrinolojisi
    (471, 34),  # Prosopagnozi -> Nöroloji
    (472, 41),  # Prostat -> Üroloji
    (473, 41),  # Prostat İltihabı -> Üroloji
    (474, 35),  # Prostat Kanseri -> Onkoloji
    (475, 40),  # Psöriatik Artrit -> Romatoloji
    (476, 24),  # Pulmoner Fibrozis -> Göğüs Hastalıkları
    (477, 31),  # Pulmoner Hipertansiyon -> Kardiyoloji
    (478, 35),  # Rahim Ağzı Kanseri -> Onkoloji
    (479, 29),  # Rahim Duvarı Kalınlaşması -> Kadın Hastalıkları ve Doğum
    (480, 35),  # Rahim Kanseri -> Onkoloji
    (481, 29),  # Rahim Sarkması -> Kadın Hastalıkları ve Doğum
    (482, 32),  # Ramsay Hunt Sendromu -> KBB
    (483, 36),  # Raşitizm -> Ortopedi
    (484, 30),  # Raynaud Sendromu -> Kalp ve Damar Cerrahisi
    (485, 21),  # Reflü -> Gastroenteroloji
    (486, 29),  # Rektosel -> Kadın Hastalıkları ve Doğum
    (487, 35),  # Rektum Kanseri -> Onkoloji
    (488, 33),  # Renal Arter Stenozu -> Nefroloji
    (489, 25),  # Renk Körlüğü -> Göz Hastalıkları
    (490, 25),  # Retina Yırtığı -> Göz Hastalıkları
    (491, 25),  # Retinopati -> Göz Hastalıkları
    (492, 11),  # Rett Sendromu -> Çocuk Nörolojisi
    (493, 34),  # Reye Sendromu -> Nöroloji
    (494, 40),  # Romatizma -> Romatoloji
    (495, 40),  # Romatoid Artrit -> Romatoloji
    (496, 18),  # Rota Virüsü -> Enfeksiyon Hastalıkları
    (497, 36),  # Rotator Cuff Sendromu -> Ortopedi
    (498, 18),  # RSV -> Enfeksiyon Hastalıkları
    (499, 18),  # Ruam Hastalığı -> Enfeksiyon Hastalıkları
    (500, 17),  # Saçkıran -> Dermatoloji
    (501, 22),  # Safra Kesesi İltihabı -> Genel Cerrahi
    (502, 35),  # Safra Kesesi Kanseri -> Onkoloji
    (503, 22),  # Safra Kesesi Taşı -> Genel Cerrahi
    (504, 35),  # Safra Yolu Kanseri -> Onkoloji
    (505, 17),  # Sakal Kıran -> Dermatoloji
    (506, 18),  # Salmonella -> Enfeksiyon Hastalıkları
    (507, 1),  # Saman Nezlesi -> Alerji ve İmmünoloji
    (508, 25),  # Sarı Nokta Hastalığı -> Göz Hastalıkları
    (509, 24),  # Sarkoidoz -> Göğüs Hastalıkları
    (510, 17),  # Seboreik Dermatit -> Dermatoloji
    (511, 17),  # Sedef Hastalığı -> Dermatoloji
    (512, 11),  # Serebral Palsi -> Çocuk Nörolojisi
    (513, 34),  # Serebrovasküler Hastalıklar -> Nöroloji
    (514, 38),  # Serotonin Sendromu -> Psikiyatri
    (515, 41),  # Sertleşme Bozukluğu -> Üroloji
    (516, 21),  # SIBO -> Gastroenteroloji
    (517, 2),  # Sırt Fıtığı -> Beyin ve Sinir Cerrahisi
    (518, 18),  # Sıtma -> Enfeksiyon Hastalıkları
    (519, 24),  # Silikozis -> Göğüs Hastalıkları
    (520, 32),  # Sinüzit -> KBB
    (521, 33),  # Sistinozis -> Nefroloji
    (522, 41),  # Sistit -> Üroloji
    (523, 34),  # Siyatik -> Nöroloji
    (524, 40),  # Sjögren sendromu -> Romatoloji
    (525, 25),  # Sklerit -> Göz Hastalıkları
    (526, 40),  # Skleroderma -> Romatoloji
    (527, 27),  # Skorbüt hastalığı -> İç Hastalıkları
    (528, 34),  # SMA Hastalığı -> Nöroloji
    (529, 15),  # Soğuk Havale -> Çocuk Sağlığı ve Hastalıkları
    (530, 24),  # Solunum Yetmezliği -> Göğüs Hastalıkları
    (531, 38),  # Somatoform Bozukluk -> Psikiyatri
    (532, 34),  # Spastisite -> Nöroloji
    (533, 2),  # Spina Bifida -> Beyin ve Sinir Cerrahisi
    (534, 25),  # Stargardt Hastalığı -> Göz Hastalıkları
    (535, 36),  # Stres Kırığı -> Ortopedi
    (536, 18),  # Suçiçeği -> Enfeksiyon Hastalıkları
    (537, 25),  # Şalazyon -> Göz Hastalıkları
    (538, 18),  # Şap Hastalığı -> Enfeksiyon Hastalıkları
    (539, 25),  # Şaşılık -> Göz Hastalıkları
    (540, 38),  # Şizofreni -> Psikiyatri
    (541, 38),  # Şizotipal Kişilik Bozukluk -> Psikiyatri
    (542, 34),  # Tarsal Tünel Sendromu -> Nöroloji
    (543, 31),  # Taşikardi -> Kardiyoloji
    (544, 37),  # Tavşan Dudak -> Plastik Cerrahi
    (545, 25),  # Tavuk karası hastalığı -> Göz Hastalıkları
    (546, 34),  # Tay-Sachs Hastalığı -> Nöroloji
    (547, 17),  # Telenjiektazi -> Dermatoloji
    (548, 17),  # Telogen Effluvium -> Dermatoloji
    (549, 41),  # Testis İltihabı -> Üroloji
    (550, 35),  # Testis Kanseri -> Onkoloji
    (551, 41),  # Testis Torsiyonu -> Üroloji
    (552, 18),  # Tetanoz -> Enfeksiyon Hastalıkları
    (553, 36),  # Tetik Parmak -> Ortopedi
    (554, 35),  # Tırnak Tümörü -> Onkoloji
    (555, 18),  # Tifo -> Enfeksiyon Hastalıkları
    (556, 35),  # Timus Bezi Kanseri -> Onkoloji
    (557, 19),  # Tip 1 Diyabet -> Endokrinoloji
    (558, 19),  # Tip 2 Diyabet -> Endokrinoloji
    (559, 19),  # Tiroid -> Endokrinoloji
    (560, 35),  # Tiroid Kanseri -> Onkoloji
    (561, 18),  # Toksoplazma -> Enfeksiyon Hastalıkları
    (562, 32),  # Tonsilit -> KBB
    (563, 17),  # Topsy-Turvy Sendromu -> Dermatoloji
    (564, 36),  # Topuk Dikeni -> Ortopedi
    (565, 34),  # Torasik Outlet Sendromu -> Nöroloji
    (566, 36),  # Tortikolis -> Ortopedi
    (567, 34),  # Tourette Sendromu -> Nöroloji
    (568, 25),  # Trahom hastalığı -> Göz Hastalıkları
    (569, 34),  # Transvers Miyelit -> Nöroloji
    (570, 38),  # Travma Sonrası Stres Bozukluğu -> Psikiyatri
    (571, 34),  # Tremor -> Nöroloji
    (572, 34),  # Trigeminal Nevralji -> Nöroloji
    (573, 29),  # Trikomoniyaz -> Kadın Hastalıkları ve Doğum
    (574, 38),  # Trikotillomani -> Psikiyatri
    (575, 32),  # Trismus -> KBB
    (576, 18),  # Tularemi -> Enfeksiyon Hastalıkları
    (577, 4),  # Turner Sendromu -> Çocuk Endokrinolojisi
    (578, 18),  # Tüberküloz -> Enfeksiyon Hastalıkları
    (579, 35),  # Tükürük Bezi Kanseri -> Onkoloji
    (580, 26),  # Tüylü Hücreli Lösemi -> Hematoloji
    (581, 17),  # Uçuk Hastalığı -> Dermatoloji
    (582, 29),  # Ureaplasma -> Kadın Hastalıkları ve Doğum
    (583, 24),  # Uyku Apnesi -> Göğüs Hastalıkları
    (584, 34),  # Uyku terörü -> Nöroloji
    (585, 17),  # Uyuz Hastalığı -> Dermatoloji
    (586, 21),  # Ülser -> Gastroenteroloji
    (587, 41),  # Üreter Taşı -> Üroloji
    (588, 41),  # Üretra Darlığı -> Üroloji
    (589, 35),  # Üretra Kanseri -> Onkoloji
    (590, 25),  # Üveit -> Göz Hastalıkları
    (591, 29),  # Vajinal Mantar -> Kadın Hastalıkları ve Doğum
    (592, 29),  # Vajinismus -> Kadın Hastalıkları ve Doğum
    (593, 41),  # Varikosel -> Üroloji
    (594, 30),  # Varis -> Kalp ve Damar Cerrahisi
    (595, 40),  # Vaskülit -> Romatoloji
    (596, 18),  # Veba -> Enfeksiyon Hastalıkları
    (597, 9),  # Ventriküler Septal Defekt -> Çocuk Kardiyolojisi
    (598, 31),  # Ventriküler Taşikardi -> Kardiyoloji
    (599, 17),  # Vitiligo -> Dermatoloji
    (600, 26),  # Von Willebrand hastalığı -> Hematoloji
    (601, 35),  # Vulva Kanseri -> Onkoloji
    (602, 29),  # Vulvar Egzama -> Kadın Hastalıkları ve Doğum
    (603, 29),  # Vulvodini -> Kadın Hastalıkları ve Doğum
    (604, 24),  # Vurgun -> Göğüs Hastalıkları
    (605, 26),  # Waldenström Makroglobulinemisi -> Hematoloji
    (606, 18),  # Whipple Hastalığı -> Enfeksiyon Hastalıkları
    (607, 12),  # Wilms Tümörü -> Çocuk Onkolojisi
    (608, 21),  # Wilson Hastalığı -> Gastroenteroloji
    (609, 31),  # Wolf Parkinson White Sendromu -> Kardiyoloji
    (610, 38),  # Yalan Söyleme Hastalığı -> Psikiyatri
    (611, 35),  # Yemek Borusu Kanseri -> Onkoloji
    (612, 15),  # Yenidoğan Sarılığı -> Çocuk Sağlığı ve Hastalıkları
    (613, 18),  # Yılancık Hastalığı -> Enfeksiyon Hastalıkları
    (614, 29),  # Yumurta Rezervi Düşüklüğü -> Kadın Hastalıkları ve Doğum
    (615, 35),  # Yumurtalık Kanseri -> Onkoloji
    (616, 29),  # Yumurtalık Kisti -> Kadın Hastalıkları ve Doğum
    (617, 35),  # Yumuşak Doku Sarkomu -> Onkoloji
    (618, 31),  # Yüksek Tansiyon -> Kardiyoloji
    (619, 34),  # Yüz Felci -> Nöroloji
    (620, 24),  # Zatürre -> Göğüs Hastalıkları
    (621, 4),  # Zellweger Sendromu -> Çocuk Endokrinolojisi
    (622, 32),  # Zenker Divertikülü -> KBB
    (623, 21),  # Zollinger-Ellison Sendromu -> Gastroenteroloji
    (624, 17),
]


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
    for hastalik, bolum in hastalik_bolum_eslesmeleri:
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


def get_each_QA(main_div, search_text):

    # sık sorulan sorular içeren h2 yi bul.
    h2_tag = main_div.find("h2", string=re.compile(search_text, re.IGNORECASE))

    if h2_tag == None:
        return ""
    else:
        QA_list = []

        # h2 den sonraki aynı seviyedeki tag leri dön
        for sib in h2_tag.next_siblings:
            if isinstance(sib, Tag):
                if sib.name == "h2":
                    break  # sonraki h2 geldi -> çık

                if sib.name == "h3":

                    question = sib.get_text()

                    # h3'ün cevabı genellikle bir sonraki p olur
                    answer_tag = sib.find_next_sibling("p")
                    if answer_tag:
                        answer = answer_tag.get_text()
                        qa = {"q": question, "a": answer}
                        QA_list.append(qa)

        if len(QA_list) < 1:
            return ""

        qa_text_list = []

        for qa in QA_list:
            qa_text = f"{qa['q']}: {qa['a']}"
            qa_text_list.append(qa_text)

        return qa_text_list


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
            "soru_cevap": "",
            "link": full_link,
        }
        full_data_list.append(dict_item)

    for i in range(len(full_link_list)):

        # hastalığın sayfasına git ve oradaki temel alınacak tag i al
        full_div = follow_and_find(full_link_list[i], "div", "article")

        if full_div == None:
            print("\n--------- ******** Bulunamadı ********* ----------\n")
            continue

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

        # Tedavi kısmını topla
        tedavi_desc = " ".join(get_full_desc(full_div, "tedavisi Nasıl Yapılır?"))
        tedavi_desc = tedavi_desc + " ".join(
            get_full_desc(full_div, "Nasıl Tedavi Edilir?")
        )

        # Sık sorulan sorular kısmını topla
        qa_list = " ".join(get_each_QA(full_div, "sık sorulan sorular"))
        print(qa_list + "\n")

        full_data_list[i]["nedir"] = nedir_desc
        full_data_list[i]["belirtiler"] = belirtiler_desc
        full_data_list[i]["türleri"] = turleri_desc
        full_data_list[i]["teshis"] = teshisi_desc
        full_data_list[i]["tedavi"] = tedavi_desc
        full_data_list[i]["bolum"] = get_bolum_by_hastalik_no(i)
        full_data_list[i]["soru_cevap"] = qa_list

    save_table(full_data_list, "data/raw/hastaliklar_detayli_listesi.csv")
