# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 11:50:17 2023

@author: Thomas Ball
"""

import argparse
import plotly.graph_objects as go
import plotly.io as pio
pio.kaleido.scope.mathjax = None

# pio.renderers.default='browser'

import pandas as pd
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument(
    "--countrycode",
    type=str,
    required=True,
    dest="country",
    help="three letter contry code"
)
args = parser.parse_args()

color_dict = { 'Ruminant meat'          : "#40004b",
            'Pig meat'                  : "#762a83",
            'Poultry meat'              : "#9970ab",
            'Dairy'                     : "#c2a5cf",
            'Eggs'                      : "#e7d4e8",

            'Grains'                    : "#00441b",
            'Roots and tubers'          : "#1b7837",
            'Vegetables'                : "#5aae61",
            'Fruit'                     : "#a6dba0",
            'Legumes, nuts, and seeds'  : "#d9f0d3",

            # 'Sugar'                     : "#68EFF8",
            'Spices'                    : "#00d5c0",
            'Stimulants'                : "#0034D5",
            'Coffee'                : "#2b00d5",
            'Cocoa'                 : "#003cd5",
            "Tea and maté"          : "#0072d5"
            }

group_label_conv = {'Ruminant meat'             : 'Ruminant meat',
                'Pig meat'                  : 'Pig meat',
                'Poultry meat'              : "Poultry",
                'Dairy'                     : "Dairy",
                'Eggs'                      : "Eggs",

                'Grains'                    : "Grains",
                'Roots and tubers'          : "Roots/tubers",
                'Vegetables'                : "Vegetables",
                'Fruit'                     : "Fruits",
                'Legumes, nuts, and seeds'  : "Pulses/nuts",

                # 'Sugar'                     : "Sugar",
                'Spices'                    : "Spices",
                'Stimulants'                : "Stimulants",
                "Coffee"                    : "Coffee",
                "Cocoa"                     : "Cocoa",
                "Tea and maté"              : "Tea and maté"
            }

reg_cutoff = 25
val_cutoff = 0.005
alpha = 0.7

# load data
basePath = os.path.join("all_results", args.country.lower())
datPath = "model/dat"
coi = args.country.upper()


def get_region(ccodes, iso3):
    reg = cCodes[cCodes["alpha-3"] == iso3]["sub-region"].to_list()[0]
    ireg = cCodes[cCodes["alpha-3"] == iso3]["intermediate-region"].to_list()[0]
    if type(ireg) == str:
        reg = ireg
    return reg

def hex_to_rgb_add_alph(hex, alpha):
    rgb = []
    for i in (0, 2, 4):
        decimal = int(hex.strip("#")[i:i+2], 16)
        rgb.append(decimal)
    rgb.append(alpha)
    return f"rgba{tuple(rgb)}"

cCodes = pd.read_csv(os.path.join(datPath, "country_codes.csv"))
xdf = pd.read_csv(os.path.join(basePath,"xdf.csv"), index_col=0)
xdf = xdf[xdf.bd_opp_cost_calc > xdf.bd_opp_cost_calc.max() * val_cutoff]
xdf["Region"] = [get_region(cCodes, country) for country in xdf.Country_ISO]
df_uk = pd.read_csv(os.path.join(basePath,"df_domestic.csv"), index_col=0)
df_os = pd.read_csv(os.path.join(basePath,"df_offshore.csv"), index_col=0)
kdf = pd.concat([df_uk,df_os])
kdf = kdf.groupby([kdf.index, "Group"]).sum().reset_index()
# kdf.loc[kdf.Group == "Sugar", "bd_opp_food"] = kdf.loc[kdf.Group == "Sugar", "bd_opp_total"]
kdf.columns =["Item"] + kdf.columns.to_list()[1:]
sum_bd = xdf.groupby(["Country_ISO", "Producer_Country_Code"]).sum().sort_values("bd_opp_cost_calc", ascending = False).reset_index()
sum_bdr = xdf.groupby(["Region"]).sum().sort_values("bd_opp_cost_calc", ascending = False).reset_index()



groups = [group for group in color_dict.keys() if group in kdf.Group.unique()]


areas = [coi] + [x for x in sum_bd.Country_ISO[:reg_cutoff].to_list() if x != coi] + ["Other"]
regions = [coi] + [x for x in sum_bdr.Region[:reg_cutoff].to_list() if x != coi] + ["Other"]

# list of source nodes
source = []

# list of target nodes (corresponding to sources)
target = []

# value contains a list of values for each connection (i.e. the connection width)
value = []

# colors contains a list of colours for each connection
colors = []

# label contains a list of node labels once each - for some reason in reverse
# order of appearance on the graph (i.e. bottom right to top left vertically)
label = []


foodgroups = groups
# foodgroups = ["Fruit"]
# foodgroups = kdf[kdf.Group == "Fruit"].Item.unique()

spatial = regions
spatial= areas
# spatial_col = "Region"
spatial_col = "Country_ISO"
level2 = ["Feed", "Food", "Pasture"]


spatial_idx = {spatial[x] : x for x in range(len(spatial))}
foodgroups_idx = {foodgroups[x] : x + list(spatial_idx.values())[-1]+1 for x in range(len(foodgroups))}

lvl2_idx = {level2[x] : x + list(foodgroups_idx.values())[-1]+1 for x in range(len(level2))}

df = pd.DataFrame(columns = ["source","value","target"])

iterv = 0
for a, area in enumerate(spatial_idx):
    label.append(area)

    for g, group in enumerate(foodgroups_idx):
        target.append(spatial_idx[area])
        source.append(foodgroups_idx[group])
        colors.append(color_dict[group])

        # if area != "Other":
        #     adf = xdf[(xdf.ItemT_Name.isin(kdf[kdf.Group == group].Item)&(xdf[spatial_col] == area))]
        # elif area == "Other":
        #     adf = xdf[xdf.ItemT_Name.isin(kdf[kdf.Group == group].Item)&(~(xdf[spatial_col].isin(areas)))]

        if area != "Other":
            adf = xdf[(xdf.ItemT_Name.isin(kdf[kdf.Group == group].Item)&(xdf[spatial_col] == area))]
        elif area == "Other":
            adf = xdf[xdf.ItemT_Name.isin(kdf[kdf.Group == group].Item)&(~(xdf[spatial_col].isin(spatial)))]

        val = adf.bd_opp_cost_calc.sum()
        value.append(val)

        df.loc[iterv, :] = [group, val, area]

        iterv += 1

# target.append(spatial_idx["South America"])
# source.append(foodgroups_idx["Sugar"])
# colors.append(color_dict["Sugar"])
# value.append(df_os.bd_opp_total.Sugar)

# target.append(spatial_idx["Northern Europe"])
# source.append(foodgroups_idx["Sugar"])
# colors.append(color_dict["Sugar"])
# value.append(df_uk.bd_opp_total.Sugar)

# target.append(spatial_idx["Other"])
# source.append(foodgroups_idex["Sugar"])
# colors.append(color_dict["Sugar"])
# value.append(df_os.bd_opp_total.Sugar)

# target.append(spatial_idx[coi])
# source.append(foodgroups_idex["Sugar"])
# colors.append(color_dict["Sugar"])
# value.append(df_uk.bd_opp_total.Sugar)


label = label + [group_label_conv[group] for group in foodgroups]
# Process colours
colors = [hex_to_rgb_add_alph(hex, alpha) for hex in colors]
link = dict(source=source, target=target, value=value, color=colors)
ncolors = ["grey" if g not in groups else color_dict[g] for g in label]

node_x = [0.001 if g in groups else 0.999 for g in label]

# group_sums = [xdf[xdf.ItemT_Name.isin(kdf[kdf.Group == group].Item)].bd_opp_cost_calc.sum() for group in groups]

node = dict(label = label, thickness=15, color = ncolors, x= node_x)

data = go.Sankey(link=link, node=node)
fig = go.Figure(data)

fig.update_layout(
    hovermode='x',
    font=dict(size=20, color='black'),
    paper_bgcolor='white'

)

# fig.show()
fig.write_image(os.path.join(basePath, "sankey.pdf"))

with open(os.path.join(basePath, "sankey_txt.txt"), "w+") as f:


    for row in df.iterrows():
        rowdat = row[1]
        s = rowdat.source
        val = rowdat.value
        t = rowdat.target
        f.write(f"{s} [{val}] {t}")
        f.write("\n")

    f.close()





