# -*- coding: utf-8 -*-
"""
Classe pour matcher les offres Pôle emploi et évaluer le matching.
"""

"""
-- outputs
   + api_poleemploi
       + 2020-01
           + 20200103_offers_pred.csv
           + 20200104_offers_pred.csv
           + ...
"""
from datetime import datetime
import pandas as pd
import re
import os
from jocas_sector.core._sector_matcher import ElasticSectorMatcher
from jocas_sector.tools._convert_naf import match_digits, convert_naf_df
from jocas_sector.core._firm_cleaner import FirmCleaner

class JocasMatchSector():
    
    def __init__(self, index):
        self.cleaner = FirmCleaner()
        self.index = index
    
    # def match_folder(
    #         self, folder, site, start_date, end_date, output_folder, 
    #         niv="NIV1"
    #         ):
    #     for date in self.get_dates_between(start_date, end_date):
    #         month, day = date[0:7], re.sub('-','', date)
    #         in_file = os.path.join(folder, site, month, day + "_offers.csv")
    #         os.makedirs(os.path.join(output_folder, site, month), exist_ok=True)
    #         out_file = os.path.join(output_folder, site, month, day + "_offers_pred.csv")
    #         # Process data
    #         df = self.enrich_df(in_file)
    #         df.name = df.name.str.upper()
    #         self.excat_match_df(df, niv, on='noms', inplace=True, succesive_modes=['vote'], empl=True)
    #         self.excat_match_df(df, niv, on='sigle', inplace=False, succesive_modes=['vote'], empl=True)
    #         self.excat_match_df(df, niv, on='prenom_nom', inplace=False, succesive_modes=['unique'], empl=False)
    #         self.excat_match_df(df, niv, on='noms', inplace=False, succesive_modes=['vote'], empl=False)
    #         print(self.accuracy(df, niv))
    #         # To csv
    #         df.to_csv(out_file, sep=";", encoding="utf-8-sig", index=False)
    
    def match_df(self, df, niv="NIV1", inplace=True):
        self.excat_match_df(df, niv, on='noms', inplace=inplace, succesive_modes=['vote'], empl=True)
        self.excat_match_df(df, niv, on='sigle', inplace=False, succesive_modes=['vote'], empl=True)
        self.excat_match_df(df, niv, on='prenom_nom', inplace=False, succesive_modes=['unique'], empl=False)
        self.excat_match_df(df, niv, on='noms', inplace=False, succesive_modes=['vote'], empl=False)
    
    def get_names_folder(
            self, folder, site, start_date, end_date, output_folder, 
            niv="NIV1"
            ):
        res = pd.DataFrame()
        for date in self.get_dates_between(start_date, end_date):
            month, day = date[0:7], re.sub('-','', date)
            in_file = os.path.join(folder, site, month, day + "_offers.csv")
            if not os.path.exists(in_file):
                continue
            # Process data
            df = self.enrich_df(in_file)
            df.name = df.name.apply(self.cleaner.clean_firm)
            mask_name = df.name != ""
            df = df.loc[mask_name].copy()
            df.drop(columns=['siren'], inplace=True)
            res = res.append(
                pd.DataFrame(
                    {'n':df.groupby(['name', 'NIV2', 'NIV1']).size()}
                    ).reset_index()
                )
        # To csv
        os.makedirs(os.path.join(output_folder, site), exist_ok=True)
        out_file = os.path.join(output_folder, site,"test_offers.csv")
        groups = pd.DataFrame({'n':res.groupby(['name', 'NIV2', 'NIV1'])['n'].sum()}).reset_index()
        groups.to_csv(out_file, sep=";", encoding="utf-8-sig", index=False)
        return groups
    
    def enrich_df(
            self, file, col_firm="entreprise_nom", col_siren = "entreprise_siren",
            col_secteur = "entrepriseSecteur_NAF88",
            select_col={'partner_status':'False'}
            ):
        """Read df and harmonize infos."""
        
        df = pd.read_csv(
            file, sep=";", encoding='utf-8-sig', dtype=str,
            usecols=[col_firm, col_siren, col_secteur] + list(select_col.keys()),
            na_values='NaN'
            )
        df.fillna("", inplace=True)
        for key, value in select_col.items():
            mask_select = df[key] == value
            df = df.loc[mask_select].copy()
        # Rename columns
        df.rename(
            columns = {col_firm:"name", col_siren:"siren", col_secteur:"NIV2"},
            inplace=True
            )
        # Don't retain empty data
        mask_name = df.name != ""
        mask_sector = df.NIV2 != ""
        df = df.loc[mask_name & mask_sector].copy()
        df = df[["name", "siren", "NIV2"]]
        # Match and convert NAF
        match_digits(df, 'NIV2')
        df = convert_naf_df(df, "NIV2", "NIV1", "NIV2", "NIV1")
        return df
        
    def excat_match_df(
            self, df, niv, inplace=True, incol="name", empl=True,
            on='noms',
            na_value="", seuil=0, 
            succesive_modes=['vote'],#,'most_recent'],
            name = ""
            ):
        outcol = niv + '_pred'
        found = 'found_' + name
        if outcol in list(df) and inplace:
            # Remove old columns
            df.drop(outcol, axis=1, inplace=True)
        # Compute
        esm = ElasticSectorMatcher(index_name=self.index)
        for mode in succesive_modes:
            if outcol not in list(df):
                df[[found, outcol]] = pd.DataFrame.from_records(
                    df[incol].map(
                        lambda x : esm.exact_match(str(x), mode, niv, on, empl, seuil)
                        )
                    )
            else: # Only empty sector
                mask_1 = df[outcol].isna()
                mask_2 = df[outcol] == ""
                mask = mask_1 | mask_2
                df.loc[mask, [found, outcol]] = pd.DataFrame.from_records(
                    df.loc[mask, incol].map(
                        lambda x : esm.exact_match(str(x), mode, niv, on, empl, seuil)
                        ),
                    index=df.loc[mask].index,
                    columns = [found, outcol]
                    )
        df[outcol].fillna(na_value, inplace=True)
        
    def approx_match_df(
            self, df, niv, incol="name", na_value="", del_match=False,
            how='fuzzy', name=""
            ):
        found = 'found_' + name
        outcol = niv + '_pred'
        if outcol in list(df) and del_match:
            # Remove old columns
            df.drop(outcol, axis=1, inplace=True)
            df[outcol] = ""
        elif del_match == True:
            df[outcol] = ""
        # Compute
        esm = ElasticSectorMatcher(index_name=self.index)
        mask_empty, mask_na = df[outcol] == "", df[outcol].isna()
        mask = mask_empty | mask_na
        if how == "fuzzy":
            df.loc[mask, [found, outcol]] = pd.DataFrame.from_records(
                df.loc[mask, incol].map(
                    lambda x : esm.fuzzy_match(str(x), niv)
                    ),
                    index=df.loc[mask].index,
                    columns = [found, outcol]
                )
        else:
            df.loc[mask, [found, outcol]] = pd.DataFrame.from_records(
                df.loc[mask, incol].map(
                    lambda x : esm.term_match(str(x), niv)
                    ),
                    index=df.loc[mask].index,
                    columns = [found, outcol]
                )
        df[outcol].fillna(na_value, inplace=True)
    
    def accuracy(self, df, niv="NIV1"):
        pred_col = niv + '_pred'
        # Filter None data
        df.fillna("" ,inplace=True)
        if len(df) == 0:
            return (1,1)
        mask_match = df[pred_col] != ""
        match_rate = sum(mask_match) / len(df)
        eval_df = df.loc[mask_match].copy()
        if len(eval_df) == 0:
            return (1,1)
        # Compute accuracy
        accuracy = sum(eval_df[pred_col] == eval_df[niv]) / len(eval_df)
        return (accuracy, match_rate)
    
    def weigthed_accuracy(self, df, niv="NIV1", w='n'):
        pred_col = niv + '_pred'
        # Filter None data
        df.fillna("" ,inplace=True)
        if len(df) == 0:
            return (1,1)
        mask_match = df[pred_col] != ""
        match_rate = sum(mask_match*df[w]) / sum(df[w])
        eval_df = df.loc[mask_match].copy()
        if len(eval_df) == 0:
            return (1,1)
        # Compute accuracy
        mask = eval_df[pred_col] == eval_df[niv]
        accuracy = sum(mask*eval_df[w]) / sum(eval_df[w])
        return (accuracy, match_rate)
    
    def accuracy_folder(
            self, output_folder, site, start_date, end_date, niv="NIV1"
            ):
        n, n_match, n_correct = 0, 0, 0
        pred = niv +"_pred"
        for date in self.get_dates_between(start_date, end_date):
            month, day = date[0:7], re.sub('-','', date)
            out_file = os.path.join(output_folder, site, month, day + "_offers_pred.csv")
            df = pd.read_csv(out_file, sep=";", usecols=[niv, pred])
            df.fillna("", inplace=True)
            n += len(df)
            n_correct += sum(df[pred] == df[niv])
            n_match += sum(df[pred] != "")
        accuracy = n_correct / n_match
        match_rate = n_match / n
        return (accuracy, match_rate)
    
    def match_siren_df(self, df):
        pass
    
    def get_dates_between(self, start_date, end_date, format_dt="%Y-%m-%d"):
        """Get list of dates between start and end dates."""
        end = datetime.strptime(end_date, "%Y-%m-%d")
        start = datetime.strptime(start_date, "%Y-%m-%d")
        dates = pd.date_range(start, end, freq='d')
        return list([datetime.strftime(date, format_dt) for date in dates])
