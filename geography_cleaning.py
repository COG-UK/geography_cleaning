#!/usr/bin/env python3

import csv
import argparse
import geopandas as gp
from collections import defaultdict
from collections import Counter
import os


def do_outer_postcode_region_latlong(geog_dict, outer_postcode, outer_to_latlongs_region):

    lst = outer_to_latlongs_region[outer_postcode]

    if len(lst) > 0:
        region = lst[0]
        lat = lst[1][0]
        longi = lst[1][1]
    else:
        return True

    geog_dict["region"] = region
    geog_dict["latitude"] = lat
    geog_dict["longitude"] = longi

    return geog_dict

def process_adm2(outer_postcode, adm2, metadata_multi_loc, straight_map, not_mappable, postcode_to_adm2, adm1, nuts_list):

    country_to_adm2, adm2_to_country, acceptable_adm2s = get_acceptable_adm2()
    adm2 = adm2.upper().replace(" ","_")

    if outer_postcode != "" and (adm2 == "" or adm2 in not_mappable):
        if outer_postcode in postcode_to_adm2:
            processed_adm2 = postcode_to_adm2[outer_postcode]
            source = "outer_postcode"
        else:
            processed_adm2 = ""
            source = ""

    elif adm2 in nuts_list:
        processed_adm2 = ""
        source = "nuts_provided"

    elif adm2 != "":
        if adm2 in acceptable_adm2s:
            processed_adm2 = adm2
            source = "adm2_raw"
        elif "|" in adm2:
            processed_adm2 = adm2
            source = "adm2_raw"
        else:
            processed_adm2 = clean_adm2(adm2, metadata_multi_loc, straight_map, not_mappable)
            if type(processed_adm2) != bool:
                if processed_adm2 == "":
                    source = ""
                else:
                    source = "cleaned_adm2_raw"
            else:
                source = ""


    #Check if the adm2 is vague but the postcode can narrow it down
    if type(processed_adm2) != bool:
        if "|" in processed_adm2 and outer_postcode != "" and outer_postcode in postcode_to_adm2:
            if "|" not in postcode_to_adm2[outer_postcode] and postcode_to_adm2[outer_postcode] in processed_adm2:
                processed_adm2 = postcode_to_adm2[outer_postcode]
                source = "outer_postcode"

        #if it goes across borders, pick the place in the right country
        country_list = set()
        if "|" in processed_adm2 and adm1 != "":
            for place in processed_adm2.split("|"):
                country_list.add(adm2_to_country[place])

        if len(country_list) > 1:
            new_adm2 = []
            acceptables = country_to_adm2[adm1]
            for place in processed_adm2.split("|"):
                if place in acceptables:
                    new_adm2.append(place)

            processed_adm2 = "|".join(sorted(new_adm2))
            source = source + "_plus_country"

    #check conflicts between input adm2 and postcode
    conflict = False
    if outer_postcode in postcode_to_adm2 and source != "outer_postcode" and source != "":
        pc_adm2 = postcode_to_adm2[outer_postcode]
        if "|" not in pc_adm2 and "|" not in processed_adm2:
            if pc_adm2 != processed_adm2:
                conflict = True
        else:
            if not any([i for i in pc_adm2.split("|") if i in processed_adm2.split("|")]) and not any([i for i in processed_adm2.split("|") if i in pc_adm2.split("|")]):
                conflict = True    

        if conflict:
            processed_adm2 = pc_adm2
            source = "postcode_conflict_resolution"


    return processed_adm2, source, conflict


def do_adm1(country):

    adm1 = ""

    contract_dict = {"SCT":"Scotland", "WLS": "Wales", "ENG":"England", "NIR": "Northern_Ireland"}
    cleaning = {"SCOTLAND":"Scotland", "WALES":"Wales", "ENGLAND":"England", "NORTHERN_IRELAND": "Northern_Ireland", "NORTHERN IRELAND": "Northern_Ireland",
    "FK":"Falkland_Islands", "GI":"Gibraltar", "JE": "Jersey", "IM":"Isle_of_Man", "GG":"Guernsey"}

    if "UK" in country:
        try:
            adm1_prep = country.split("-")[1]
        except IndexError:
            print(country)
        adm1 = contract_dict[adm1_prep]
    else:
        if country.upper() in cleaning.keys():
            adm1 = cleaning[country.upper()]

    return adm1


def clean_adm2(adm2, metadata_multi_loc, straight_map, not_mappable):

    new_unclean = False

    if adm2 != "" and adm2 not in not_mappable:
        if adm2 in straight_map.keys():
            processed_prep = straight_map[adm2]
            if processed_prep in metadata_multi_loc.keys():
                processed = metadata_multi_loc[processed_prep]
            else:
                processed = processed_prep

        elif adm2 in metadata_multi_loc.keys():
            processed = "|".join(sorted([i for i in metadata_multi_loc[adm2]]))

        else:
            new_unclean = True
            return new_unclean

    elif adm2 in not_mappable:
        processed = ""

    return processed

def prep_adm2_data(clean_locs_file):

    metadata_multi_loc = defaultdict(list)
    straight_map = {}

    with open(clean_locs_file) as f:
        next(f)
        for l in f:
            toks = l.strip("\n").split("\t")
            toks [:] = [x for x in toks if x]
            metadata_loc = toks[0].replace(" ","_")
            real_locs = toks[1:]

            if len(real_locs) == 1:
                straight_map[metadata_loc] = real_locs[0].upper()
            else:
                metadata_multi_loc[metadata_loc] = real_locs

    return metadata_multi_loc, straight_map


def get_acceptable_adm2():

    country_to_adm2 = {
    "England":['BARNSLEY', 'BATH_AND_NORTH_EAST_SOMERSET', 'BEDFORDSHIRE', 'BIRMINGHAM', 'BLACKBURN_WITH_DARWEN', 'BLACKPOOL', 'BOLTON', 'BOURNEMOUTH', 'BRACKNELL_FOREST', 'BRADFORD', 'BRIGHTON_AND_HOVE', 'BRISTOL', 'BUCKINGHAMSHIRE', 'BURY',
    'CALDERDALE', 'CAMBRIDGESHIRE', 'CENTRAL_BEDFORDSHIRE', 'CHESHIRE_EAST', 'CHESHIRE_WEST_AND_CHESTER', 'CORNWALL', 'COVENTRY', 'CUMBRIA',
    'DARLINGTON', 'DERBY', 'DERBYSHIRE', 'DEVON', 'DONCASTER', 'DORSET', 'DUDLEY', 'DURHAM',
    'EAST_RIDING_OF_YORKSHIRE', 'EAST_SUSSEX', 'ESSEX',
    'GATESHEAD', 'GLOUCESTERSHIRE', 'GREATER_LONDON',
    'HALTON', 'HAMPSHIRE', 'HARTLEPOOL', 'HEREFORDSHIRE', 'HERTFORDSHIRE',
    'ISLE_OF_WIGHT', 'ISLES_OF_SCILLY',
    'KENT', 'KINGSTON_UPON_HULL', 'KIRKLEES', 'KNOWSLEY',
    'LANCASHIRE', 'LEEDS', 'LEICESTER', 'LEICESTERSHIRE', 'LINCOLNSHIRE', 'LUTON',
    'MANCHESTER', 'MEDWAY', 'MIDDLESBROUGH', 'MILTON_KEYNES',
    'NEWCASTLE_UPON_TYNE', 'NORFOLK', 'NORTH_LINCOLNSHIRE', 'NORTH_SOMERSET', 'NORTH_TYNESIDE', 'NORTH_YORKSHIRE', 'NORTHAMPTONSHIRE', 'NORTHUMBERLAND', 'NOTTINGHAM', 'NOTTINGHAMSHIRE',
    'OLDHAM', 'OXFORDSHIRE',
    'PETERBOROUGH', 'PLYMOUTH', 'POOLE', 'PORTSMOUTH',
    'READING', 'REDCAR_AND_CLEVELAND', 'ROCHDALE', 'ROTHERHAM', 'RUTLAND',
    'SAINT_HELENS', 'SALFORD', 'SANDWELL', 'SEFTON', 'SHEFFIELD', 'SHROPSHIRE', 'SLOUGH', 'SOLIHULL', 'SOMERSET', 'SOUTH_GLOUCESTERSHIRE', 'SOUTH_TYNESIDE', 'SOUTHAMPTON', 'SOUTHEND-ON-SEA', 'STAFFORDSHIRE', 'STOCKPORT', 'STOCKTON-ON-TEES', 'STOKE-ON-TRENT', 'SUFFOLK', 'SUNDERLAND', 'SURREY', 'SWINDON',
    'TAMESIDE', 'TELFORD_AND_WREKIN', 'THURROCK', 'TORBAY', 'TRAFFORD', 'WAKEFIELD', 'WALSALL', 'WARRINGTON', 'WARWICKSHIRE', 'WEST_BERKSHIRE', 'WEST_SUSSEX', 'WIGAN', 'WILTSHIRE', 'WINDSOR_AND_MAIDENHEAD', 'WIRRAL', 'WOKINGHAM', 'WOLVERHAMPTON', 'WORCESTERSHIRE', 'YORK'],
    "Northern_Ireland":['ANTRIM_AND_NEWTOWNABBEY', 'ARMAGH_BANBRIDGE_AND_CRAIGAVON', 'BELFAST', 'CAUSEWAY_COAST_AND_GLENS', 'DERRY_AND_STRABANE', 'FERMANAGH_AND_OMAGH', 'LISBURN_AND_CASTLEREAGH', 'MID_AND_EAST_ANTRIM', 'MID_ULSTER', 'NEWRY_MOURNE_AND_DOWN', 'NORTH_DOWN_AND_ARDS', 'TYRONE', 'ANTRIM', 'ARMAGH', 'FERMANAGH', 'LONDONDERRY', 'DOWN'],
    "Scotland":['ABERDEEN', 'ABERDEENSHIRE', 'ANGUS', 'ARGYLL_AND_BUTE', 'CLACKMANNANSHIRE', 'DUMFRIES_AND_GALLOWAY', 'DUNDEE', 'EAST_AYRSHIRE', 'EAST_DUNBARTONSHIRE', 'EAST_LOTHIAN', 'EAST_RENFREWSHIRE', 'EDINBURGH', 'EILEAN_SIAR', 'FALKIRK', 'FIFE',
    'GLASGOW', 'HIGHLAND', 'INVERCLYDE', 'MIDLOTHIAN', 'MORAY', 'NORTH_AYRSHIRE', 'NORTH_LANARKSHIRE', 'ORKNEY_ISLANDS', 'PERTHSHIRE_AND_KINROSS', 'RENFREWSHIRE', 'SCOTTISH_BORDERS', 'SHETLAND_ISLANDS', 'SOUTH_AYRSHIRE', 'SOUTH_LANARKSHIRE', 'STIRLING', 'WEST_DUNBARTONSHIRE', 'WEST_LOTHIAN'],
    "Wales":['ANGLESEY', 'BLAENAU_GWENT', 'BRIDGEND', 'CAERPHILLY', 'CARDIFF', 'CARMARTHENSHIRE', 'CEREDIGION', 'CONWY', 'DENBIGHSHIRE', 'FLINTSHIRE', 'GWYNEDD', 'MERTHYR_TYDFIL', 'MONMOUTHSHIRE', 'NEATH_PORT_TALBOT', 'NEWPORT', 'PEMBROKESHIRE', 'POWYS', 'RHONDDA_CYNON_TAFF', 'SWANSEA', 'TORFAEN', 'VALE_OF_GLAMORGAN', 'WREXHAM'],
    "Channel_Islands":['GUERNSEY', "JERSEY"], # probably remove this and one below later on when the new adm1s are integrated, but it should work either way
    "British_overseas_territories": ["FALKLAND_ISLANDS", "GIBRALTAR"]
    }

    adm2_to_country = {}
    acceptable_adm2s = []
    for country,adm2_list in country_to_adm2.items():
        for adm2 in adm2_list:
            adm2_to_country[adm2] = country
            acceptable_adm2s.append(adm2)

    acceptable_adm2s.append("ISLE_OF_MAN")

    return country_to_adm2, adm2_to_country, acceptable_adm2s

def read_in_postcode_to_adm2(input_file):

    postcode_to_adm2 = {}

    with open(input_file) as f:
        next(f)
        for l in f:
            toks = l.strip("\n").split("\t")
            postcode_to_adm2[toks[0]] = toks[1]

    return postcode_to_adm2

def find_outerpostcode_to_coord_mapping(map_utils_dir):

    cleaning_outer_pc = {}
    outer_to_latlongs_region = defaultdict(list)

    with open(os.path.join(map_utils_dir,"outer_postcode_cleaning.csv")) as f:
        next(f)
        for l in f:
            toks = l.strip("\n").split(",")
            cleaning_outer_pc[toks[0]] = toks[1]

    with open(os.path.join(map_utils_dir,"outer_postcodes_latlongs_region.csv")) as f:
        i = csv.DictReader(f)
        data = [r for r in i]
        for seq in data:
            outer = seq["outer_postcode"]
            region = seq["region"]
            coords = (seq["lat"],seq["long"])

            if outer in cleaning_outer_pc.keys():
                clean_outer = cleaning_outer_pc[outer]
            else:
                clean_outer = outer

            outer_to_latlongs_region[clean_outer] = [region, coords]

    return outer_to_latlongs_region

def get_nuts_list(nuts_file):

    nuts_to_constituents = defaultdict(list)

    with open(nuts_file) as f:
        for l in f:
            toks = l.strip("\n").split("\t")
            toks [:] = [x for x in toks if x]
            nuts = toks[0]
            constituents = toks[1:]

            nuts_to_constituents[nuts] = constituents

    return nuts_to_constituents

def generate_adm2_to_utla(lookup_file):
    adm2_to_utla = defaultdict(set)
    utla_codes = {}
    suggested_grouping = {}
    with open(lookup_file) as f:
        data = csv.DictReader(f)
        for l in data:
            utla_code = l["UTLA_code"]
            utla_name = l["UTLA_name"]
            adm2 = l['adm2']
            sug_adm2 = l['aggregated_adm2']

            adm2_to_utla[adm2].add(utla_name)
            utla_codes[utla_name] = utla_code
            suggested_grouping[adm2] = sug_adm2

    return adm2_to_utla, utla_codes, suggested_grouping

def make_safe_loc(adm2_to_week_counts, geog_dict, epiweek, non_uks, safe_locs):

    adm2 = geog_dict["adm2"]
    agg_adm2 = geog_dict["suggested_adm2_grouping"]
    nuts = geog_dict["NUTS1"]
    adm1 = geog_dict["adm1"]

    if adm2 != "":
        if float(adm2_to_week_counts[adm2][epiweek]) >= 5:
            safe_loc = adm2
        elif "|" in adm2:
            parts = adm2.split("|")
            count = 0
            for ele in parts:
                if ele in adm2_to_week_counts.keys():
                    if epiweek in adm2_to_week_counts[ele]:
                        count += float(adm2_to_week_counts[ele][epiweek])
            if count >= 5:
                safe_loc = adm2
            else:
                safe_loc = ""
        else:
            safe_loc = ""
    else:
        safe_loc = ""
            
    if safe_loc == "" and agg_adm2 != "":
        if float(adm2_to_week_counts[agg_adm2][epiweek]) >= 5:
            safe_loc = agg_adm2
        elif "|" in agg_adm2:
            parts = agg_adm2.split("|")
            count = 0
            for ele in parts:
                if ele in adm2_to_week_counts.keys():
                    if epiweek in adm2_to_week_counts[ele]:
                        count += float(adm2_to_week_counts[ele][epiweek])
            if count >= 5:
                safe_loc = agg_adm2
            else:
                safe_loc = nuts
        else:
            safe_loc = nuts
    
    if safe_loc == "" and nuts != "":
        safe_loc = nuts

    if adm1 in non_uks:
        if float(adm2_to_week_counts[adm1][epiweek]) >= 5:
            safe_loc = adm1
        elif float(adm2_to_week_counts[safe_locs[adm1]][epiweek]) >= 5:
            safe_loc = safe_locs[adm1]
        else:
            safe_loc = ""

    return safe_loc

def deal_with_nonuk_cog(country, adm1, adm2, epiweek, geog_dict, adm2_to_week_counts, safe_locs):

    if adm2 != "":
        adm1 = adm2.title().replace("Of","of")

    if country != adm1:
        country = adm1

    geog_dict["adm1"] = adm1
    geog_dict["country"] = country
    geog_dict["adm2"] = ""
    geog_dict["adm2_source"] = ""
    geog_dict["NUTS1"] = ""
    geog_dict["location"] = adm1.replace("_"," ").title().replace("Of", "of")
    geog_dict["utla"] = "" 
    geog_dict["utla_code"] = ""
    geog_dict["suggested_adm2_grouping"] = ""

    adm1_lookup = adm1.upper()

    safe_loc = safe_locs[adm1_lookup]

    if adm1_lookup in adm2_to_week_counts.keys():
        if epiweek in adm2_to_week_counts[adm1_lookup].keys():
            adm2_to_week_counts[adm1_lookup][epiweek] += 1
        else:
            adm2_to_week_counts[adm1_lookup][epiweek] = 1
    else:
        adm2_to_week_counts[adm1_lookup] = {}
        adm2_to_week_counts[adm1_lookup][epiweek] = 1
    
    if safe_loc in adm2_to_week_counts.keys():
        if epiweek in adm2_to_week_counts[safe_loc].keys():
            adm2_to_week_counts[safe_loc][epiweek] += 1
        else:
            adm2_to_week_counts[safe_loc][epiweek] = 1
    else:
        adm2_to_week_counts[safe_loc] = {}
        adm2_to_week_counts[safe_loc][epiweek] = 1

    return geog_dict, adm2_to_week_counts


def process_input(metadata_file, country_col, outer_postcode_col, adm1_col, adm2_col, epiweek_col, map_utils_dir,outdir):

    outer_to_latlongs_region = find_outerpostcode_to_coord_mapping(map_utils_dir)
    metadata_multi_loc, straight_map = prep_adm2_data(os.path.join(map_utils_dir, "adm2_cleaning.tsv"))
    nuts_dict = get_nuts_list(os.path.join(map_utils_dir, "nuts_to_adm2.tsv"))
    postcode_to_adm2 = read_in_postcode_to_adm2(os.path.join(map_utils_dir, "postcode_to_adm2.tsv"))

    new_unclean_locations = open(os.path.join(outdir, "new_unclean_locations.csv"), 'w')
    new_unclean_postcodes = open(os.path.join(outdir, "new_unclean_postcodes.csv"), 'w')
    postcodes_with_no_adm2 = open(os.path.join(outdir, "postcodes_without_adm2.csv"), 'w')
    incompatible_locations = open(os.path.join(outdir,"sequences_with_incompatible_locs.csv"), 'w')
    log_file = open(os.path.join(outdir, "log_file.txt"), 'w')

    incompatible_locations.write(f'name,input_postcode,input_adm2,adm2_from_postcode,adm2_from_input_adm2\n')

    adm2_to_utla, utla_codes, suggested_groupings = generate_adm2_to_utla(os.path.join(map_utils_dir, "LAD_UTLA_adm2.csv"))

    already_found = []
    done_postcodes = []
    
    outer_geog_dict = defaultdict(dict)
    adm2_to_week_counts = defaultdict(dict)
    epiweek_dict = {}

    missing_adm1 = 0
    missing_adm2 = 0
    missing_op = 0
    curation = 0
    conflict_count = 0

    nice_names = commonly_used_names()

    country_list = ["UK", "Falkland Islands", "Gibraltar", "Jersey", "Isle of Man", "Guernsey"]
    non_uk = ["FALKLAND_ISLANDS", 'GIBRALTAR', 'JERSEY', 'ISLE_OF_MAN', 'GUERNSEY']

    not_mappable = ["NA","WALES", "YORKSHIRE", "OTHER", "UNKNOWN", "UNKNOWN_SOURCE", "NOT_FOUND", "CITY_CENTRE", "NONE"] 
    missing_postcodes = ["ZZ9", "ZZ99", "99ZZ", "UNKNOWN", "BF1", "BF10"] #the BFs are british forces overseas, but can't narrow down where in the world from just the outer postcode
    NI_counties = ['TYRONE', 'ANTRIM', 'ARMAGH', 'FERMANAGH', 'LONDONDERRY', 'DOWN']

    safe_locs = {"FALKLAND_ISLANDS": "OVERSEAS_TERRITORY", 'GIBRALTAR':'OVERSEAS_TERRITORY', 'JERSEY':'CHANNEL_ISLANDS', 'GUERNSEY':'CHANNEL_ISLANDS', 'ISLE_OF_MAN':''}

    already_checked_discreps = ["LOND-12508C8", "LOND-1263D3C", "LOND-1263622", "NORT-29A8E3", "PORT-2D7668"]

    fixed_seqs = {"NORT-289270": "DL12"}

    with open(metadata_file) as f:
        data = csv.DictReader(f)
        for sequence in data:
            conflict = False
            country = sequence[country_col]
            adm1 = sequence[adm1_col]
            outer_postcode = sequence[outer_postcode_col].upper().strip(" ")
            adm2 = sequence[adm2_col]
            name = sequence["central_sample_id"]


            if name in fixed_seqs:
                outer_postcode = fixed_seqs[name]

            geog_dict = {}
            geog_dict["sequence_name"] = sequence["sequence_name"]
            geog_dict["id"] = name
            geog_dict["adm2_raw"] = adm2
            geog_dict["outer_postcode"] = outer_postcode
            geog_dict['country'] = country
            
            geog_dict['location'] = ""
            NUTS1 = ""

            adm2 = adm2.replace(" ","_")

            if country in country_list:

                processed_adm1 = do_adm1(adm1)
                geog_dict["adm1"] = processed_adm1
                if processed_adm1 == "":
                    missing_adm1 += 1

                if outer_postcode != "" and outer_postcode not in missing_postcodes:
                    output = do_outer_postcode_region_latlong(geog_dict, outer_postcode, outer_to_latlongs_region)
                    if type(output) != bool:
                        geog_dict = output
                        if outer_postcode not in postcode_to_adm2:
                            if outer_postcode not in done_postcodes:
                                postcodes_with_no_adm2.write(outer_postcode + "\n")
                                done_postcodes.append(outer_postcode)
                    else:
                        geog_dict["region"] = ""
                        geog_dict["latitude"] = ""
                        geog_dict["longitude"] = ""
                        if outer_postcode not in done_postcodes and outer_postcode not in missing_postcodes:
                            new_unclean_postcodes.write(outer_postcode + "\n")
                            done_postcodes.append(outer_postcode)
                else:
                    missing_op += 1

                if adm2 != "" or outer_postcode != "":

                    processed_adm2,source, conflict = process_adm2(outer_postcode, adm2, metadata_multi_loc, straight_map, not_mappable, postcode_to_adm2, processed_adm1, nuts_dict)
                    
                    geog_dict["adm2_source"] = source

                    if type(processed_adm2) != bool and processed_adm2 not in non_uk:
                        
                        geog_dict["adm2"] = processed_adm2

                        if source != "nuts_provided":
                            if "|" in processed_adm2:
                                nuts_adm2 = processed_adm2.split("|")[0]
                            else:
                                nuts_adm2 = processed_adm2

                            for region, lst in nuts_dict.items():
                                if nuts_adm2 in lst:
                                    NUTS1 = region
                        else:
                            NUTS1 = adm2
                            

                        geog_dict["NUTS1"] = NUTS1.title()


                    else:
                        curation += 1
                        geog_dict["adm2"] = "Needs_manual_curation"
                        geog_dict["NUTS1"] = ""
                        if adm2 not in already_found:
                            new_unclean_locations.write(adm2 + "\n")
                            already_found.append(adm2)

                else:
                    processed_adm2 = ""
                    geog_dict["adm2"] = ""
                    missing_adm2 += 1
                    geog_dict["adm2_source"] = ""
                    geog_dict["NUTS1"] = ""



                if type(processed_adm2) != bool and processed_adm2 != "" and geog_dict["location"] == "" and processed_adm2 not in non_uk:
                    if "|" in processed_adm2:
                        if processed_adm2 in nice_names:
                            location = nice_names[processed_adm2]
                        elif NUTS1 != "":
                            location = NUTS1.replace("_"," ").title().replace("Of","of")
                        elif processed_adm1 != "":
                            location = processed_adm1
                    else:
                        
                        location = processed_adm2.title().replace("_"," ").replace("Of","of")

                    geog_dict["location"] = location
                    
                elif geog_dict["location"] == "":
                    if NUTS1 != "":
                        location = NUTS1.replace("_"," ").title().replace("Of","of")
                    elif processed_adm1 != "":
                        location = processed_adm1

                    geog_dict["location"] = location
                    

                if conflict and name not in already_checked_discreps:
                    incompatible_locations.write(f'{sequence["central_sample_id"]},{outer_postcode},{adm2},{postcode_to_adm2[outer_postcode]},{processed_adm2}\n')
                    conflict_count += 1

                utla = ""
                code = ""
                grouping = ""

                if type(processed_adm2) != bool and processed_adm2 != "" and processed_adm2 not in NI_counties and processed_adm2 not in non_uk:
                    if "|" in processed_adm2:
                        utlas = set()
                        bits = processed_adm2.split("|")
                        for i in bits:
                            for j in adm2_to_utla[i]:
                                utlas.add(j)
                        utla = "|".join(utlas)
                    else:
                        utla = "|".join(adm2_to_utla[processed_adm2])

                    if "|" in utla:
                        codes = set()
                        bits = utla.split("|")
                        for i in bits:
                            codes.add(utla_codes[i])
                        code = "|".join(codes)
                    else:
                        code = utla_codes[utla]

                    if "|" in processed_adm2:
                        groupings = set()
                        bits = processed_adm2.split("|")
                        for i in bits:
                            groupings.add(suggested_groupings[i])
                        grouping = "|".join(groupings)
                    else:
                        grouping = suggested_groupings[processed_adm2]

                geog_dict["utla"] = utla 
                geog_dict["utla_code"] = code
                geog_dict["suggested_adm2_grouping"] = grouping
                
                epiweek = sequence[epiweek_col] 
                if processed_adm2 != "" and processed_adm2 != "Needs_manual_curation":
                    if processed_adm2 in adm2_to_week_counts.keys():
                        if epiweek in adm2_to_week_counts[processed_adm2].keys():
                            adm2_to_week_counts[processed_adm2][epiweek] += 1
                        else:
                            adm2_to_week_counts[processed_adm2][epiweek] = 1
                    else:
                        adm2_to_week_counts[processed_adm2] = {}
                        adm2_to_week_counts[processed_adm2][epiweek] = 1
                if grouping != "":
                    if grouping in adm2_to_week_counts.keys():
                        if epiweek in adm2_to_week_counts[grouping].keys():
                            adm2_to_week_counts[grouping][epiweek] += 1
                        else:
                            adm2_to_week_counts[grouping][epiweek] = 1
                    else:
                        adm2_to_week_counts[grouping] = {}
                        adm2_to_week_counts[grouping][epiweek] = 1


                if processed_adm1 in non_uk or processed_adm2 in non_uk:
                    geog_dict,adm2_to_week_counts = deal_with_nonuk_cog(country, processed_adm1, processed_adm2, epiweek, geog_dict, adm2_to_week_counts, safe_locs)


                outer_geog_dict[name] = geog_dict 
                epiweek_dict[name] = epiweek
    
    new_unclean_locations.close()
    incompatible_locations.close()
    postcodes_with_no_adm2.close()

    write_log_file(missing_adm1, missing_adm2, missing_op, curation, conflict_count, log_file)
    log_file.close()
    
    return outer_geog_dict, adm2_to_week_counts, epiweek_dict, non_uk, safe_locs

def make_geography_csv(metadata_file, country_col, outer_postcode_col, adm1_col, adm2_col,epiweek_col, map_utils_dir, outdir):

    with open(os.path.join(outdir,"geography.csv"), 'w') as fw:
        fieldnames = ["sequence_name","id","country", "adm2_raw","adm2","adm2_source","NUTS1","adm1","outer_postcode","region","latitude","longitude", "location", "utla", "utla_code", "suggested_adm2_grouping", "safe_location"]
        writer = csv.DictWriter(fw, fieldnames=fieldnames)
        writer.writeheader()

        outer_geog_dict, adm2_to_week_counts, epiweek_dict, non_uk, safe_locs = process_input(metadata_file, country_col, outer_postcode_col, adm1_col, adm2_col, epiweek_col, map_utils_dir, outdir)

        for name, geog_dict in outer_geog_dict.items():
            epiweek = epiweek_dict[name]
            if geog_dict['adm2'] != "Needs_manual_curation":
                safe_loc = make_safe_loc(adm2_to_week_counts, geog_dict, epiweek, non_uk, safe_locs)
            else:
                safe_loc = ""
            geog_dict["safe_location"] = safe_loc.upper().replace(" ","_")
            writer.writerow(geog_dict)

def write_log_file(missing_adm1, missing_adm2, missing_op, curation, conflict, log_file):

    log_file.write("Log file for geographic data\n\n")

    log_file.write(f'{missing_adm1} sequences are missing adm1 information\n')
    log_file.write(f'{missing_op} sequences are missing outer postcodes\n')

    log_file.write(f'Of these, an additional {missing_adm2} sequences are also missing any other sub-national geographic information, and so cannot be accurately mapped to an adm2 region. \n')
    log_file.write(f'{curation} sequences need additional manual curation to accurately match their adm2 to a real adm2.\n')

    log_file.write(f'{conflict} sequences have incompatible input adm2 and outer postcode.')



def commonly_used_names():

    nice_names = {
        "BIRMINGHAM|COVENTRY|DUDLEY|SANDWELL|SOLIHULL|WALSALL|WOLVERHAMPTON":"West Midlands",
        "DERBY|DERBYSHIRE|LEICESTER|LEICESTERSHIRE|LINCOLNSHIRE|NORTHAMPTONSHIRE|NOTTINGHAM|NOTTINGHAMSHIRE|RUTLAND":"East Midlands",
        "BOLTON|BURY|MANCHESTER|OLDHAM|ROCHDALE|SALFORD|STOCKPORT|TAMESIDE|TRAFFORD|WIGAN":"Greater Manchester",
        "EAST_SUSSEX|WEST_SUSSEX":"Sussex",
        "BRADFORD|CALDERDALE|KIRKLEES|LEEDS|WAKEFIELD":"West Yorkshire",
        "GATESHEAD|NEWCASTLE_UPON_TYNE|NORTH_TYNESIDE|SOUTH_TYNESIDE|SUNDERLAND": "Tyne and Wear",
        "BARNSLEY|DONCASTER|ROTHERHAM|SHEFFIELD": "South Yorkshire",
        "BRACKNELL_FOREST|READING|SLOUGH|WEST_BERKSHIRE|WINDSOR_AND_MAIDENHEAD|WOKINGHAM":"Berkshire",
        'KNOWSLEY|SAINT_HELENS|SEFTON|WIRRAL':"Merseyside",
        "CHESHIRE_EAST|CHESHIRE_WEST_AND_CHESTER":"Cheshire",
        "CORNWALL|ISLES_OF_SCILLY":"Cornwall and Isles of Scilly",
        "DENBIGHSHIRE|CONWY|FLINTSHIRE|WREXHAM":"Clwyd"
    }

    return nice_names


def main():

    parser = argparse.ArgumentParser(description='cleaning_adm2')

    parser.add_argument("--metadata")
    parser.add_argument("--country-col", dest="country_col")
    parser.add_argument("--outer-postcode-col", dest="outer_postcode_col")
    parser.add_argument("--adm2-col", dest="adm2_col")
    parser.add_argument("--adm1-col", dest="adm1_col")
    parser.add_argument("--epiweek-col", dest="epiweek_col")
    parser.add_argument("--mapping-utils-dir", dest="map_utils_dir", help="path to map utils eg outer postcode")
    parser.add_argument("--outdir")


    args = parser.parse_args()

    make_geography_csv(args.metadata, args.country_col, args.outer_postcode_col, args.adm1_col, args.adm2_col, args.epiweek_col, args.map_utils_dir, args.outdir)


if __name__ == '__main__':
    main()
