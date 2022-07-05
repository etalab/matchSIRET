# -*- coding: utf-8 -*-
"""
Cleaner pour les noms d'entreprises.
"""
from jocas_match_occupation.core import StringCleaner
from jocas_match_occupation.core import Lemmatizer
from jocas_match_occupation import JobOffersTitleCleaner
import re

class FirmLemmatizer(Lemmatizer):
    
    def __init__(self):
        self.firm_cleaner = FirmCleaner()
        lemmas_list = [
            {
                "agglo" : "agglomération",
                "soc" : "société",
                "synd" : "syndicat",
                "ctre" : "centre",
                "hosp" : "hospitalier",
                "dep" : "departemental",
                "asso" : "association",
                "feder" : "federation",
                "gpt" : "groupement",
                "ime" : "institut medico educatif",
                "instit" : "institut",
                "inst" : "institut",
                "sm" : "syndicat mixte",
                "ephad" :"ehpad",
                "ets":"etablissement",
                "intercom" : "intercommunal",
                "csc" : "centre socio culturel",
                "mjc": "maison des jeunes et de la culture",
                "mfr" : "MAISON FAMILIALE RURALE",
                "cpam": "caisse primaire d'assurance maladie",
                }
            ]
        lemmas_expr = {
            "comm com" : "communauté de communes",
            "com com" : "communauté de communes",
            "communaute com" : "communauté de communes",
            "conseil departemental"  : "département",
            "conseil régional"  : "région",
            "caisse primaire assur" : "caisse primaire d'assurance maladie",
            "dir dep" : "direction departementale",
            "dir dpt" : "direction departementale",
            "dir reg" : "direction régionale",
            "ets pub" : "etablissement public",
            "^sce" : "service",
            "^mairie" :"commune",
            "^ass" : "association",
            "^coop" : "coopérative",
            }
        super().__init__(lemmas_list, None, self.firm_cleaner, lemmas_expr)
        
    def clean_replace(self, firm):
        firm_clean = self.firm_cleaner.clean_firm(firm)
        return self.lemmatize_str(
            firm_clean, drop_duplicate=False, clean=False
            )
            

class FirmCleaner(StringCleaner):
    
    def __init__(self):
        # replace_infirst = {"l'":" ", "d'":" "}
        stopwords = [
            "sarl", "earl", "gmbh", "eurl", "sprl", "sas", "sel", "eirl", 
            "cse", 
            "scea", "scev", # société exploitation agricole/viticole
            "scp", # société civile professionnelle
            "gfa", # groupement agricole
            "sci", "scm", "sa", "cfl", "snc", "ei", 
            "sn", "selarl", "sca", "scop", "scs", "sasu", "siege",
            "le", "la", "les", "de", "des", "du"
            # "soc civile"
            ]
        words = ['entreprise', 'groupe', "ste", "entr", "ent", "entrep"]
        gender = ["monsieur", "madame", "mr", "mme", "m"]
        titles = ["dr", "docteur"]
        starting_words = ['^' + words for words in titles + gender + words]
        punctuation = ["\,", "\/", "\*", "\"", "-", "&"]#, "'"]
        # Add location remover
        ### Load ressources - Location
        # from jocas_match_occupation.ressources_txt.FR.cleaner.location import (
        #     loc_departments, loc_countries, loc_regions, loc_others,
        #     loc_replace_infirst
        #     )
        # remove_words = loc_regions + loc_countries
        
        super().__init__(
            stopwords=stopwords+starting_words, punctuation=punctuation,
            # remove_words = remove_words
            )
        
    def clean_firm(self, text):
        text = re.sub("\s+\'\s+", "'", text)
        # remove "l'" and "d'" in first + replace ' by none
        clean_txt = re.sub("\b[lL]'|\b[dD]'", " ", text)
        clean_txt = re.sub("'", "", clean_txt)
        # Enlever les points
        clean_txt = re.sub('\.', '', clean_txt)
        # Concaténer les acronymes
        clean_txt = self.merge_accronyms(clean_txt)
        # Nettoyage classique
        clean_txt = self.clean_str(clean_txt, digits=False)
        # Enlever ce qu'il y a entre parenthèses
        clean_txt = self.remove_brackets(clean_txt)
        # Enlever les l et d seuls
        clean_txt = re.sub("\\b[d|l]\\b", '', clean_txt)
        # Enlever les numéros de téléphone
        clean_txt = re.sub('\d{10,}', "", clean_txt)
        # Normalisation des espaces
        clean_txt = re.sub('^\s+|\s+$', '', clean_txt)
        clean_txt = re.sub('\s+', ' ', clean_txt)
        return clean_txt
    
    def merge_accronyms(self, text):
        # Probems with space at edge
        text = ' ' + text + ' '
        text = re.sub('(?<=\s\w)\s(?=\w\s)', '', text)
        text = re.sub('^\s|\s$', '', text)
        return text
    
    def remove_brackets(self, text):
        text = re.sub('\(.*\)', '', text)
        return text
    
#%%
# names = [
#   "ADHAP 38", "AINTÉRIM", "ADECCO  CHATEAU", "GESTI GROUPE COGESER, TOULOUSE",
#   "**ALPAE CONSEIL**", '"ACR MEDIA"', "SUP'INTERIM 88", "RH-TT",
#   "S.O.S. VILLAGES D'ENFANTS", "COMPLEA/ASSISTANCE DEPENDANCE",
#   "3.I.D (DECONTAMINATION)", "DR RONCHINI CATHERINE", 
#   "GROUPE ALTERNANCE ROCHEFORT", "I D F LES COMPAGNONS",
#   "CHAMPAGNE DESBOEUFS&FILS",
#   "ASSOCIATION FRANCOPHONE DES GLYCOGENOSES (COMITE D'ENTRAIDE)",
# "interim & co", "adwork's", "l'auberge de jeunesse",
# "ZWILLER S.A. / HYPERBURO", "L ' AUBERGE",
# "mc donald s branges",
# "communaute d agglomeration"
#   ]
# fc = FirmCleaner()
# for name in names:
#     print(fc.clean_firm(name))