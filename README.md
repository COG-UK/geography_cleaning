## Geography cleaning

This is the repo for the geography cleaning scripts and utilities used in phylopipe/datapipe runs for COG-UK. 

Author: Verity Hill at the University of Edinburgh.

It takes the submitted sequence metadata as an input, and attempts to find the highest resolution geographical data available.

The adm2s are cleaned to match those found in the Global Administrative Database (gadm.org) database.

In all cases, pipes ("|") are used to denote ambiguity. 
Correct adm2s with pipes (i.e. if the ambiguity is known on submission) in between locations will be be accepted as inputs. 

This script will also accept valid NUTS1 regions as inputs. These are defined at the bottom of the page, along with their constituent adm2s.


### Columns in output:
- Sequence_name
- ID
- Country: will be mostly UK, but now this script accepts crown dependencies/overseas territories which have their own country designations
- adm2_raw: the inputted adm2, unedited
- adm2: processed adm2, corrected for spelling mistakes and matched to the GADM adm2s. See below for explanation.
- adm2_source: options are "outer_postcode", "adm2_raw", "cleaned_adm2_raw", "postcode_conflict_resolution". See below for explanation.
- NUTS: Nomenclature of Territorial Units for Statistics (NUTS1), a larger standardised grouping, see https://en.wikipedia.org/wiki/NUTS_statistical_regions_of_the_United_Kingdom for more information
- adm1: Scotland, England, Wales or Northern Ireland
- outer_postcode: Inputted first section of postcode, spelling mistakes cleaned where possible. Corresponds to postcode district.
- region: The postcode region (the letters at the start of the postcode)
- latitude: centroids of the postcode districts
- longitude: centroids of the postcode districts
- location: A human readable version of the processed adm2s, mostly for use in trees in civet reports. If adm2 isn't available, the location is the highest level of geographical data available. See below.
- utla: Upper Tier Local Authority. Similar to adm2, often used with reporting epidemiological data. Multiple adm2s may map to the same UTLA and vice versa.
- utla_code: ONS-defined code for UTLAs.
- suggested_adm2_grouping: Designation that may be more sensible for some geographical analyses. See below.
- safe_location: location to de-identify sequence if the data is very sparse, see algorithm below.


### Adm2 processing:

There are multiple ways that the final adm2 designation is achieved, and this is denoted in the "source" column:

- outer_postcode: simply matches the postcode to the appropriate adm2 or adm2s. It is worth noting that postcodes and adm2s are non-overlapping systems of splitting up the UK, and so sequences with this source may have highly ambiguous adm2s.
- adm2_raw: inputted adm2 is valid, spelt correctly, and can't be made more specific by the outer postcode.
- cleaned_adm2_raw: adm2 that isn't valid but has been seen before and so is accounted for in cleaning. This may be because the input is spelt wrong, or that it isn't an adm2. For example, Kings Heath isn't an adm2, but it's in Birmingham so this can be mapped to a true adm2.
- postcode_conflict_resolution: If the postcode and the cleaned input adm2 are incompatible, the adm2 from the postcode is chosen.
- any of the above plus country: if the adm2 is ambiguous across adm1 borders, only those in the inputted adm1 are taken forwards. This is mostly applicable with postcodes on the english/welsh border.

### Location:

This is designed to be as useful as possible for humans. The adm2 processing often results in long, and ambiguous strings, joined by pipe symbols which, while important for any analysis or mapping, can be tricky for people to interprete quickly.

There are a few different ways the location field is used:

It will show the highest resolution (up to adm2) data available going from adm1-->NUTS1-->adm2

Or it may show a grouping of adm2s that is commonly used more than the adm2s themselves, avoiding long and ambiguous adm2 strings. These groupings can be found at the bottom of this page.

### Suggested adm2 groupings:

This is a field based on experience of running geographical analyses using the genome data in the UK. It is designed to try and keep all of the geographical genome data as accurate as possible.
It is a combination of two things:
 - The grouping together locations that are commonly grouped (and are submitted in those groupings), and uses the same groupings as "location", which can be found at the bottom of this page
 - The merging of locations that are only very rarely given as the inputted value of adm2s. This is usually cities such as Leicester, Derby, Nottingham etc that are their own adm2s, but are hardly ever seen in inputted adm2s.
 This was determined by looking at the sequences where both postcode and adm2 were provided, but conflicted with each other - i.e. it allowed us to see which adm2s were commonly being mistaken for another one. 
 This is most useful for sequences where the only geographical data we have is the adm2, as we cannot be sure that a sequence that says (for eg) "Leicestershire" could actually be from Leicester. 
 Therefore to avoid artificially low sequencing numbers for areas that would only have sequences with postcode data placed in them, it is best to group the locations together and treat all sequences from Leicestershire and Leicester as being from the same place.

The file that defines this is "adm2_aggregation.csv" in the "geography_utils" folder. 

### Safe location:

While adm2-level data usually isn't viewed as identifying, if data is sparse, it may be. If there are fewer than 5 sequences in an epiweek in the sequence's adm2, then the aggregated adm2 is checked. If there are still less than five sequences in this grouping, then the NUTS1 region is given. If the adm2 or grouping is ambiguous one (ie it has a "|"), then the counts are combined. Eg if the adm2 is "EAST_SUSSEX|WEST_SUSSEX", then there must be five sequences between the two locations or the aggregated adm2 will be provided.

### Files in geography_utilities folder:

- LAD_UTLA_adm2.csv: made by Chris Ruis at the University of Cambridge, contains the adm2 to utla mapping. Also contains Local Authority Areas.
- adm2_cleaning.tsv: known mistakes made when inputting adm2s. First column is the location provided in the unclean metadata. If there's only one other column, it is a 1:1 mapping to a GADM adm2 (eg Borders to Scottish_borders). If there are multiple other columns, then the adm2 supplied consists of multiple GADM adm2s.
- nuts_to_adm2.tsv: definition of the NUTS1 regions in terms of adm2.
- outer_postcode_cleaning.csv: known errors in input postcodes. Usually spelling mistakes and mis-transcription.
- outer_postcode_latlongs_region.csv: lookup table for postcode district to region and centroid. Those without latitudes and longitudes are non-geographic postcodes
- postcode_to_adm2: Lookup table to match outer postcodes to one or more GADM adm2s, ambiguities denoted by "|".


### Groupings:

- BIRMINGHAM|COVENTRY|DUDLEY|SANDWELL|SOLIHULL|WALSALL|WOLVERHAMPTON: West Midlands
- DERBY|DERBYSHIRE|LEICESTER|LEICESTERSHIRE|LINCOLNSHIRE|NORTHAMPTONSHIRE|NOTTINGHAM|NOTTINGHAMSHIRE|RUTLAND: East Midlands
- BOLTON|BURY|MANCHESTER|OLDHAM|ROCHDALE|SALFORD|STOCKPORT|TAMESIDE|TRAFFORD|WIGAN: Greater Manchester
- EAST_SUSSEX|WEST_SUSSEX: Sussex
- BRADFORD|CALDERDALE|KIRKLEES|LEEDS|WAKEFIELD: West Yorkshire
- GATESHEAD|NEWCASTLE_UPON_TYNE|NORTH_TYNESIDE|SOUTH_TYNESIDE|SUNDERLAND: Tyne and Wear
- BARNSLEY|DONCASTER|ROTHERHAM|SHEFFIELD: South Yorkshire
- BRACKNELL_FOREST|READING|SLOUGH|WEST_BERKSHIRE|WINDSOR_AND_MAIDENHEAD|WOKINGHAM: Berkshire
- KNOWSLEY|SAINT_HELENS|SEFTON|WIRRAL: Merseyside
- CHESHIRE_EAST|CHESHIRE_WEST_AND_CHESTER: Cheshire
- CORNWALL|ISLES_OF_SCILLY: Cornwall and Isles of Scilly
- DENBIGHSHIRE|CONWY|FLINTSHIRE|WREXHAM: Clwyd

NUTS1 regions:
- EAST_MIDLANDS:	DERBY	DERBYSHIRE	NOTTINGHAMSHIRE	NOTTINGHAM	LEICESTERSHIRE	LEICESTER	RUTLAND	NORTHAMPTONSHIRE	LINCOLNSHIRE	SWADLINCOTE
- EAST_OF_ENGLAND:	EAST_ANGLIA	CENTRAL_BEDFORDSHIRE	HERTFORDSHIRE	ESSEX	NORFOLK	SUFFOLK	CAMBRIDGESHIRE	HOCKLEY	LUTON	PETERBOROUGH	SOUTHEND-ON-SEA	THURROCK																																												
- GREATER_LONDON:	GREATER_LONDON																																																			
- NORTH_EAST:	NORTHUMBERLAND	TYNE_AND_WEAR	DURHAM	DARLINGTON	GATESHEAD	HARTLEPOOL	MIDDLESBROUGH	NEWCASTLE_UPON_TYNE	NORTH_TYNESIDE	REDCAR_AND_CLEVELAND	SOUTH_TYNESIDE	STOCKTON-ON-TEES	SUNDERLAND																																											
- NORTH_WEST:	CHESHIRE_EAST	CHESHIRE_WEST_AND_CHESTER	CUMBRIA	MANCHESTER	BOLTON	WIGAN	STOCKPORT	TAMESIDE	BURY	OLDHAM	ROCHDALE	SALFORD	TRAFFORD	LANCASHIRE	HALTON	SAINT_HELENS	KNOWSLEY	BLACKBURN_WITH_DARWEN	BLACKPOOL	SEFTON	WARRINGTON	WIRRAL																																													
- SOUTH_EAST:	WEST_BERKSHIRE	READING	WOKINGHAM	BRACKNELL_FOREST	WINDSOR_AND_MAIDENHEAD	SLOUGH	BERKSHIRE	BUCKINGHAMSHIRE	MILTON_KEYNES	EAST_SUSSEX	WEST_SUSSEX	SUSSEX	BRIGHTON_AND_HOVE	HAMPSHIRE	SOUTHAMPTON	PORTSMOUTH	ISLE_OF_WIGHT	KENT	MEDWAY	OXFORDSHIRE	SURREY																																		
- SOUTH_WEST:	BATH_AND_NORTH_EAST_SOMERSET	SOMERSET	NORTH_SOMERSET	BRISTOL	GLOUCESTERSHIRE	SOUTH_GLOUCESTERSHIRE	WILTSHIRE	DORSET	DEVON	CORNWALL	PLYMOUTH	BOURNEMOUTH	ISLES_OF_SCILLY	POOLE	SWINDON																																												
- WEST_MIDLANDS:	BIRMINGHAM	COVENTRY	DUDLEY	SANDWELL	HEREFORDSHIRE	SOLIHULL	SHROPSHIRE	STAFFORDSHIRE	STOKE-ON-TRENT	TELFORD_AND_WREKIN	WALSALL	WARWICKSHIRE	WOLVERHAMPTON	WORCESTERSHIRE
- YORKSHIRE_AND_THE_HUMBER:	BARNSLEY	EAST_RIDING_OF_YORKSHIRE	NORTH_LINCOLNSHIRE	NORTH_YORKSHIRE	LEEDS	BRADFORD	CALDERDALE	KIRKLEES	DONCASTER	KINGSTON_UPON_HULL	ROTHERHAM	SHEFFIELD	WAKEFIELD	YORK																																								
- SCOTLAND:	ABERDEEN	ABERDEENSHIRE	ANGUS	ARGYLL_AND_BUTE	CLACKMANNANSHIRE	DUMFRIES_AND_GALLOWAY	DUNDEE	EAST_AYRSHIRE	EAST_DUNBARTONSHIRE	EAST_LOTHIAN	EAST_RENFREWSHIRE	EDINBURGH	EILEAN_SIAR	FALKIRK	FIFE	GLASGOW	HIGHLAND	INVERCLYDE	MIDLOTHIAN	MORAY	NORTH_AYRSHIRE	NORTH_LANARKSHIRE	ORKNEY_ISLANDS	PERTHSHIRE_AND_KINROSS	RENFREWSHIRE	SCOTTISH_BORDERS	SHETLAND_ISLANDS	SOUTH_AYRSHIRE	SOUTH_LANARKSHIRE	STIRLING	WEST_DUNBARTONSHIRE	WEST_LOTHIAN																								
- WALES:	ANGLESEY	BLAENAU_GWENT	BRIDGEND	CAERPHILLY	CARDIFF	CARMARTHENSHIRE	CEREDIGION	CONWY	DENBIGHSHIRE	FLINTSHIRE	GWYNEDD	MERTHYR_TYDFIL	MONMOUTHSHIRE	NEATH_PORT_TALBOT	NEWPORT	PEMBROKESHIRE	POWYS	RHONDDA_CYNON_TAFF	SWANSEA	TORFAEN	VALE_OF_GLAMORGAN	WREXHAM																																		
- NORTHERN_IRELAND:	ANTRIM_AND_NEWTOWNABBEY	ARMAGH_BANBRIDGE_AND_CRAIGAVON	BELFAST	CAUSEWAY_COAST_AND_GLENS	DERRY_AND_STRABANE	FERMANAGH_AND_OMAGH	LISBURN_AND_CASTLEREAGH	MID_AND_EAST_ANTRIM	MID_ULSTER	NEWRY_MOURNE_AND_DOWN	NORTH_DOWN_AND_ARDS	TYRONE	ANTRIM	ARMAGH	FERMANAGH	LONDONDERRY	DOWN			
- CHANNEL_ISLANDS:	GUERNSEY	JERSEY																																		


