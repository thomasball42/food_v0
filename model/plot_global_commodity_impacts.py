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

# import global_commodity_impacts

# datPath = "..\\dat\\model\\dat"
datPath = "C:\\Users\\Thomas Ball\\OneDrive - University of Cambridge\\Work\\FOODv0\\food_v0\\dat"
oPath = "global_commodity_impacts"

db = pd.read_csv(os.path.join(datPath, "..", "crop_db.csv"))

quants = [0.1, 0.5, 0.90]
# =============================================================================
figsize = (8,6)
ylabel = "log10 LIFE restore per kg"
# =============================================================================

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
                    
                'Sugar crops'               : "#68EFF8",
                'Spices'                    : "#00C8D5",
                'Coffee'                : "#2b00d5",
                'Cocoa'                 : "#003cd5",
                "Tea and maté"          : "#0072d5",
                
                "Other" : "k"
                }

with open(os.path.join(oPath,"datalist.pkl"), 'rb') as file:
    datalist = pickle.load(file)
with open(os.path.join(oPath,"itemlist.pkl"), 'rb') as file:
    itemlist = pickle.load(file)

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
        group = item
    return group
        
df = pd.DataFrame()
for i, item in enumerate(itemlist):
    dat = datalist[i]
    if len(dat)>0:
        dat["Item"] = item
        
        isanim = dat.isanim.any()
        dat["Group"] = [get_group(item,"group_name_v5",isanim) for k in range(len(dat))]
        df = pd.concat([df,dat])



df["t_est"] = df.bd * df.w
#%%
AGGREGATE = "Group"

for i, item in enumerate(df[AGGREGATE].unique()):
    dat = df[(df[AGGREGATE] == item)&(np.isfinite(df.w))]
    
    dat["wn"] = dat.w / dat.w.sum()
    df.loc[df[AGGREGATE] == item, ["LQ","MQ","HQ"]] = weighted_quantile(dat.bd, quants, 
                                sample_weight=dat.wn,values_sorted=False)
#%%
df = df.drop(columns=['bd_f','bd_pasture_per_kg','kg_m2_tb','kg_m2_wwf','t_est'])
df = df.sort_values("MQ")
df.to_csv(os.path.join(oPath, "country_bd_items_weights.csv"))
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
    LQ = np.log10(LQ)
    MQ = np.log10(MQ)
    HQ = np.log10(HQ)
    pr = HQ-LQ
    
    # GET COLOURS
    if dat.isanim.any():
        group = db[db.group_name_v2 == item].group_name_v3.squeeze()
        if not isinstance(group, str):
            group = group.iloc[0]
    else:
        group = db[db.Item == item].group_name_v3.squeeze()
        
    if len(group) ==0:
        color = "r"
    else:
        color = colours_stim[group]
    # color = "r"
    if dat.isanim.any():
        xcolor = "r"
    else: xcolor = "g"   
    
    # PLOT
    ax.bar(i, pr, bottom = LQ, fill=True, color = color, edgecolor = color, alpha = 1)
    # ax.scatter(i, p50, marker = "x", color = xcolor)
    ax.bar(i, 0, bottom = MQ, fill=False, edgecolor = color, alpha = 1)
    tick_labels.append(item) 
# EXTRAS
ax.set_xticks(np.arange(0,len(tick_labels),1), 
              labels = tick_labels, 
                rotation = 90)
ax.set_ylabel(ylabel)
fig.set_size_inches(figsize)
fig.tight_layout()
