# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 11:21:46 2024

@author: tom
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import pickle

datPath = os.path.join("..", "model", "dat")
oPath = os.path.join("..", "model", "global_commodity_impacts")

db = pd.read_csv(os.path.join("..", "model", "crop_db.csv"))

grouping = "group_name_v6"
quants = [0.10, 0.5, 0.90]
# =============================================================================
figsize = (8,7)
alpha = 0.8
ylabel = u"Specific extinction impact distribution (log10 $\Delta$E per-kilogram-year)"
# =============================================================================

colours_stim = { 
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
                
                "Oilcrops" : "#000000",
                "Other" : "#A2A2A2"
                }


with open(os.path.join(oPath,"datalist.pkl"), 'rb') as file:
    # datalist = pickle.load(file)
    datalist = pd.read_pickle(file)
with open(os.path.join(oPath,"itemlist.pkl"), 'rb') as file:
    # itemlist = pickle.load(file)
    itemlist = pd.read_pickle(file)

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

def weighted_quantile(values, quantiles, sample_weight=None, 
                      values_sorted=False, old_style=False):
    """ Very close to numpy.percentile, but supports weights.
    NOTE: quantiles should be in [0, 1]!
    :param values: numpy.array with data
    :param quantiles: array-like with many quantiles needed
    :param sample_weight: array-like of the same length as `array`
    :param values_sorted: bool, if True, then will avoid sorting of
        initial array
    :param old_style: if True, will correct output to be consistent
        with numpy.percentile.
    :return: numpy.array with computed quantiles.
    """
    values = np.array(values)
    quantiles = np.array(quantiles)
    if sample_weight is None:
        sample_weight = np.ones(len(values))
    sample_weight = np.array(sample_weight)
    assert np.all(quantiles >= 0) and np.all(quantiles <= 1), \
        'quantiles should be in [0, 1]'

    if not values_sorted:
        sorter = np.argsort(values)
        values = values[sorter]
        sample_weight = sample_weight[sorter]

    weighted_quantiles = np.cumsum(sample_weight) - 0.5 * sample_weight
    
    if old_style:
        # To be convenient with numpy.percentile
        weighted_quantiles -= weighted_quantiles[0]
        weighted_quantiles /= weighted_quantiles[-1]
    else:
        weighted_quantiles /= np.sum(sample_weight)
    return np.interp(quantiles, weighted_quantiles, values)


def get_group(item, tgroup, isanim):
    group = db[db.Item == item][tgroup].squeeze()
    if isanim:
        group = db[db.group_name_v2 == item][tgroup].squeeze()
        if not type(group) == str and len(group) > 1:
            group = group.iloc[0]
    return group
        
df = pd.DataFrame()
for i, item in enumerate(itemlist):
    dat = datalist[i]
    if len(dat)>0:
        dat["Item"] = item
        isanim = dat.isanim.any()
        dat["Group"] = [get_group(item,grouping,isanim) for k in range(len(dat))]
        df = pd.concat([df,dat])

df["t_est"] = df.bd * df.w
#%%
AGGREGATE = "Group"
# AGGREGATE = "Item"

for i, item in enumerate(df[AGGREGATE].unique()):
    dat = df[(df[AGGREGATE] == item)&(np.isfinite(df.w))]
    
    dat["wn"] = dat.w / dat.w.sum()
    df.loc[df[AGGREGATE] == item, ["LQ","MQ","HQ"]] = weighted_quantile(dat.bd, quants, 
                                sample_weight=dat.wn,values_sorted=False)
    
#%%
df = df.sort_values("MQ")
odf =pd.DataFrame()

df = df[df.Group != "Other"]
tick_labels = []
fig, ax = plt.subplots()
for i, item in enumerate(df[AGGREGATE].unique()):       
    # FILTER
    dat = df[(df[AGGREGATE] == item)&(np.isfinite(df.w))].copy()
    dat["wn"] = dat.w / dat.w.sum()
    
    # Get vals
    LQ = dat.LQ.unique().squeeze()
    MQ = dat.MQ.unique().squeeze()
    HQ = dat.HQ.unique().squeeze()
    
    odf = pd.concat([odf, pd.DataFrame([item, LQ,MQ,HQ],index= ["g", "LQ", "MQ", "HQ"]).T])
    LQ = np.log10(LQ)
    MQ = np.log10(MQ)
    HQ = np.log10(HQ)
    pr = HQ-LQ
    
    try:
        color = colours_stim[item]
    except KeyError:
        color = "r"
        
    # if dat.isanim.any():
    #     xcolor = "b"
    # else: xcolor = "g" 
    
    color = "#D55E00"

    # PLOT
    ax.bar(i, pr, bottom = LQ, fill=True, color = color, 
           edgecolor = color, alpha = alpha)
    # ax.scatter(i, p50, marker = "x", color = xcolor)
    ax.bar(i, 0, bottom = MQ, fill=False, edgecolor = invert_color(color), alpha = 1)
    
    tick_labels.append(item) 

# EXTRAS
ax.set_xticks(np.arange(0,len(tick_labels),1), 
              labels = tick_labels, 
                rotation = 90)
ax.set_ylabel(ylabel)
fig.set_size_inches(figsize)
fig.tight_layout()