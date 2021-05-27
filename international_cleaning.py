#!/usr/bin/env python3

import csv
import argparse
import geopandas as gp
from collections import defaultdict
from collections import Counter
import os
import ftfy
import unicodedata

def remove_weird_characters(s):
    s = ftfy.fix_text(s)
    s = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
    return s

def load_international_files(utils_dir):

    acceptable_adm0s = []
    acceptable_adm1s = []
    adm0_clean_dict = {}
    adm1_clean_dict = {}


    with open(os.path.join(utils_dir,"clean_adm0_list.tsv")) as f:
        data = csv.DictReader(f,delimiter="\t")
        for l in data:
            acceptable_adm0s.append(l['adm0'].upper().replace(" ","_").replace("-","_"))

    with open(os.path.join(utils_dir,"clean_adm1_list.tsv")) as f:
        data = csv.DictReader(f,delimiter="\t")
        for l in data:
            acceptable_adm1s.append(l['adm1'].upper().replace(" ","_").replace("-","_"))

    with open(os.path.join(utils_dir,"adm0_cleaning.csv")) as f:
        data = csv.DictReader(f)
        for l in data:
            adm0_clean_dict[l['input_adm0']] = l['clean_adm0']

    with open(os.path.join(utils_dir,"adm1_cleaning.csv")) as f:
        data = csv.DictReader(f)
        for l in data:
            adm1_clean_dict[l['input_adm1']] = l['clean_adm1']

    return acceptable_adm0s, acceptable_adm1s, adm0_clean_dict, adm1_clean_dict


def clean_adm1(adm1_raw, acceptable_adm1s, adm1_clean_dict, unclean_adm1):

    no_weirds = remove_weird_characters(adm1_raw)
    lookup = no_weirds.upper().replace(" ","_").replace("-","_")

    if lookup in acceptable_adm1s:
        adm1 = lookup.title()
    elif lookup in adm1_clean_dict:
        adm1 = adm1_clean_dict[lookup].title()
    else:
        unclean_adm1.append(adm1_raw)
        adm1 = ""

    return adm1, unclean_adm1
    

def clean_adm0(adm0_raw, acceptable_adm0s, adm0_clean_dict, unclean_adm0):

    no_weirds = remove_weird_characters(adm0_raw)
    lookup = no_weirds.upper().replace(" ","_").replace("-","_")

    initials = ["UK","USA","DRC"]

    if lookup in acceptable_adm0s:
        if lookup not in initials:
            adm0 = lookup.title()
        else:
            adm0 = lookup
    elif lookup in adm0_clean_dict:
        if adm0_clean_dict[lookup] not in initials:
            adm0 = adm0_clean_dict[lookup].title()
        else:
            adm0 = adm0_clean_dict[lookup]
    else:
        unclean_adm0.add(adm0_raw)
        adm0 = ""

    return adm0, unclean_adm0

def international_cleaning(geog_dict, unclean_adm0, unclean_adm1, acceptable_adm0s, acceptable_adm1s, adm0_clean_dict, adm1_clean_dict):


    if geog_dict['adm1_raw'] == "Luxembourg":
        adm1 = ""
        adm0 = "Luxembourg"
    else:
        if geog_dict['country'] != "":
            adm0, unclean_adm0 = clean_adm0(geog_dict["country"], acceptable_adm0s, adm0_clean_dict, unclean_adm0)
        else:
            adm0 = ""
        if geog_dict['adm1_raw'] != "":
            adm1, unclean_adm1 = clean_adm1(geog_dict["adm1_raw"], acceptable_adm1s, adm1_clean_dict, unclean_adm1)
        else:
            adm1 = ""

    geog_dict["adm1"] = adm1
    geog_dict["country"] = adm0


    return geog_dict, unclean_adm0, unclean_adm1


def write_international_missing_file(unclean_adm0, unclean_adm1, outdir): #if >100 sequences and not in acceptable list after cleaning

    fw_adm1 = open(os.path.join(outdir,"missing_adm1.csv"),'w')
    fw_adm1.write("place,count\n")
    unclean_adm1_counts = Counter(unclean_adm1)

    for place, count in unclean_adm1_counts.items():
        if count >= 100:
            fw_adm1.write(f'{place},{count}\n')

    fw_adm0 = open(os.path.join(outdir,"missing_adm0.csv"),'w')
    for country in unclean_adm0:
        fw_adm0.write(country + "\n")

    fw_adm0.close()
    fw_adm1.close()
    
    