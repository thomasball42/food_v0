
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 11:13:54 2023

@author: tom
"""

import argparse
import pandas as pd
import numpy as np
import os
import random
import matplotlib.pyplot as plt
from matplotlib import colormaps

parser = argparse.ArgumentParser()
parser.add_argument(
    "--countrycode",
    type=str,
    required=True,
    dest="country",
    help="three letter contry code"
)
args = parser.parse_args()

# savepath = "C:\\Users\\Thomas Ball\\OneDrive - University of Cambridge\\Work\\stack_paper\\figs\\v3"
savepath = "./sav"
datPath = "model"
spath = "dat"
bpath = os.path.join("all_results", args.country.lower())
savepath = bpath

grouping = "group_name_v3"

cmap = colormaps["viridis"]
coi = 229

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

                # 'Sugar'                     : "#68EFF8",
                'Spices'                    : "#00C8D5",
                'Coffee'                : "#2b00d5",
                'Cocoa'                 : "#003cd5",
                "Tea and maté"          : "#0072d5"
                }

group_label_conv = {'Ruminant meat'     : 'Ruminant meat',
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

anim_prods = list(colours_stim.keys())[:5]
groups = colours_stim.keys()

#%%

cropdb = pd.read_csv(os.path.join(datPath, "crop_db.csv"))
bd_opp_cost = pd.read_csv(os.path.join(datPath, "dat",
                                       "country_opp_cost_v2.csv"),
                                       index_col = 0)

bh = pd.read_csv(os.path.join(bpath, "human_consumed_impacts_wErr.csv"), index_col = 0)
bf = pd.read_csv(os.path.join(bpath, "feed_impacts_wErr.csv"), index_col = 0)

#%%
bf["bd_opp_cost_calc"] = bf["bd_opp_cost_calc"].mask(bf["bd_opp_cost_calc"].lt(0),0)

bh = bh[np.logical_not(np.isinf(bh.FAO_land_calc_m2))]
bh.loc[:, "ItemT_Code"] = bh.loc[:, "Item_Code"]
bh.loc[:, "ItemT_Name"] = bh.loc[:, "Item"]
bh.loc[:, "Arable_m2"] = bh.FAO_land_calc_m2
bh.loc[:, "Pasture_m2"] = bh.Pasture_avg_calc.fillna(0)
bh["bd_perc_err"] = bh["bd_opp_cost_calc_err"] / bh["bd_opp_cost_calc"]

bf = bf[np.logical_not(np.isinf(bf.FAO_land_calc_m2))]
bf.loc[:, "ItemT_Code"] = bf.loc[:, "Animal_Product_Code"]
bf.loc[:, "ItemT_Name"] = bf.loc[:, "Animal_Product"]
bf.loc[:, "Arable_m2"] = bf.FAO_land_calc_m2
bf.loc[:, "Pasture_m2"] = 0
bf["bd_perc_err"] = bf["bd_opp_cost_calc_err"] / bf["bd_opp_cost_calc"]
bf = bf[~np.isinf(bf.bd_perc_err)]
xdf = pd.concat([bh,bf])



xdfs_uk = xdf[xdf.Producer_Country_Code == coi].groupby("ItemT_Name").sum()
xdfs_os = xdf[~(xdf.Producer_Country_Code == coi)].groupby("ItemT_Name").sum()

df_uk = pd.DataFrame()

for item in xdfs_uk.index.tolist():
    x = xdfs_uk.loc[item]
    try:
        df_uk.loc[item, "Group"] = cropdb[cropdb.Item == item][grouping].values[0]
        df_uk.loc[item, "Pasture_m2"] = x.Pasture_m2
        df_uk.loc[item, "Arable_m2"] = x.Arable_m2
        df_uk.loc[item, "Scarcity_weighted_water_l"] = x.SWWU_avg_calc.sum()
        df_uk.loc[item, "ghg_food"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].GHG_avg_calc.sum()
        df_uk.loc[item, "ghg_feed"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code == coi)].GHG_avg_calc.sum()
        df_uk.loc[item, "ghg_total"] =  df_uk.loc[item, "ghg_feed"] + df_uk.loc[item, "ghg_food"]
        df_uk.loc[item, "bd_opp_food"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)]["bd_opp_cost_calc"].sum()
        df_uk.loc[item, "bd_opp_feed"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code == coi)]["bd_opp_cost_calc"].sum()
        df_uk.loc[item, "bd_opp_total"] = df_uk.loc[item, "bd_opp_feed"] + df_uk.loc[item, "bd_opp_food"]

        # bd opp food err
        df_uk.loc[item, "bd_opp_food_err"] = df_uk.loc[item, "bd_opp_food"] \
            * np.sqrt(np.nansum(np.array(bh[(bh.Item==item)&(bh.Producer_Country_Code==coi)].bd_perc_err) ** 2))
        # bd opp feed err
        df_uk.loc[item, "bd_opp_feed_err"] = df_uk.loc[item, "bd_opp_feed"] \
            * np.sqrt(
                np.nansum(np.array(bf[(bf.Animal_Product==item)&(bf.Producer_Country_Code==coi)].bd_perc_err) ** 2)
                )
        # bd opp total error
        fe_err = df_uk.loc[item, "bd_opp_feed_err"]/df_uk.loc[item, "bd_opp_feed"]
        fo_err = df_uk.loc[item, "bd_opp_food_err"]/df_uk.loc[item, "bd_opp_food"]

        df_uk.loc[item, "bd_opp_total_err"] = df_uk.loc[item, "bd_opp_total"] \
            * np.sqrt(np.nansum(np.nansum([(fe_err)**2,(fo_err)**2])))



        df_uk.loc[item, "Cons"] = bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].provenance.sum()
        df_uk.loc[item, "Cons_err"] = np.sqrt(np.nansum(bh[(bh.Item == item)&(bh.Producer_Country_Code == coi)].provenance_err ** 2))

    except IndexError:
        print(f"Couldn't find {item} in the db")

# df_uk.columns = [col + "_uk" for col in df_uk.columns.to_list()]

df_os = pd.DataFrame()
for item in xdfs_os.index.tolist():
    x = xdfs_os.loc[item]
    try:
        df_os.loc[item, "Group"] = cropdb[cropdb.Item == item][grouping].values[0]
        df_os.loc[item, "Pasture_m2"] = x.Pasture_m2
        df_os.loc[item, "Arable_m2"] = x.Arable_m2
        df_os.loc[item, "Scarcity_weighted_water_l"] = x.SWWU_avg_calc.sum()
        df_os.loc[item, "ghg_food"] = bh[(bh.Item == item)&(bh.Producer_Country_Code != coi)].GHG_avg_calc.sum()
        df_os.loc[item, "ghg_feed"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code != coi)].GHG_avg_calc.sum()
        df_os.loc[item, "ghg_total"] =  df_os.loc[item, "ghg_feed"] + df_os.loc[item, "ghg_food"]
        df_os.loc[item, "bd_opp_food"] = bh[(bh.Item == item)&(bh.Producer_Country_Code != coi)]["bd_opp_cost_calc"].sum()
        df_os.loc[item, "bd_opp_feed"] = bf[(bf.Animal_Product == item)&(bf.Producer_Country_Code != coi)]["bd_opp_cost_calc"].sum()
        df_os.loc[item, "bd_opp_total"] = df_os.loc[item, "bd_opp_feed"] + df_os.loc[item, "bd_opp_food"]
        # if item not in df_uk.index:
        df_os.loc[item, "Cons"] = bh[(bh.Item == item)&(bh.Producer_Country_Code !=coi)].provenance.sum()
        df_os.loc[item, "Cons_err"] = np.sqrt(np.nansum(bh[(bh.Item == item)&(bh.Producer_Country_Code !=coi)].provenance_err ** 2))

        # bd opp food err
        df_os.loc[item, "bd_opp_food_err"] = df_os.loc[item, "bd_opp_food"] \
            * np.sqrt(np.nansum(np.array(bh[(bh.Item==item)&(bh.Producer_Country_Code!=coi)].bd_perc_err) ** 2))
        # bd opp feed err
        df_os.loc[item, "bd_opp_feed_err"] = df_os.loc[item, "bd_opp_feed"] \
            * np.sqrt(
                np.nansum(np.array(bf[(bf.Animal_Product==item)&(bf.Producer_Country_Code!=coi)].bd_perc_err) ** 2)
                )
        # bd opp total error
        fe_err = df_os.loc[item, "bd_opp_feed_err"]/df_os.loc[item, "bd_opp_feed"]
        fo_err = df_os.loc[item, "bd_opp_food_err"]/df_os.loc[item, "bd_opp_food"]

        df_os.loc[item, "bd_opp_total_err"] = df_os.loc[item, "bd_opp_total"] \
            * np.sqrt(np.nansum(np.nansum([(fe_err)**2,(fo_err)**2])))

    except IndexError:
        print(f"Couldn't find {item} in the db")

# df_os.columns = [col + "_os" for col in df_os.columns.to_list()]

#%%
# fbs = pd.read_csv(os.path.join(spath, "FAOSTAT_data_en_7-4-2023.csv"))
# diets = pd.read_csv(os.path.join(spath, "comm_replacement","diets3.csv"), index_col = 0)
# diets_list = diets.columns


# #%%sugar
# sug = pd.read_csv(os.path.join(spath, "FAOSTAT_data_en_SUGAR.csv"))
# sug_y = pd.read_csv(os.path.join(spath, "FAOSTAT_data_en_SUGAR_yield.csv"))
# sug_p = pd.read_csv(os.path.join(spath, "FAOSTAT_data_en_SUGAR_production.csv"))

# sugarprov = fbs[fbs.Item == "Sugar (Raw Equivalent)"].Value
# # uks = 906 / (906 + 969)
# # oss = 969 / (906 + 969)
# uks = 0.75
# oss = 0.25

# uk_sug_y = sug_y[
#     sug_y.Area == "United Kingdom of Great Britain and Northern Ireland"
#     ].Value.values[0] * 100 # g / ha
#
# sub_ratio = (sugarprov * uks / sug[(sug.Item == "Sugar beet")&(
#     sug.Element == "Processing")].Value.values).values[0]
# sub = bd_opp_cost["sub"] # per km2
# subval = sug[(sug.Item == "Sugar beet")&(
#     sug.Element == "Processing")].Value.values[
#         0] * uks * 1000000 * 1000 # g sugarbeet from UK
# subval = subval / uk_sug_y # hectares UK
# df_uk.loc["Sugar", "bd_opp_total"] = subval * sub.GBR
# df_uk.loc["Sugar", "bd_opp_total_err"] = df_uk.loc["Sugar", "bd_opp_total"] * 0.2
# wwf_sug_ghg_avg = 1.4
# df_uk.loc["Sugar", "ghg_total"] = subval * wwf_sug_ghg_avg
# wwf_sug_water_avg = 4.6
# df_uk.loc["Sugar", "Scarcity_weighted_water_l"] = subval * wwf_sug_water_avg
# df_uk.loc["Sugar", "Group"] = "Sugar"
#
# subval = sug[(sug.Item == "Sugar beet")&(
#     sug.Element == "Processing")].Value.values[
#         0] * oss * 1000000 * 100
# arable_avg = 1.4 * 1000 * 1000000 * (1/100)
# subval = subval / arable_avg
# df_os.loc["Sugar", "bd_opp_total"] = subval * bd_opp_cost["suc"].median()
# wwf_sugb_ghg_avg = 2.8
# df_os.loc["Sugar", "ghg_total"] = subval * wwf_sugb_ghg_avg
# wwf_sugb_water_avg = 4.6
# df_os.loc["Sugar", "Scarcity_weighted_water_l"] = subval * wwf_sugb_water_avg
# df_os.loc["Sugar", "Group"] = "Sugar"
# df_os.loc["Sugar", "bd_opp_total_err"] = df_os.loc["Sugar", "bd_opp_total"] * 0.2


kdf = pd.concat([df_uk,df_os])
kdf = kdf.groupby([kdf.index, "Group"]).sum().reset_index()
# kdf.loc[kdf.Group == "Sugar", "bd_opp_food"] = kdf.loc[kdf.Group == "Sugar", "bd_opp_total"]
kdf.columns =["Item"] + kdf.columns.to_list()[1:]


impact = "bd_opp_total"
num = 50
sorts = xdf.sort_values("bd_opp_cost_calc", ascending = False)

ukpop = 67000000
days = 365
alpha = 0.7
bbx = (1.0, 1.0)
fontsize_leg = 13.5
leg_offset = 0
fontsize = 10
figsize = (8,6)
dpi = 800
bar_width = 0.4
dfsize = 40
font = {"fontsize":fontsize,
        "fontname":"Helvetica",
        }

domestic = df_uk.groupby("Group").sum()
offshore = df_os.groupby("Group").sum()
textalph = 0.15
fig, axs = plt.subplots(nrows=1,ncols=2, sharey=True)
ax = axs[0]

oval = []
ovalerr = []
ogroup = []
drat = []

for g, group in enumerate(groups):
    try:
        cons = domestic.loc[group]["Cons"]
        cons_err = domestic.loc[group]["Cons_err"]
    except KeyError:
        try:
            cons = offshore.loc[group]["Cons"]
            cons_err = offshore.loc[group]["Cons_err"]
        except KeyError:
            continue
    # if group == "Sugar":
    #     cons = sugarprov * 1000 #tonnes
    scalar = cons * 1000 #kg

    colour = colours_stim[group]
    if group in domestic.index:
        domestic_imp = domestic.loc[group][impact] / scalar
        domestic_imp_err = domestic.loc[group][impact+"_err"] / scalar
        dom_feed = domestic.loc[group].bd_opp_feed / scalar
        dom_feed_err = domestic.loc[group].bd_opp_feed_err / scalar
        dom_food = domestic.loc[group].bd_opp_food / scalar
        dom_food_err = domestic.loc[group].bd_opp_food_err / scalar
    else:
        domestic_imp = 0
        domestic_imp_err = 0
        dom_feed = 0
        dom_feed_err = 0
        dom_food = 0
        dom_food_err = 0
    if group in offshore.index:
        offshore_imp = offshore.loc[group][impact] / scalar
        offshore_imp_err = offshore.loc[group][impact+"_err"] / scalar
        os_feed = offshore.loc[group].bd_opp_feed / scalar
        os_feed_err = offshore.loc[group].bd_opp_feed_err / scalar
        os_food = offshore.loc[group].bd_opp_food / scalar
        os_food_err = offshore.loc[group].bd_opp_food_err / scalar
    else:
        offshore_imp = 0
    ax.barh(g, -domestic_imp, color = colour,
            alpha = alpha,xerr = domestic_imp_err)
    ax.barh(g, offshore_imp, color = colour,
            alpha = alpha, xerr = offshore_imp_err)
    ax.barh(g, -dom_feed, fill = False, linewidth = 0,
            alpha = alpha, hatch = "//")
    ax.barh(g, os_feed, fill = False, linewidth = 0,
                alpha = alpha, hatch = "//")
ax.set_xticks(ax.get_xticks(), labels = [round(abs(x),11) for x in ax.get_xticks()])
# ax.set_xlabel("(a) annual extinctions contribution per kg", **font)

odf = pd.DataFrame(columns = ["Group", "val", "err","dratio"])

ax = axs[1]
scalar = 1# ukpop
for g, group in enumerate(groups):
    colour = colours_stim[group]
    if group in domestic.index:
        domestic_imp = domestic.loc[group][impact] / scalar
        domestic_imp_err = domestic.loc[group][impact+"_err"] / scalar
        dom_feed = domestic.loc[group].bd_opp_feed / scalar
        dom_feed_err = domestic.loc[group].bd_opp_feed_err / scalar
        dom_food = domestic.loc[group].bd_opp_food / scalar
        dom_food_err = domestic.loc[group].bd_opp_food_err / scalar
    else:
        domestic_imp = 0
        domestic_imp_err = 0
        dom_feed = 0
        dom_feed_err = 0
        dom_food = 0
        dom_food_err = 0
    if group in offshore.index:
        offshore_imp = offshore.loc[group][impact] / scalar
        offshore_imp_err = offshore.loc[group][impact+"_err"] / scalar
        os_feed = offshore.loc[group].bd_opp_feed / scalar
        os_feed_err = offshore.loc[group].bd_opp_feed_err / scalar
        os_food = offshore.loc[group].bd_opp_food / scalar
        os_food_err = offshore.loc[group].bd_opp_food_err / scalar
    else:
        offshore_imp = 0
    ogroup.append(group)
    oval.append(offshore_imp + domestic_imp)
    ovalerr.append(np.sqrt(offshore_imp_err**2+domestic_imp_err**2))
    try:
        drat.append(domestic_imp / (offshore_imp+domestic_imp))
    except ZeroDivisionError:
        continue
    ax.barh(g, -domestic_imp, color = colour,
            alpha = alpha,xerr = domestic_imp_err)
    ax.barh(g, offshore_imp, color = colour,
            alpha = alpha, xerr = offshore_imp_err)
    ax.barh(g, -dom_feed, fill = False, linewidth = 0,
            alpha = alpha, hatch = "//")
    if g==0:
        ax.barh(g, os_feed, fill = False, linewidth = 0,
                alpha = alpha, hatch = "//", label = "Feed")
    else:
        ax.barh(g, os_feed, fill = False, linewidth = 0,
                alpha = alpha, hatch = "//")
ax.set_xticks(ax.get_xticks(), labels = [round(abs(x),11) for x in ax.get_xticks()])
# ax.set_xlabel("(b) annual extinctions contribution total", **font)
ax.legend(fontsize =fontsize_leg,
          fancybox=False, shadow=False)
for ax in axs:
    ax.text(ax.get_xticks()[0]/2, -0.5+len(groups)/2, "Domestic",
            fontsize = dfsize, alpha =textalph,
            rotation = 90,verticalalignment = "center",horizontalalignment="center")
    ax.text(-ax.get_xticks()[0]/2, -0.5+len(groups)/2, "Offshore",
            fontsize = dfsize, alpha =textalph,
            rotation = 270,verticalalignment = "center",horizontalalignment="center")
    ax.axvline(0, color="k")
    ax.set_yticks(np.arange(0,len(groups), 1),
                  labels = [group_label_conv[k] for k in list(groups)],
                  rotation = 10, **font)

fig.set_size_inches(figsize)
fig.tight_layout()
fig.savefig(os.path.join(savepath, "specific_total_hbar_extinctions.png"),
            dpi = 500)

# df= pd.DataFrame({"Group":ogroup,"bd_value":oval, "bd_err":ovalerr,"dratio":drat})
df_uk.to_csv(os.path.join(bpath, "df_domestic.csv"))
df_os.to_csv(os.path.join(bpath, "df_offshore.csv"))
xdf.to_csv(os.path.join(bpath, "xdf.csv"))
kdf.to_csv(os.path.join(bpath, "kdf.csv"))
