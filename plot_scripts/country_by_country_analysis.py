# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 15:34:30 2024

@author: Thomas Ball
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt


odPath = "E:\\OneDrive\\OneDrive - University of Cambridge"
# odPath = "C:\\Users\\Thomas Ball\\OneDrive - University of Cambridge"
resultsPath = os.path.join(odPath, "Work\\FOODv0\\results")
figPath = "figs"
datPath = "food_v0\\dat"

global_dat = pd.read_csv(os.path.join("results", "odf_commodities.csv"),index_col=0)
crop_db = pd.read_csv(os.path.join(odPath, "Work\\FOODv0\\food_v0", 
    "crop_db.csv"))

groups = crop_db.group_name_v6.unique()
country_db_file = "nocsDataExport_20220822-151738.xlsx"
country_db = pd.read_excel(os.path.join(datPath,country_db_file))
pop_dat = pd.read_csv(os.path.join(datPath,"FAOSTAT_data_en_3-12-2024_population.csv"))
pop_dat = pop_dat[pop_dat.Year == 2021]
cal_dat = pd.read_csv(os.path.join(datPath,"FAOSTAT_data_en_3-12-2024_calories.csv"))

coi = {
        
        # "DEU" : "", 
        "USA" : {"marker" : ">", "color" : "#EDF97A"},
        "BRA" : {"marker": "x", "color" : "#DC267F"},
        "JPN" : {"marker": ".", "color" : "#FE6100"},
        
        "UGA" : {"marker" : "^", "color" : "#648FFF"},
        "GBR" : {"marker": "v", "color" : "#FFB000"}, 
        "IND" : {"marker": "o", "color" : "#785EF0"},
        # "TZA" : {}, 
        
        # "LKA" : {}
        # "UKR" : {}
        }

coi = {
        
        # "DEU" : "", 
        "USA" : {"marker" : ">", "color" : "#EDF97A"},
        "JPN" : {"marker": ".", "color" : "#FE6100"},
        "GBR" : {"marker": "v", "color" : "#FFB000"}, 
        
        "BRA" : {"marker": "x", "color" : "#DC267F"},
        "UGA" : {"marker" : "^", "color" : "#648FFF"},
        "IND" : {"marker": "o", "color" : "#785EF0"},
        # "TZA" : {}, 
        
        # "LKA" : {}
        # "UKR" : {}
        }

colours = { 
                'Ruminant meat' : "#C90D75",
                'Pig meat'       : "#D64A98",
                'Poultry meat'   : "#D880B1",
                'Dairy'          : "#F7BDDD",
                'Eggs'           : "#FFEDF7",
                
                'Grains'             : "#D55E00",
                "Rice"               : "#D88E53",
                "Soybeans"           : "#DCBA9E",
                
                'Roots and tubers'   : "#0072B2",
                'Vegetables'         : "#4F98C1",
                'Legumes and pulses' : "#9EBFD2",
                
                'Bananas'           : "#FFED00",
                'Tropical fruit'    : "#FFF357",
                'Temperate fruit'   : "#FDF8B9",
                'Tropical nuts'     : "#27E2FF",
                'Temperate nuts'    : "#7DEEFF",
                    
                'Sugar beet'    : "#FFC000",
                'Sugar cane'    : "#F7C93B",
                'Spices'        : "#009E73",
                'Coffee'        : "#33CCA2",
                'Cocoa'         : "#62DEBC",
                "Tea and maté"  : "#A2F5DE",
                
                "Oilcrops" : "k",
                "Other" : "#A2A2A2"
                }

data_df = pd.DataFrame()
odf = pd.DataFrame()

#%%
def w_mean(df, col, cons_col):
    w_mean = (df[col] * df[cons_col]).sum() / (df[cons_col].sum())**2
    if type(w_mean) != float:
        w_mean = w_mean.squeeze()
    return w_mean / 1000

def invert_color(hex_color):
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Convert hex to RGB
    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)
    
    # Invert RGB
    inverted_red = 255 - red
    inverted_green = 255 - green
    inverted_blue = 255 - blue
    
    # Convert back to hex
    inverted_hex = '#{0:02x}{1:02x}{2:02x}'.format(inverted_red, inverted_green, inverted_blue)
    
    return inverted_hex
    
#%%
groups = np.concatenate([groups, ["Total"]])

for c in coi.keys():
    
    ccode = country_db[country_db.ISO3==c].M49
    cpop = (pop_dat[pop_dat["Area Code (M49)"]==ccode.squeeze()].Value * 1000).squeeze()
    
    try:
        kdf = pd.read_csv(os.path.join(resultsPath, c.lower(), "kdf.csv"),index_col=0)
        xdf = pd.read_csv(os.path.join(resultsPath, c.lower(), "xdf.csv"),index_col=0)
    except FileNotFoundError:
        resultsPath_ext = "D:\\Food_v0\\all_results"
        kdf = pd.read_csv(os.path.join(resultsPath_ext, c.lower(), "kdf.csv"),index_col=0)
        xdf = pd.read_csv(os.path.join(resultsPath_ext, c.lower(), "xdf.csv"),index_col=0)
    
    xdf["Consumer"] = c
    xdf = xdf[~xdf.Item.str.contains("Vanill")]
    data_df = pd.concat([data_df, xdf])
    
    for g, group in enumerate(groups):
        
        if group == "Total":
            items = crop_db.Item
        else:
            items = crop_db[crop_db.group_name_v5 == group].Item
        
        kdf_groupdat = kdf[kdf.Item.isin(items)]
        total_cap = kdf_groupdat.bd_opp_total.sum() / (cpop * 365)
        feed_cap = kdf_groupdat.bd_opp_feed.sum() / (cpop * 365)
        food_cap = kdf_groupdat.bd_opp_food.sum() / (cpop * 365)
        
        # food
        xdfg = xdf[xdf.Item.isin(items)]
        prov = xdfg.provenance.sum()
        domestic = xdfg[xdfg.Country_ISO == c]
        offshore = xdfg[xdfg.Country_ISO != c]
        dom_oc_food = domestic.bd_opp_cost_calc.sum()
        os_oc_food = offshore.bd_opp_cost_calc.sum()
        w_mean_food_domestic = w_mean(domestic, "bd_opp_cost_calc", "provenance")
        w_mean_food_offshore = w_mean(offshore, "bd_opp_cost_calc", "provenance")
        
        # feed
        xdfg = xdf[xdf.Animal_Product.isin(items)]
        domestic = xdfg[xdfg.Country_ISO == c]
        offshore = xdfg[xdfg.Country_ISO != c]
        if len(xdfg) > 0:
            w_mean_feed_domestic = w_mean(domestic, "bd_opp_cost_calc", "provenance")
            w_mean_feed_offshore= w_mean(offshore, "bd_opp_cost_calc", "provenance")
            dom_oc_feed = domestic.bd_opp_cost_calc.sum()
            os_oc_feed = offshore.bd_opp_cost_calc.sum()
        else:
            w_mean_feed_domestic = 0
            w_mean_feed_offshore = 0
            dom_oc_feed = 0
            os_oc_feed = 0
        
        tdom = np.nansum([w_mean_food_domestic, w_mean_feed_domestic])
        toff = np.nansum([w_mean_food_offshore, w_mean_feed_offshore])
        
        if (np.array([tdom,toff]) == 0).any():
            ratio = 0
        else:
            ratio = toff / tdom
        
        perc_dom = np.nansum([dom_oc_food, dom_oc_feed]) / np.nansum([os_oc_food, os_oc_feed, dom_oc_food, dom_oc_feed])
        perc_os = 1-perc_dom
        odf = pd.concat([odf, pd.DataFrame({
                        "a":c,
                        "g":group,
                        "total_cap": total_cap,
                        "feed_cap": feed_cap,
                        "food_cap": food_cap,
                        # "dom_kg" : tdom,
                        # "os_kg" : toff,
                        "ratio" : ratio,
                        "perc_os" : perc_os,
                        "cons" : prov,
                        "pop" : cpop},
            
                     index = [0])
                         ])
  
odf["cons_pc"] = odf.cons / odf["pop"]

odf.to_csv(os.path.join(resultsPath, "odf_countries.csv"))
           
odf = odf[~(odf.g.isna())]
odf = odf[~odf.g.str.contains("sug",case=False)]
groups = odf.g.unique()
areas = odf.a.unique()

#%%
fig, ax = plt.subplots()
alpha = 0.8
figsize = (8, 7)
country_m49s = [country_db[country_db.ISO3==c].M49.squeeze() for c in areas]
mean_cals = cal_dat[cal_dat["Area Code (M49)"].isin(country_m49s)].Value.mean()

xgroups = groups[:-1]
exc_groups = ["Sugar beet", "Sugar cane"]# "Other"]#, "Oilcrops"]
xgroups = groups[:-1]
xgroups = [k for k in colours.keys() if k not in exc_groups]


for a, area in enumerate(areas):
    
    ccode = country_db[country_db.ISO3==area].M49
    cdat = odf[odf.a==area]
    ccals = cal_dat[cal_dat["Area Code (M49)"]==ccode.squeeze()].Value.squeeze()
    
    cal_scalar =1# mean_cals / ccals
    print(mean_cals, ccals)
    # cal_scalar = 1
    # cal_scalar = 1 / cdat.total_cap.sum()
    
    ctotal = 0
    for g, group in enumerate(xgroups):
        
        if group in colours.keys():
            color = colours[group]
        else:
            color = "k" 
            
        val = cdat[cdat.g==group].total_cap.squeeze() * cal_scalar
        
        if a == 0:
            ax.bar(a, val, bottom = ctotal, 
                   color = color,
                   alpha = alpha,
                   label = group)
        else:
            ax.bar(a, val, bottom = ctotal, color = color,
                   alpha = alpha)
        ctotal = np.nansum([ctotal,val])
        
    print(area, cdat[cdat.g=="Ruminant meat"].total_cap.squeeze() * cal_scalar / ctotal)
    
ax.legend(ncol = 3)
ax.set_xticks(np.arange(0, len(areas),1), labels = ["UK" if a == "GBR" else a for a in areas])
ax.set_ylabel("Mean daily consumption impact ($\Delta$E per-capita per-day)")
fig = plt.gcf()
fig.set_size_inches(figsize)
fig.tight_layout()


#%%
def OSRATIO():
    ac = len(areas)
    ag = len(groups)
    
    offset_scale = 0.7
    bwidth = -0.01 + offset_scale / ac
    alpha_offset = 0.3
    ylim = (-1.2, 15.5)
    figsize = (8, 7)
    markersize = 40
    
    fig, axs = plt.subplots(2, 1)
    
    country_m49s = [country_db[country_db.ISO3==c].M49.squeeze() for c in areas]
    mean_cals = cal_dat[cal_dat["Area Code (M49)"].isin(country_m49s)].Value.mean()
    
    new_ax = len(groups) // 2
    
    for a, area in enumerate(areas):
        
        ccode = country_db[country_db.ISO3==area].M49
        ccals = cal_dat[cal_dat["Area Code (M49)"]==ccode.squeeze()].Value.squeeze()
        cal_scalar = mean_cals / ccals
        cdat = odf[odf.a==area]
        
        try:
            marker = coi[area]["marker"]
        except KeyError:
            marker = "x"
            
        try:
            color = coi[area]["color"]
        except KeyError:
            color = "k"  
            
        offset = - (offset_scale/2) + offset_scale * a/ac 
        
        alpha = (a + alpha_offset) / (ac + alpha_offset)
        alpha = 0.5
        
        for g, group in enumerate(groups):
                
            if g >= new_ax:
                ax = axs[1]
            else:
                ax = axs[0]
                
            # if group in colours.keys():
            #     color = colours[group]
            # else:
            #     color = "k" 
            
            gdat = cdat[cdat.g == group]
            
            rval = gdat.ratio.squeeze()
            
            if rval > ylim[1]:
                ravl = ylim[1] - 0.2
            
            xpos = g + offset
            
            if rval != 0:
                ax.bar(xpos, rval - 1, bottom = 1, 
                       width = bwidth, color = color, alpha = alpha)
                ax.scatter([xpos], [rval],
                           marker = marker, s = markersize,
                           color = color)
                if g == 0:
                    ax.scatter([xpos], [rval],
                               marker = marker, color = color,
                               s = markersize,
                               label = area)
                           
    axs[0].hlines(1, *axs[0].get_xlim(), linestyle = "--", color = "k", alpha = 0.8)
    axs[1].hlines(1, *axs[1].get_xlim(), linestyle = "--", color = "k", alpha = 0.8)
    
    axs[0].set_ylim(*ylim)
    axs[1].set_ylim(*ylim)        
    
    axs[0].legend()
    
    def strip_chars(string):
        ustring = string.replace(" and ", ", ")
        return ustring
        
    sgroups = [strip_chars(string) for string in groups]
    axs[0].set_xticks(np.arange(0, len(sgroups[:new_ax]),1), labels = sgroups[:new_ax], 
                      rotation = 75)
    axs[1].set_xticks(np.arange(new_ax, new_ax + len(sgroups[new_ax:]),1), labels = sgroups[new_ax:], 
                      rotation = 75)
    fig = plt.gcf()
    fig.set_size_inches(figsize)
    fig.tight_layout()

#%%
def OSBARS_unused():
    ac = len(areas)
    ag = len(groups)
    
    offset_scale = 0.4
    bwidth = -0.6 + offset_scale / 2
    alpha_offset = 0.5
    figsize = (8, 7)
    markersize = 60
    
    fig, ax = plt.subplots()
    
    country_m49s = [country_db[country_db.ISO3==c].M49.squeeze() for c in areas]
    mean_cals = cal_dat[cal_dat["Area Code (M49)"].isin(country_m49s)].Value.mean()
    
    xgroups = groups[:-1]
    xgroups = [k for k in colours.keys() if "Sugar" not in k]
    
    for a, area in enumerate(areas):
        
        ccode = country_db[country_db.ISO3==area].M49
        ccals = cal_dat[cal_dat["Area Code (M49)"]==ccode.squeeze()].Value.squeeze()
        cal_scalar = mean_cals / ccals
        cal_scalar = 1
        
        cdat = odf[odf.a==area]
        
        try:
            marker = coi[area]["marker"]
        except KeyError:
            marker = "x"
        
        alpha = (a + alpha_offset) / (ac + alpha_offset)
        alpha = 0.6
        
        os_b, do_b = 0,0 
    
        for g, group in enumerate(xgroups):
            
            try:
                color = colours[group]
            except KeyError:
                color = "k"  
            
            gdat = cdat[cdat.g == group]
            
            val = gdat.total_cap.squeeze()
            os_val = val * gdat.perc_os.squeeze()
            do_val = val * (1-gdat.perc_os.squeeze())
            
            offset = - (offset_scale/2) + offset_scale * 0
            
            xpos = a + offset
            ax.bar(xpos, os_val, bottom = os_b, 
                   width = bwidth, color = color, alpha = alpha)
            offset = - (offset_scale/2) + offset_scale * 1 
            os_b += os_val
            
            xpos = a + offset
            ax.bar(xpos, do_val, bottom = do_b,
                   width = bwidth, color = color, alpha = alpha)
            do_b += do_val
                           
    # axs[0].hlines(1, *axs[0].get_xlim(), linestyle = "--", color = "k", alpha = 0.8)
    # axs[1].hlines(1, *axs[1].get_xlim(), linestyle = "--", color = "k", alpha = 0.8) 
    
    # axs[0].legend()
    
    # def strip_chars(string):
    #     ustring = string.replace(" and ", ", ")
    #     return ustring
        
    # sgroups = [strip_chars(string) for string in groups]
    # axs[0].set_xticks(np.arange(0, len(sgroups[:new_ax]),1), labels = sgroups[:new_ax], 
    #                   rotation = 75)
    # axs[1].set_xticks(np.arange(new_ax, new_ax + len(sgroups[new_ax:]),1), labels = sgroups[new_ax:], 
    #                   rotation = 75)
    
    # fig = plt.gcf()
    # # fig.text(0.5, 0.04, 'common X', ha='center')
    
    # fig.set_size_inches(figsize)
    # fig.add_subplot(111, frameon=False)
    # # hide tick and tick label of the big axis
    # plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    # # plt.xlabel("common X")
    # plt.ylabel("Proportion of per-capita \nconsumption impact arising from imports")
    # fig.tight_layout()

#%%

ac = len(areas)
ag = len(groups)

offset_scale = 0.4
bwidth = -0.6 + offset_scale / 2
# alpha_offset = 0.5
figsize = (8, 7)
markersize = 60

dfsize = 30
dfalph = 0.6

alpha = 0.8

ylab = "Percentage of per-capita impact"
ylim = (-0.5, 0.5)
yticks = np.arange(-0.5, 0.75, 0.25)
yticks_labels = np.absolute(np.arange(-100, 150, 50))
yticks_labels = [str(x) + "%" for x in yticks_labels]
# yticks_labels = [100, "domestic   50", 0, "overseas   50", 100]

fig, ax = plt.subplots()

country_m49s = [country_db[country_db.ISO3==c].M49.squeeze() for c in areas]
mean_cals = cal_dat[cal_dat["Area Code (M49)"].isin(country_m49s)].Value.mean()

exc_groups = ["Sugar beet", "Sugar cane", "Other"]#, "Oilcrops"]

xgroups = groups[:-1]
xgroups = [k for k in colours.keys() if k not in exc_groups]

labels = []

for a, area in enumerate(areas):
    
    cdat = odf[odf.a==area]
    ccode = country_db[country_db.ISO3==area].M49
    ccals = cal_dat[cal_dat["Area Code (M49)"]==ccode.squeeze()].Value.squeeze()
    # cal_scalar = mean_cals / ccals
    # cal_scalar = 1
    cal_scalar = 1 / cdat.total_cap.sum()
    cal_scalar = ccals
    
    try:
        marker = coi[area]["marker"]
    except KeyError:
        marker = "x"
    
    # alpha = (a + alpha_offset) / (ac + alpha_offset)
    
    
    os_b, do_b = 0,0 

    for g, group in enumerate(xgroups):
        
        try:
            color = colours[group]
        except KeyError:
            color = "k"  
        
        gdat = cdat[cdat.g == group]
        
        val = gdat.total_cap.squeeze() / cdat.total_cap.sum()
        os_val = val * gdat.perc_os.squeeze()
        do_val = val * (1-gdat.perc_os.squeeze())
        
        offset = - (offset_scale/2) + offset_scale * 0
        offset = 0
        
        xpos = a + offset
        if group not in ax.get_legend_handles_labels()[1]:
            ax.bar(xpos, os_val, bottom = os_b, 
                   width = bwidth, color = color, alpha = alpha,
                   label = group)
        else:
            ax.bar(xpos, os_val, bottom = os_b, 
                   width = bwidth, color = color, alpha = alpha,
                   )
            
        offset = - (offset_scale/2) + offset_scale * 1 
        offset = 0
        
        os_b += os_val
        
        xpos = a + offset
        if group not in ax.get_legend_handles_labels()[1]:
            ax.bar(xpos, -do_val, bottom = -do_b,
                   width = bwidth, color = color, alpha = alpha,
                   label = group)
        else:
            ax.bar(xpos, -do_val, bottom = -do_b,
                   width = bwidth, color = color, alpha = alpha,
                   )
        do_b += do_val
                       
        
ax.text(-0.5, -0.25, "Domestic",
        fontsize = dfsize, alpha =dfalph,
        rotation = 90,verticalalignment = "center",horizontalalignment="center")

ax.text(-0.5, 0.25, "Imported",
        fontsize = dfsize, alpha =dfalph,
        rotation = 90,verticalalignment = "center",horizontalalignment="center")
        
ax.hlines(0, *ax.get_xlim(), linestyle = "--", color = "k", alpha = 0.6)
ax.set_ylim(*ylim)
ax.set_yticks(yticks, labels = yticks_labels)
ax.legend(ncol = 2)
ax.set_xticks(np.arange(0, len(areas),1), labels = ["UK" if a == "GBR" else a for a in areas])
ax.set_ylabel(ylab)
fig = plt.gcf()
fig.set_size_inches(figsize)
fig.tight_layout()

