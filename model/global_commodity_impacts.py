# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 11:25:12 2024

@author: Thomas Ball
"""

import pandas as pd
import numpy as np
import os
import pickle

# def main(overwrite):
overwrite = True
years = 5
datPath = "dat"
oPath = "global_commodity_impacts"
#%%
if not os.path.isfile(os.path.join(oPath,"df.pkl")) or not os.path.isfile(
        os.path.join(oPath,"itemlist.pkl")) or not os.path.isfile(
            os.path.join(oPath,"datalist.pkl")) or overwrite:
    
    # where are the files
    suafile = "SUA_Crops_Livestock_E_All_Data_(Normalized).csv" # FAO supply utilisation accounts
    prodfile = "Production_Crops_Livestock_E_All_Data_(Normalized).csv" # FAO production data
    bd_factors_file = "country_opp_cost_v4.csv" # dat
    country_db_file = "nocsDataExport_20220822-151738.xlsx" # dat
    comm_db_file = "crop_db.csv" # dat
    pasture_factors_file = "tb_pasture_factors_2.csv" # dat
    primary_mapping_file = "primary_item_map_feed.csv" # Schwarzmueller
    content_factors_file = "content_factors_per_100g.xlsx" # Schwarzmueller
    prov_mat_feed_file = "TradeMatrixFeed_import_dry_matter_2013.csv" # Schwarzmueller
    weighing_factors_file = "weighing_factors.csv" # Schwarzmueller
    p_n_file = "Planet-Based Diets - Data and Viewer.xlsx" # WWF planet based diets
    
    # load and do some stuff to the files
    bd_factors = pd.read_csv(os.path.join(datPath,bd_factors_file), index_col = 0)
    prod = pd.read_csv(os.path.join(datPath,prodfile), index_col = 0, 
                          encoding = "latin-1")
    fM49 = lambda string: int(string.strip("'"))
    prod = prod[prod.Year > prod.Year.max() - (years + 1)]
    prod["Area Code (M49)"] = prod["Area Code (M49)"].apply(fM49)
    comm_db = pd.read_csv(comm_db_file)
    country_db = pd.read_excel(os.path.join(datPath,country_db_file))
    primary_mapping = pd.read_csv(os.path.join(datPath, primary_mapping_file),
                                  encoding = "latin-1")
    content_factors = pd.read_excel(os.path.join(datPath, content_factors_file),
                                    header = 1)
    pasture_factors = pd.read_csv(os.path.join(datPath, pasture_factors_file), 
                                               index_col = 0)
    prov_mat_feed = pd.read_csv(os.path.join(datPath, prov_mat_feed_file))
    weighing_factors = pd.read_csv(os.path.join(datPath, weighing_factors_file))
    p_n = pd.read_excel(os.path.join(datPath, p_n_file), 
                        sheet_name = "DATA - Product Level")
    sm_wwf_map = pd.read_csv(os.path.join(
        datPath, "schwarzmueller_wwf.csv"),index_col = 0)
    
    
    # what r the items
    bd_items = [item for item in bd_factors.columns if "err" not in item]
    
    # for calculating
    def w_mean_err(a, a_err, w, w_err):
        wmean = np.nansum(a * w) / (np.nansum(w))
        e_term1 = np.nansum(w_err ** 2) / (np.nansum(w)**2)
        e_term2 = np.nansum(((w_err/w)**2) + ((a_err/a)**2)) / (np.nansum(a*w)**2)
        wmean_err = wmean * np.sqrt(e_term1 + e_term2)
        return wmean, wmean_err
    
    # output data
    itemlist, datalist = [],[]
    
    # iterate items
    for i, bd_item in enumerate(bd_items):
        
        #filter biodiversity
        bd_filt = bd_factors[bd_item]
        bd_errs = bd_factors[bd_item + "_err"]
        
        # get FAO names / codes
        fao_items, fao_codes = comm_db[comm_db.GAEZres06 == bd_item].loc[:,["Item", "Item_Code"]].values.T.squeeze()
        mkarr = lambda inlist: np.array([inlist]) if not isinstance(inlist, np.ndarray) else inlist
        fao_items, fao_codes = mkarr(fao_items), mkarr(fao_codes)
        
        for item_idx, item_name in enumerate(fao_items):
            
            fao_code = fao_codes[item_idx]
            
            # get countries with non-zero bd value
            item_producers_ISO3 = bd_factors[(~bd_filt.isna())&(bd_filt>0)].index.to_list()
            item_producers_M49 = [country_db[country_db.ISO3 == area].M49.squeeze() for area in item_producers_ISO3]
            
            # filter production data by these items and producers
            pfilt = prod[(prod["Item Code"].isin(mkarr(fao_code)))&(prod["Area Code (M49)"].isin(item_producers_M49))]
    
            # ignore animals and do those later, also ignore non-food
            if pfilt.shape[0] == 0 and item_name not in ["tob", "cot", "fdd"]:
                pass
            
            else:
                print(i/len(bd_items))
                
                bd_perkg,bd_perkg_err,pweights,pweights_err,areas,isanim = [],[],[],[],[],[]
                
                # iterate countries
                for areaM49 in item_producers_M49:
                    
                    areaISO3 = country_db[country_db.M49 == areaM49].ISO3.squeeze()
                        
                    # get yield for country hg/ha
                    yields = pfilt[(pfilt["Area Code (M49)"]==areaM49)&(pfilt.Element=="Yield")]
                    yield_means = yields.groupby("Item").Value.agg(np.mean)
                    yield_errs = yields.groupby("Item").Value.agg(lambda x: np.std(x) / np.sqrt(len(x)))
                    
                    prods = pfilt[(pfilt["Area Code (M49)"]==areaM49)&(pfilt.Element=="Production")]
                    prod_means = prods.groupby("Item").Value.agg(np.mean)
                    prod_errs = prods.groupby("Item").Value.agg(lambda x: np.std(x) / np.sqrt(len(x)))
                    
                    # calcualte weighted average yield for the group (+error)
                    yield_wmean,yield_wmean_err = w_mean_err(yield_means, yield_errs, prod_means, prod_errs)
                    
                    # get bd value and err (per km2)
                    area_bd_val = bd_filt[areaISO3].squeeze()
                    area_bd_err = bd_errs[areaISO3].squeeze()
                    
                    # calculate per kg impact
                    val = (area_bd_val) / (yield_wmean * 10)
                    
                    # append the value, (prod)weights, and errs
                    if not np.isnan(val) and not np.isinf(val):
                        bd_perkg.append(val)
                        bd_perkg_err.append(val*np.sqrt((yield_wmean_err/yield_wmean)**2+(area_bd_err/area_bd_val)**2))
                        # calculate mean weighting
                        pweights.append(np.sum(prod_means))
                        pweights_err.append(np.sqrt((prod_errs**2).sum()))
                        areas.append(areaISO3)
                        isanim.append(False)
                
                if len(bd_perkg) > 0:
                    xdf = pd.DataFrame({"bd":bd_perkg,"bde":bd_perkg_err,"w":pweights,"we":pweights_err, "a":areas,"isanim":isanim})
                    bd_perkg,bd_perkg_err,pweights,pweights_err = map(pd.Series, (bd_perkg,bd_perkg_err,pweights,pweights_err))
                    bd_wmean = np.sum(bd_perkg * pweights) / np.sum(pweights)
                    bd_wmean_err = np.sqrt(np.var(bd_perkg)) * np.sqrt(np.sum((pweights/np.sum(pweights))**2))
                    itemlist.append(item_name)
                    datalist.append(xdf)
 
    livestock_items = {
        "Dairy" : [{"bvmilk" : ["Milk, whole fresh cow"]}, 0.6],
        "Cattle meat" : [{"bvmeat" : ["Meat, cattle"]}, 25],
         "Sheep and goat meat" : [{"sgmeat" : ["Meat, sheep", "Meat, goat"]}, 12],
        "Poultry meat" : [{"chickens" : ["Meat, chicken"], 
                          "ducks" : ["Meat, duck","Meat, goose and guinea fowl","Meat, turkey"]}, 4.5],
        "Pig meat" : [{"pigs" : ["Meat, pig"]}, 9],
        "Eggs" : [{"chickens" : ["Eggs, hen, in shell"]}, 2]
                       }
    
    # # iterate through livestock items
    for l, ls_prod in enumerate(livestock_items.keys()):
    
        
        ls_dat = livestock_items[ls_prod][0]
        ls_fcr = livestock_items[ls_prod][1]
        
        # iterate subprods
        for ls_bd_item in ls_dat.keys(): # eg chickens + other poultry
            
            primary_prods = ls_dat[ls_bd_item]
            
            #filter biodiversity
            bd_filt = bd_factors[ls_bd_item]
            bd_errs = bd_factors[ls_bd_item + "_err"]
            
            # get FAO names / codes
            fao_items, fao_codes = primary_mapping[primary_mapping.FAO_name.isin(primary_prods)].loc[:,["FAO_name", "FAO_code"]].values.T.squeeze()
            mkarr = lambda inlist: np.array([inlist]) if not isinstance(inlist, np.ndarray) else inlist
            fao_items, fao_codes = mkarr(fao_items), mkarr(fao_codes)
            feed_conv = weighing_factors[
                weighing_factors.Item_Code.isin(fao_codes)][
                    "Weighing factors"]
                    
            assert len(feed_conv.unique()) == 1
            feed_conv = feed_conv.unique()[0]
            
            wwf_item = sm_wwf_map[sm_wwf_map.Item_Code_FAO.isin(fao_codes)].WWF_cat
            assert(len(wwf_item.unique())) == 1
            wwf_item = wwf_item.unique()[0]
            
            # get countries with non-zero bd value
            item_producers_M49 = [country_db[country_db.ISO3 == area].M49.squeeze() for area in bd_factors[(~bd_filt.isna())&(bd_filt>0)].index.to_list()]
            
            
            # filter production data by these items and producers
            pfilt = prod[(prod["Item Code"].isin(fao_codes))&(prod["Area Code (M49)"].isin(item_producers_M49))]
            
            item_producers_M49 = [c for c in item_producers_M49 if c in pfilt["Area Code (M49)"].unique()]
            
            bd_perkg,bd_perkg_err,pweights,pweights_err,areas,bd_per_kg_f = [],[],[],[],[],[]
            isanim, bd_pasture_per_kg_list, kg_m2_tb, kg_m2_wwf = [],[],[],[]
            
            #iterate producers
            for a, areaM49 in enumerate(item_producers_M49):
                print(" " * 40,end = "\r")
                print(f"{ls_bd_item}  {round(a/len(item_producers_M49), 4)}",end = "\r")
                areaISO3 = country_db[country_db.M49 == areaM49].ISO3.squeeze()
                areaFAO = country_db[country_db.M49 == areaM49].FAOSTAT.squeeze()
                
                prods = pfilt[(pfilt["Area Code (M49)"]==areaM49)&(pfilt.Element=="Production")] #tonnes
                prod_means = prods.groupby("Item").Value.agg(np.mean).squeeze()
                prod_errs = prods.groupby("Item").Value.agg(lambda x: np.std(x) / np.sqrt(len(x)))
                
                
                # get pasture yield
                kg_m2 = 1/pasture_factors[(pasture_factors.Country_ISO==areaISO3)
                                        &(pasture_factors.livestock==ls_bd_item
                                          )].fp_m2_kg.squeeze() #m2 per kg
                
                bd_per_km2 = bd_factors[ls_bd_item].loc[areaISO3].squeeze()
                
                pf_wwf = 1/p_n[(p_n.Product == wwf_item)&(
                    p_n.Country_ISO == areaISO3)].Pasture_avg.squeeze() #m2 per kg
                
                def clean_nan_ser_inf(list_in, fval):
                    arr = np.array(list_in, dtype = "object")
                    if arr.size == 0: arr = np.zeros_like(arr.shape)
                    arr[np.logical_not(list(map(lambda x:isinstance(x,float) or isinstance(x,int), arr)))]=fval
                    arr[~np.isfinite(arr.astype(float))] = 0
                    return arr
                    
                    # impact from pasture
                if ls_bd_item in ["bvmeat","bvmilk","sgmeat"]:
                    m2_kg_val = clean_nan_ser_inf([kg_m2, pf_wwf],0).max() # kg / m2
                else: m2_kg_val = 0
                
                if m2_kg_val == 0:
                    bd_pasture_per_kg = 0
                else:
                    bd_pasture_per_kg = bd_per_km2 / (kg_m2 * 1000000)
                
                # do feed somehow
                feed_df = prov_mat_feed[
                    (prov_mat_feed.Animal_Product_Code.isin(fao_codes))\
                        &(prov_mat_feed.Consumer_Country_Code==areaFAO)]
                
                if len(feed_df) == 0:
                    bd_tfeed_per_kg = 0
                else:
                    feed_df = feed_df[(feed_df.Value > 0)&(np.logical_not(feed_df.Value.isna()))]
                    
                    feed_df.loc[:, "Value"] = feed_df.loc[:, "Value"] / feed_df.loc[:, "Value"].sum()
                    feed_df = feed_df[feed_df.Value > 1E-3] # filter by 1% to speed this up
                    
                    feed_df.loc[:, "Value"] = feed_df.loc[:, "Value"] / feed_df.loc[:, "Value"].sum()
                    # feed_total = prod_means.squeeze() * ls_fcr # tonnes for whole supply
                    feed_df.loc[:,"weight"] = feed_df.loc[:,"Value"] * ls_fcr # skip previous line ; fcr is mass beef for mass feed i.e. for 1 kg
                    
                    
                    for ridx, row in feed_df.iterrows():
                        feed_areaISO = country_db[country_db.FAOSTAT == row.Producer_Country_Code].ISO3.squeeze()
                        feed_areaM49 = country_db[country_db.FAOSTAT == row.Producer_Country_Code].M49.squeeze()
                        feed_bd_name = comm_db[comm_db.Item_Code == row.Item_Code].GAEZres06.squeeze()
                        try:
                            feed_bd_factor = bd_factors.loc[feed_areaISO][feed_bd_name] # per km2
                            feed_bd_factor = clean_nan_ser_inf([feed_bd_factor], 0).max()
                        except KeyError:
                            feed_bd_factor = 0
                            
                        feed_yield = prod[(prod["Area Code (M49)"]==areaM49)&(
                            prod.Element=="Yield")&(
                                prod["Item Code"]==row.Item_Code)].groupby(
                                    "Item").Value.agg(
                                        np.mean).squeeze() * 10 # kg/km2 
    
                        feed_yield = clean_nan_ser_inf([feed_yield], 0).max() # kg/km2
                        
                        if feed_yield == 0:
                            feed_bd_per_kg = 0
                        else:
                            feed_weight = feed_df.loc[ridx, "weight"] 
                            feed_bd_per_kg = feed_weight * feed_bd_factor / feed_yield
                        
                        feed_df.loc[ridx, "feed_bd_per_kg"] = feed_bd_per_kg
                        # can output this if need be...
                    
                    bd_tfeed_per_kg = feed_df.feed_bd_per_kg.sum()
                
                val = bd_tfeed_per_kg + bd_pasture_per_kg
                
                if not np.isnan(val) and not np.isinf(val):
                    bd_perkg.append(val)
                    bd_perkg_err.append(np.nan)
                    pweights.append(np.sum(prod_means))
                    pweights_err.append(np.sqrt((prod_errs**2).sum()))
                    areas.append(areaISO3)
                    bd_per_kg_f.append(bd_tfeed_per_kg)
                    isanim.append(True )
                    
                    kg_m2_tb.append(kg_m2)
                    kg_m2_wwf.append(pf_wwf)
                    bd_pasture_per_kg_list.append(bd_pasture_per_kg)

                
        xdf = pd.DataFrame({"bd":bd_perkg, "bd_f":bd_per_kg_f,
                            "bde":bd_perkg_err,"w":pweights,"we":pweights_err,
                            "a":areas, "isanim":isanim,
                            "bd_pasture_per_kg":bd_pasture_per_kg_list,
                            "kg_m2_tb":kg_m2_tb,
                            "kg_m2_wwf":kg_m2_wwf})
        
        itemlist.append(ls_prod)
        datalist.append(xdf)
                # cry

    if not os.path.isdir(oPath):
        os.mkdir(oPath)
        
    with open(os.path.join(oPath,"datalist.pkl"), 'wb') as file:
        pickle.dump(datalist, file)
    with open(os.path.join(oPath,"itemlist.pkl"), 'wb') as file:
        pickle.dump(itemlist, file)
    file = None


# else:
#     with open(os.path.join(oPath,"datalist.pkl"), 'rb') as file:
#         datalist = pickle.load(file)
#     with open(os.path.join(oPath,"itemlist.pkl"), 'rb') as file:
#         itemlist = pickle.load(file)
    
# return df, itemlist, datalist

# if __name__ == "__main__":
    
#     df, itemlist, datalist = main(True)
    
    