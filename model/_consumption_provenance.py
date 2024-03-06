# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 16:55:34 2022

@author: Thomas Ball
"""
import pandas as pd
import numpy as np
import os
import sys

try:
    import data_utils
except ModuleNotFoundError:
    import model.data_utils as data_utils
    
def add_item_cols(indf, datPath):
    item_codes = data_utils.get_item_codes(datPath)
    for i, idx in enumerate(indf.index):
        CPC_item_code = indf.loc[idx]["Item Code (CPC)"]
        try:
            item_info = item_codes[item_codes["CPC Code"] == CPC_item_code]
            item_name = item_info.Item.values[0]
            FAO_code = item_info["Item Code"].values[0]
            indf.loc[idx, "item_name"] = item_name
            indf.loc[idx, "FAO_code"] = FAO_code
        except IndexError:
            pass
    return indf

def main(fs, country_of_interest, scenPath, datPath):
    
    fserr = fs.copy()
    means = fs.groupby(["Item", "Item Code"]).Value.mean().reset_index()
    errs = fs.groupby(["Item", "Item Code"]).Value.sem().reset_index()
    
    fs = fs[fs.Year == fs.Year.unique().max()]
    fserr = fserr[fserr.Year==fserr.Year.unique().max()]
    for item in means.Item:
        fs.loc[fs.Item == item, "Value"] = means[means.Item==item].Value.values[0]
        fserr.loc[fserr.Item == item, "Value"] = errs[errs.Item==item].Value.values[0]
    
    offshoring = False
    if offshoring == True:
        prod_sum=pd.read_csv(
            os.path.join(scenPath, "prod_sum.csv"),index_col=0)
        offshorePath = "offshoring"
        try:
            crop_table=pd.read_csv(
                os.path.join(offshorePath,"crop_db.csv"),index_col=0)
        except FileNotFoundError:
            offshorePath = "."
            crop_table=pd.read_csv(
                os.path.join(offshorePath,"crop_db.csv"),index_col=0)
        prod_sum.index = [x.split("_")[0] for x in prod_sum.index]
        
    fs = add_item_cols(fs, datPath)
    fserr = add_item_cols(fserr, datPath)
    
    #%%
    item_codes = data_utils.get_item_codes(datPath)
    area_codes = data_utils.get_area_codes(datPath)
    coi_code = area_codes[area_codes["LIST NAME"] == country_of_interest][
        "FAOSTAT"].values[0]
    #%% random funcs
    def area_code_to_iso(code):
        try:
            ISO3 = area_codes[area_codes["FAOSTAT"] == code]["ISO3"].values[0]
        except IndexError:
            ISO3 = None
        return ISO3
    
    def item_code_to_product(code):
        try:
            product = item_codes[item_codes["Item Code"] == code][
                "Item"].values[0]
        except IndexError:
            product = None
        return product
    
    def add_cols(indf):
        df = indf.copy()
        df.loc[:, "Country_ISO"] = [area_code_to_iso(code) for code \
                                    in indf.loc[:, "Producer_Country_Code"]]
        df.loc[:, "Item"] = [item_code_to_product(code) for code \
                             in indf.loc[:, "Item_Code"]]
        if "Animal_Product_Code" in df.columns:
            df.loc[:, "Animal_Product"] = [item_code_to_product(code) for code\
                                 in indf.loc[:, "Animal_Product_Code"]]
        return df
    
    #%% calculate ratio of imports for crops, AP, and feed
    prov_mat_no_feed = data_utils.get_provenance_matrix_nofeed(2013, datPath)
    prov_mat_feed = data_utils.get_provenance_matrix_feed(2013, datPath)
    def import_ratios(prov_mat_feed, prov_mat_no_feed, coi_code):
        # This is the trade matrix with the re-exp algorithm applied and 
        # converted into dry matter, but no conversion to feed has taken place 
        # yet. As such this contains information about the production of animal 
        # products directly but not their feed crops
        imports_no_feed = prov_mat_no_feed[
            prov_mat_no_feed.Consumer_Country_Code == coi_code]
        imports_no_feed = add_cols(imports_no_feed)
        imports_no_feed = imports_no_feed[np.logical_not(
            imports_no_feed.Item.isna())]
        # Animal products have been converted to their respective feed 
        # requirements and most importantly the feed requirements have been 
        # subtracted from the total for each product (i.e. wheat is broken down
        # into wheat for consumption by humans and then each animal product)
        imports_feed = prov_mat_feed[
            prov_mat_feed.Consumer_Country_Code == coi_code]
        imports_feed = add_cols(imports_feed)
        imports_feed = imports_feed[np.logical_not(imports_feed.Item.isna())]   
        animal_product_codes = imports_no_feed[imports_no_feed.Item.isin(
            imports_feed[np.logical_not(
            imports_feed.Animal_Product.isna())
                ].Animal_Product)].Item_Code.unique().tolist()
        def get_value_ratios_01(input_df, level, do_os):
            def get_div(sums, level, row):
                if type(level) == list:
                    div = sums.xs(df.loc[row, level], level = level).values[0]
                else: div = sums[df.loc[row, level]]        
                return div
            df = input_df.copy()
            sums = df.groupby(level).Value.sum()
            for row in df.index:        
                try:
                    rowdat = df.loc[row]
                    pcc = rowdat.Producer_Country_Code
                    div = get_div(sums, level, row)
                    val = rowdat.Value
                    df.loc[row,"Value"] = val / div
                except KeyError: df.loc[row,"Value"] = 0
            df = df[(df.Value >= 0) & (df.Value <= 1)]
            sums = df.groupby(level).Value.sum()
            for row in df.index:
                div = get_div(sums, level, row)
                df.loc[row,"Value"] = df.loc[row,
                                        "Value"]/div
            if offshoring == True and do_os == True:
                sums = df.groupby(level).Value.sum()
            
                for row in df.index:
                   
                    rowdat = df.loc[row]
                    if rowdat.Producer_Country_Code == coi_code and \
                        rowdat.Item != "Cloves":                       
                        try:
                            gaez_name = crop_table.loc[rowdat.Item].GAEZres06
                            offshoreRatio = prod_sum.loc[gaez_name].ratio
                        except KeyError:
                            gaez_name = None
                            offshoreRatio = 1                  
                        df.loc[row,"Value"] = df.loc[row,"Value"] \
                            * offshoreRatio                        
                nsums = df.groupby(level).Value.sum()  
                for row in df.index:
                    rowdat = df.loc[row]
                    ic = rowdat.Item_Code
                    if rowdat.Producer_Country_Code == coi_code:
                        scalar = 1
                    else:
                        diff = get_div(nsums, level, row) \
                            - get_div(sums, level, row)
                        item_val = df[(df.Item_Code == ic) \
                        & (df.Producer_Country_Code != coi_code)].Value.sum()
                        scalar = 1 - (diff / item_val)
                    if scalar < 0:
                        scalar = 0
                    df.loc[row, "Value"] = df.loc[row, "Value"] * scalar
            # Normalise for missing values/items/countries
            sums = df.groupby(level).Value.sum()
            for row in df.index:
                div = get_div(sums, level, row)
                df.loc[row,"Value"] = df.loc[row,
                                        "Value"]/div
            return df
        # filter out fodder crops from feed provmat (anything with an assoc AP) 
        # to get impacts of crops for humans
        imports_feed_crops = imports_feed[imports_feed.Animal_Product.isna()]
        # Need to clean/handle negative values (the paper mentions this). The 
        # following items have -ive values ['Linseed', 'Oilseeds nes', 
        # 'Castor oil seed', 'Poppy seed', 'Artichokes', 'Fruit; fresh nes', 
        # 'Chestnut', 'Rapeseed']
        # They are excluded from analyses in the paper, will exclude them by 
        # default for now.
        imports_feed_crops = imports_feed_crops[imports_feed_crops.Value >= 0]
        imports_feed_crops_ratio = get_value_ratios_01(imports_feed_crops,
                                                       "Item_Code", True)
        imports_feed_crops_ratio.loc[:, "Animal_Product"] = None
        # filter nofeed to just animals to get direct AP impacts 
        imports_no_feed_anim = imports_no_feed[imports_no_feed.Item_Code.isin(
            animal_product_codes)]
        imports_no_feed_anim_ratio = get_value_ratios_01(imports_no_feed_anim,
                                                          "Item_Code",True)
        imports_no_feed_anim_ratio.loc[:,"Animal_Product"] = "Primary"
        # animal products converted into feed to get indirect AP impacts
        # imports_feed_feed = imports_feed[np.logical_not(
        #     imports_feed.Animal_Product.isna())]
        # imports_feed_feed_ratio = get_value_ratios_01(
        #     imports_feed_feed,"Animal_Product_Code",False)
        human_consumed_imports = pd.concat([imports_feed_crops_ratio,
                                            imports_no_feed_anim_ratio])
        # feed_consumed_imports = imports_feed_feed_ratio
        return human_consumed_imports
    human_consumed_imports = \
        import_ratios(  prov_mat_feed,
                        prov_mat_no_feed, 
                        coi_code)
    
    
    #%% reqs for doing provenance calc
    file_reqs = ["content_factors_per_100g.xlsx", "primary_item_map_feed.csv", 
                 "weighing_factors.csv"]
    try:
        factors = pd.read_excel(data_utils.file_list(
            search=[datPath, file_reqs[0]])[0], skiprows=1)
        item_map = pd.read_csv(data_utils.file_list(
            search=[datPath, file_reqs[1]])[0], encoding = "latin-1")
        weighing_factors = pd.read_csv(data_utils.file_list(search=[
            datPath, file_reqs[2]])[0], encoding = "latin-1")
    except IndexError:
        sys.exit(f"Cannot find {file_reqs} in {datPath}")
    
    #%%
    def fs_provenance(fs, fserr):
        """
        Parameters
        ----------
        fs : dataframe
            domestic supply quantity (tonnes) for a single year.
        Returns
        ----------
        cons_prov : provenance of food for direct consumption (crops + animals)
                    countries * products
        feed_prov : animal products converted to feed requirement and respective
                    crop provenance (countries * feed products)
        """
        df_hc = fs.copy()
        df_hc_err = fserr.copy()
        for row in df_hc.iterrows():
            CPC_item_code = row[1]["Item Code"]
            item_name = row[1].item_name
            FAO_code = row[1].FAO_code
            FAO_name_primary = item_map[
                item_map["FAO_code"]==FAO_code].FAO_name_primary
            primary_item_code = item_map[
                item_map["FAO_code"]==FAO_code].primary_item   
            if len(primary_item_code) != 0:
                primary_item_code = primary_item_code.values[0]
                if primary_item_code == 254:
                    print(item_name)
                    print(df_hc[df_hc.item_name == item_name].Value)
                FAO_name_primary = FAO_name_primary.values[0]
                df_hc.loc[row[0], "primary_item"] = FAO_name_primary
                df_hc.loc[row[0], "primary_item_code"] = primary_item_code
                df_hc_err.loc[row[0], "primary_item"] = FAO_name_primary
                df_hc_err.loc[row[0], "primary_item_code"] = primary_item_code
                item_dm = factors[factors[
                    "Item Code"] == FAO_code].dry_matter.values[0]
                try:
                    primary_dm = factors[factors[
                        "Item Code"] == primary_item_code].dry_matter.values[0]
                    ratio = primary_dm / item_dm
                    if ratio == np.inf:
                        df_hc = df_hc[np.logical_not(df_hc[
                            "Item Code"]==CPC_item_code)]
                        df_hc_err = df_hc_err[np.logical_not(df_hc_err[
                            "Item Code"]==CPC_item_code)]
                        # reject.append([item_name, "no_primary"])
                    else: 
                        df_hc.loc[row[0], "ratio"] = ratio
                        df_hc_err.loc[row[0], "ratio"] = ratio
                except IndexError:
                    # reject.append([item_name, "no_dm"])
                    df_hc = df_hc[np.logical_not(df_hc["Item Code"]==
                                                 CPC_item_code)]
                    df_hc_err = df_hc_err[np.logical_not(df_hc_err["Item Code"]==
                                                 CPC_item_code)]
        #     else: reject.append([item_name, "aggregate_or_notindf"])
        # reject_df = pd.concat([reject_df, 
        #                        pd.DataFrame(reject, columns=["item_name",
        #                                                      "cause"])])
        df_hc = df_hc[np.logical_not(df_hc.ratio.isna())]
        df_hc_err = df_hc_err[np.logical_not(df_hc_err.ratio.isna())]
        df_hc["value_primary"] = df_hc.Value / df_hc.ratio
        primary_consumption = df_hc.groupby(
            "primary_item_code").value_primary.sum()
        primary_consumption = primary_consumption.reset_index()
        primary_consumption.loc[:, "item_name"] = [
            item_code_to_product(code) for \
            code in primary_consumption.primary_item_code]   
        for pi_code in primary_consumption.primary_item_code:
            dat = np.array(df_hc_err[df_hc_err.primary_item_code == pi_code].Value)
            primary_consumption.loc[primary_consumption.primary_item_code==pi_code,
                                    "value_primary_err"] = np.sqrt((dat**2).sum())
        
        # provenance for human consumption
        print("Calculating human consumed provenance")
        cons_prov = pd.DataFrame()
        for row in primary_consumption.iterrows():
            primary_item_code = row[1].primary_item_code
            value_primary = row[1].value_primary
            value_primary_err = row[1].value_primary_err
            import_ratios = human_consumed_imports[
                human_consumed_imports.Item_Code == primary_item_code]
            imports = import_ratios.copy()
            if len(import_ratios) == 0:
                pass
            else:
                prov = import_ratios.Value * value_primary
                prov_err_guesstimate = 0.0
                prov_err = prov * prov_err_guesstimate
                imports["provenance"] = prov
                if prov.sum() > 0 and value_primary > 0:
                    imports["provenance_err"] = prov * np.sqrt((prov_err/prov)**2\
                                        + (value_primary_err/value_primary)**2)
                cons_prov = pd.concat([cons_prov, imports])
        
        # provenance of feed
        primary_consumption_anim = primary_consumption[
            primary_consumption.primary_item_code.isin(
                weighing_factors.Item_Code)]
        feed_prov = pd.DataFrame()
        # get animal product
        print("Calculating feed provenance")
        for row in primary_consumption_anim.iterrows():
            primary_item_code = row[1].primary_item_code
            value_primary = row[1].value_primary
            value_primary_err = row[1].value_primary_err
            item_name = row[1].item_name
            feed_conv = weighing_factors[
                weighing_factors.Item_Code==primary_item_code][
                    "Weighing factors"]
            feed_conv = feed_conv.values[0]
            source_countries = human_consumed_imports[
                human_consumed_imports.Item_Code == primary_item_code]
            # get countries that produce the animal product
            for rowx in source_countries.iterrows():
                cRatio = rowx[1].Value
                country_code = rowx[1].Producer_Country_Code
                country_name = rowx[1].Country_ISO
                cVal = value_primary * cRatio
                cVal_err = value_primary_err * cRatio
                # where do they get their feed from?
                dfx = prov_mat_feed[
                    (prov_mat_feed.Animal_Product_Code==primary_item_code)\
                        &(prov_mat_feed.Consumer_Country_Code==country_code)]
                dfx = dfx[(dfx.Value > 0)&(np.logical_not(dfx.Value.isna()))]
                dfx.loc[:, "Value"] = dfx.loc[:, "Value"] / dfx.loc[:, "Value"].sum()
                if feed_conv == 0: pass
                else:
                    prov_rat = dfx.Value * feed_conv
                    prov_rat_err = prov_rat * prov_err_guesstimate
                    prov = prov_rat * cVal
                    dfx["provenance"] = prov
                    if prov.sum() > 0 and cVal > 0:
                        dfx["provenance_err"] = prov * np.sqrt((prov_rat_err/prov_rat)**2\
                                                               +(cVal_err/cVal)**2)
                    dfx["Country_ISO"] = [area_code_to_iso(code) for code in dfx.Producer_Country_Code]
                    dfx["Item"] = [item_code_to_product(code) for code in dfx.Item_Code]
                    dfx["Animal_Product"] = item_name
                    feed_prov = pd.concat([feed_prov, dfx])
        return cons_prov, feed_prov
    cons_prov, feed_prov = fs_provenance(fs, fserr)
    cons_prov = cons_prov[(cons_prov.Value > 1E-8)&(cons_prov.provenance > 0)]
    cons_prov.to_csv(os.path.join(scenPath, "human_consumed.csv"))
    feed_prov = feed_prov[(feed_prov.Value > 1E-8)&(feed_prov.provenance > 0)]
    feed_prov.to_csv(os.path.join(scenPath, "feed.csv"))
    return cons_prov, feed_prov
