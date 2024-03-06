import argparse
import model._consumption_provenance
import model._get_impacts
import pandas as pd
import os
import sys

countries = pd.read_excel("/maps/mwd24/food_v0/model/dat/nocsDataExport_20220822-151738.xlsx")

parser = argparse.ArgumentParser() 
parser.add_argument(
    "--countrycode",
    type=str,
    required=True,
    dest="country",
    help="three letter contry code"
)
args = parser.parse_args()

country_data = countries[countries.ISO3==args.country]
if len(country_data) == 0:
    print(f"Failed to lookup county code {args.country}", file=sys.stderr)
    sys.exit(1)
elif len(country_data) > 1:
    print(f"Got multiple results for {args.country_code}", file=sys.stderr)
    sys.exit(1)

scenPath = os.path.join("/maps/mwd24/food_v0/all_results/", args.country.lower())
os.makedirs(scenPath, exist_ok=True)

datPath = "/maps/mwd24/food_v0/model/"
coi = country_data['LIST NAME'].iloc[0]

years = [2017,2018,2019,2020,2021]

sua = pd.read_csv(os.path.join(datPath, "dat",
                    "SUA_Crops_Livestock_E_All_Data_(Normalized).csv"),
                    encoding = "latin-1", engine="python")
fs = sua[(sua.Area==coi)&(sua["Element Code"]==5141)&(sua.Year.isin(years))]

# run consumption / prov
model._consumption_provenance.main(fs, coi, scenPath, datPath)

# run impact calcs
fprov = pd.read_csv(os.path.join(scenPath, "feed.csv"), index_col = 0)
feedimp = model._get_impacts.get_impacts(fprov, 2019, coi, scenPath, datPath)
feedimp.to_csv(os.path.join(scenPath, "feed_impacts_wErr.csv"))
hprov = pd.read_csv(os.path.join(scenPath, "human_consumed.csv"), index_col = 0)
foodimp = model._get_impacts.get_impacts(hprov, 2019, coi, scenPath, datPath)
foodimp.to_csv(os.path.join(scenPath, "human_consumed_impacts_wErr.csv"))
