import argparse
import os

import pandas as pd
import matplotlib.pyplot as plt

colours_stim = { 'Ruminant meat'             : "#40004b",
				'Pig meat'                  : "#762a83",
				'Poultry meat'              : "#9970ab",
				'Dairy'                     : "#c2a5cf",
				'Eggs'                      : "#e7d4e8",

				'Grains'                    : "#00441b",
				'Roots and tubers'          : "#1b7837",
				'Vegetables'                : "#5aae61",
				'Fruit'                     : "#a6dba0",
				'Legumes, nuts, and seeds'  : "#d9f0d3",

				'Sugar crops'                     : "#68EFF8",
				'Stimulants'                : "red",
				'Spices'                    : "#00C8D5",
				'Coffee'                : "#2b00d5",
				'Cocoa'                 : "#003cd5",
				"Tea and maté"          : "#0072d5",
				"Other" : "grey"
				}


groups = colours_stim.keys()

parser = argparse.ArgumentParser()
parser.add_argument(
	"--countrycode",
	type=str,
	required=True,
	dest="country",
	help="three letter contry code"
)
args = parser.parse_args()

bpath = os.path.join("results", args.country.lower())
savepath = bpath
datPath = "model"


cropdb = pd.read_csv(os.path.join(datPath, "crop_db.csv"))

kdf = pd.read_csv(os.path.join(bpath, "kdf.csv"), index_col = 0)
kdf["bd_per_kg"] = kdf["bd_opp_total"] / kdf["Cons"]

totals_per_group = kdf.groupby("Group").sum()

fig, ax = plt.subplots()

groups = totals_per_group.index.to_list()
group_colours = [colours_stim[x] for x in groups]

ax.barh(
	totals_per_group.index.to_list(),
	totals_per_group["bd_per_kg"].to_list(),
	# xerr=totals_per_group["bd_opp_total_err"].to_list(),
	color=group_colours
)

ax.set_xlabel('per KG impact')
ax.set_title(args.country)

figsize = (8,6)

fig.set_size_inches(figsize)
fig.tight_layout()
fig.savefig(os.path.join(savepath, "ghg_totals.png"), dpi = 500)


# bf = pd.read_csv(os.path.join(bpath, "feed_impacts_wErr.csv"), index_col = 0)
# bf = bf.merge(cropdb, on="Item_Code")
# print(bf)
