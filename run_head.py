import model._consumption_provenance
import model._get_impacts
import pandas as pd
import os

scenPath = "/maps/tsb42/food_v0/results/bra"
datPath = "/maps/tsb42/food_v0/model/"
coi = "Brazil"

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