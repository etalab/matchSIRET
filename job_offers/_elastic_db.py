# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch, helpers
import csv
from io import TextIOWrapper
import os
import pandas as pd
import zipfile
from datetime import datetime
from jocas_sector.core._sirene_cols import sirene_cols, sirene_files
from jocas_sector.tools._convert_naf import (
    convert_naf, get_naf_hierarchy, get_dict_naf
    )
from jocas_sector.core._firm_cleaner import FirmLemmatizer

class ElascticSirene():
    
    def __init__(self, index_name, host="http://localhost:9200"):
        # Connect to elastic search cluster (must be launched //!\\ )
        self.host = host
        self.es = Elasticsearch(host)
        # Define index name
        self.index_name = index_name
        self.firm_cleaner = FirmLemmatizer()
        
    def create_index(self, index=None):
        if index is None:
            index = self.index_name
        body = {}
        body['mappings'] = self._mapping()
        body["settings"]= {
	        "refresh_interval" : "30s",
	        "number_of_replicas": 0
	    }
        # Check if index already exists
        exits = self.es.indices.exists(index=index)
        if exits:
            print("***Please delete index before using create.***")
            return
        # Create index
        self.es.indices.create(index=index, ignore=400, body=body)
        
    def index_sirene_data(self, folder, doc_type, output_csv=None):
        """Create an index from a csv file."""
        # Index new data
        helpers.bulk(
                self.es,
                self.load_sirene_data(folder, doc_type),#, output_csv=output_csv), 
                index=self.index_name,
                chunk_size=400
                )
        
    def load_sirene_data(
            self, folder, doc_type, allow_out_scope=False, output_csv=None
            ):
        """
        Load Sirene data (last current data) into Elasticsearch database.
        * allow_out_scope : allow observation out of scope (cessées avant la date 
                            de début, non employeurs...)
        """
        # Init
        min_dt = datetime.strptime("2017-01-01", "%Y-%m-%d")
        # TODO check if doc type is 'entreprise' or 'etab'
        # Get corrext files and colums names
        usecols = sirene_cols[doc_type]
        zip_file = os.path.join(folder, sirene_files[doc_type][0])
        file = sirene_files[doc_type][1]
        id_col = 'siret' if doc_type == 'etab' else 'siren'
        
        # File to convert naf
        dict_NIV5_NIV1 = get_dict_naf(from_="NIV5", to_="NIV1")
        dict_NIV5_NIV2 = get_dict_naf(from_="NIV5", to_="NIV2")
        
        # Get records of all names
        all_names = pd.DataFrame()
        
        # Count valid firms
        n_ok, n_total = 0, 0
        start = datetime.now()
        
        # Read data and index them in elastic search
        zip_ = zipfile.ZipFile(zip_file) 
        with zip_.open(file, mode='r') as f:
            reader = csv.DictReader(TextIOWrapper(f, encoding='utf-8'))
            while True:
                try:
                    row, i = next(reader), reader.line_num
                    # if i == 300000:
                    #      break
                    if i % 100000 == 0:
                        end = datetime.now()
                        print("Nombre d'observations analysées : %s" %i)
                        pct_ok = round(n_ok * 100 / 100000, 2)
                        print("Dont indéxées en pct : %s" %pct_ok)
                        time = (end-start).total_seconds()
                        v = round(n_ok / time, 0)
                        print("Vitesse en doc/s %s" %v)
                        print("Nombre total %s" %n_total)
                        n_ok = 0
                        start = datetime.now()
                    # Change col names
                    row = dict(
                        (usecols[name], val) 
                        for name, val in row.items()
                        if name in usecols.keys()
                        )
                    
                    # _id = row[id_col] # L'identifiant est Siren ou Siret
                    # Ignorer les dates de début inconnues, ces observations
                    # ne nous concernent pas cf docu
                    if row["date_debut"] == "":
                        continue
                    # Is in scope 
                    date_debut_dt = datetime.strptime(row["date_debut"], "%Y-%m-%d")
                    row['in_scope'] = self.is_in_scope(row, min_dt, date_debut_dt)
                    if (not row['in_scope']) and (not allow_out_scope):
                        continue
                    
                    # Restructure variables
                    names = self.structure_row(row, dict_NIV5_NIV1, dict_NIV5_NIV2)
                    if output_csv is not None:
                        all_names = all_names.append(names)

                    # On garde l'observation la plus récente sur la période,
                    # en ajoutant les infos qui ont changé au fur et à mesure
                    # exists = self.es.exists(
                    #     index=self.index_name, 
                    #     id=_id
                    #     )
                    # # if exists:
                    # if exists and (allow_out_scope or row['in_scope']):
                    #     old_row = self.get_doc(_id)
                    #     old_date = datetime.strptime(old_row["date_debut"], "%Y-%m-%d")
                    #     # On garde le plus récent et on ajoute les noms possibles
                    #     noms = old_row['noms'] + row['noms']
                    #     noms = list(set(noms))
                    #     if old_date > date_debut_dt: # Update current doc
                    #         res = self.es.update_field_by_id(_id, 'noms', noms)
                    #         print("Update data.")
                    #     else: # Replace doc
                    #         row['noms'] = noms
                    #         # delete old and reindex
                    #         row.update({
                    #             "doc_type": doc_type,
                    #             "_id": _id,
                    #             "noms": noms
                    #             })
                    #         print("Replace data: %s" %_id)
                    #         yield row
                    # elif (allow_out_scope or row['in_scope']): # New data
                    if (allow_out_scope or row['in_scope']):
                        if (len(row['prenom_nom']) > 0) or (len(row['noms']) > 0):
                            row.pop('in_scope')
                            row.update({
                                    "doc_type": doc_type,
                                    # "_id": _id
                                    })
                            n_ok += 1
                            n_total += 1
                            yield row
                    else:
                        pass
                except csv.Error as e:
                    print("line: {}, error: {}".format(reader.line_num, e))
                except StopIteration:
                    break
        if output_csv is not None:
            all_names.to_csv(
                output_csv, sep=";", encoding='utf-8-sig', index=False
                )
    
    def is_in_scope(self, row, min_dt, date_debut_dt):
        # L'observation est-elle hors champ ?
        # names = ['nom1', 'nom2', 'nom3', 'nom4']
        if (row['etatadmin'] == "C") and date_debut_dt < min_dt:
            # entreprise cessée
            return False
        if (row['etatadmin'] == "F") and date_debut_dt < min_dt:
            # etablissement fermé
            return False
        elif (row['nomenclature_naf'] != 'NAFRev2'):
            return False
        # elif row['carac_empl'] == 'N':
        #     return False 
        elif row['naf'] == "00.00Z":
            return False 
        # Aucun nom : possible si entrepreneur 
        # elif all([row[name] == "" for name in names]):
        #     return False
        else:
            return True
    
    def structure_row(self, row, dict_NIV5_NIV1, dict_NIV5_NIV2):
        """Resctructure SIREN observations."""
        # Corriger les dates de création, sinon ça marche pas (approx...)
        if row['date_creation'] == "":
           row['date_creation'] = '1900-01-01'
        # Conversion des niveaux de NAF
        if row["nomenclature_naf"] == 'NAFRev2':
            row['naf_A21'] = convert_naf(
                row['naf'], dict_=dict_NIV5_NIV1, 
                raise_on_false=False
                )
            row['naf_A88'] = convert_naf(
                row['naf'], dict_=dict_NIV5_NIV2, 
                raise_on_false=False
                )
        # Ajout du prenom + nom comme champ possible
        row['prenom_nom']= []
        if 'nom' in row.keys(): # Entreprise seulement
            prenom, nom = row['prenom'], row['nom']
            if row['nom_usage'] != "":
                nom = row['nom_usage']
            if all(x != "" for x in [prenom, nom]):
                row['prenom_nom'] += [prenom + ' ' + nom]
                row['prenom_nom'] += [nom + ' ' + prenom]
            row['prenom_nom'] = list(set(row['prenom_nom']))
            row.pop('nom')
            row.pop('prenom')
            row.pop('nom_usage')
        # Cleaning des noms prenoms
        row['prenom_nom_clean'] = [
            self.firm_cleaner.clean_replace(x) for x in row['prenom_nom']
            ]
        # Merge des noms
        row['noms'] , row['noms_clean'] = [], []
        names = ['nom1', 'nom2', 'nom3', 'nom4', 'sigle']
        for name in names:
            if name in row.keys():
                nom = row[name]
                if nom != "":
                    row['noms'] = row['noms'] + [nom]
                clean_nom = self.firm_cleaner.clean_replace(nom)
                if clean_nom != "":
                    row['noms_clean'] = row['noms_clean'] + [clean_nom]
                row.pop(name)
        row['noms'] = list(set(row['noms']))
        row['noms_clean'] = list(set(row['noms_clean']))
        if 'postal_code' not in row.keys():
            pass
        elif row['postal_code'] != "":
            row['dpt_code'] = row['postal_code'][0:2]
        else:
            pass
        # Unused infos
        row.pop('nomenclature_naf')
        infos = pd.DataFrame({
            'noms':row['noms_clean'], 
            'naf_A88':row['naf_A88'], 
            'naf_A21':row['naf_A21']
            })
        return infos
    
    def delete_index(self):
        self.es.indices.delete(index=self.index_name, ignore=[400, 404])

    def get_mapping(self, index=None):
        if index is None:
            index = self.index_name
        return self.es.indices.get_mapping(index)[index]
    
    def get_variables(self):
        mapping = self.get_mapping()
        variables = mapping['mappings']['properties']['doc']['properties'].keys()
        return list(variables)
    
    def get_mapping_var(self, var):
        mapping = self.get_mapping()
        return mapping['mappings']['properties']['doc']['properties'][var]
    
    def edit_mapping(self, var, new_mapping={'type': 'keyword'}, mapping=None):
        if mapping is None:
            mapping = self.get_mapping()
        mapping['mappings']['properties'][var] = new_mapping
        return mapping
    
    def set_to_keywords(self, vars_, mapping=None):
        # vars_ = [
        #     'siret', 'siren', 'postal_code', 'naf_A88', 'naf_A21', 'naf', 
        #     'etatadmin', 'dpt_code', 'doc_type', 'carac_empl'
        #     ]
        for var in vars_:
            mapping = self.edit_mapping(var, mapping=mapping)
        return mapping
    
    def get_doc(self, _id):
        """
        Get value of doc by ID (SIREN or SIRET).
        """
        body = {
               "query": {"bool": {
                       "must": [{"match" : {"_id" : _id}}]
                       }}
               }
        res = self.es.search(index=self.index_name, body=body)
        infos = res['hits']['hits'][0]['_source']
        return infos

    def get_all_doc(self,):
        """
        Get value of doc by ID (SIREN or SIRET).
        """
        body = {
                "query": {
                    "match_all": {}
                }
            }
        res = self.es.search(index=self.index_name, body=body)
        infos = res['hits']['hits']
        return infos

    def update_field_by_id(self, id_, field, new_value):
        """Change field value of a document."""
        body = {
            "doc":{
                field : new_value
                }
            }
        res = self.es.update(index=self.index_name, id=id_, body=body)
        return res
    
    def _mapping(self):
        return {
                'properties': {
                    'carac_empl': {'type': 'keyword'},
                    'date_creation': {'type': 'date'},
                    'date_debut': {'type': 'date'},
                    'doc_type': {'type': 'keyword'},
                    'dpt_code': {'type': 'keyword'},
                    'etatadmin': {'type': 'keyword'},
                    'in_scope': {'type': 'boolean'},
                    'naf': {'type': 'keyword'},
                    'naf_A21': {'type': 'keyword'},
                    'naf_A88': {'type': 'keyword'},
                    'noms': {
                        'type': 'text',
                        'fields': {
                            'keyword': {
                                'type': 'keyword', 'ignore_above': 256}
                            }
                        },
                    'noms_clean': {
                        'type': 'text',
                        'fields': {
                            'keyword': {
                                'type': 'keyword', 'ignore_above': 256}
                            }
                        },
                    'postal_code': {'type': 'keyword'},
                    'siren': {'type': 'keyword'},
                    'siret': {'type': 'keyword'},
                    'prenom_nom': {
                        'type': 'text',
                        'fields': {
                            'keyword': {
                                'type': 'keyword', 'ignore_above': 256}
                            }
                        },
                    'prenom_nom_clean': {
                        'type': 'text',
                        'fields': {
                            'keyword': {
                                'type': 'keyword', 'ignore_above': 256}
                            }
                        }
                }
            }
    
