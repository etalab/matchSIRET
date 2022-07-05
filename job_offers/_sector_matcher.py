# -*- coding: utf-8 -*-
"""
Class to match csv file by sector.
"""
from elasticsearch import Elasticsearch
from collections import Counter

class ElasticSectorMatcher:
    
    def __init__(self, index_name='base_sirene_4', host="localhost:9200"):
        self.index_name = index_name
        self.client = Elasticsearch(host)
        self.niv_dict = {"NIV5":"naf", "NIV1":"naf_A21", "NIV2":"naf_A88"}
        
    def get_filter(self, firm, on='noms', employeur=True):
        if on == 'noms':
            filter_ = [{"term": {"noms.keyword": firm}}]
        elif on == "sigle":
            filter_ = [{"term": {"sigle.keyword": firm}}]
        elif on == "sigle_clean":
            filter_ = [{"term": {"sigle_clean.keyword": firm}}]
        elif on == "noms_clean":
            filter_ = [{"term": {"noms_clean.keyword": firm}}]
        elif on == "prenom_nom":
            filter_ = [{"term": {"prenom_nom": firm}}]
        elif on == "prenom_nom_clean":
            filter_ = [{"term": {"prenom_nom_clean.keyword": firm}}]
        else:
            raise ValueError("Unknow matching names %s" %on)
        if employeur:
            filter_ += [{'term': {"carac_empl": 'O'}}]
        return filter_
        
    def exact_match_all(self, firm, on='noms_clean', employeur=True):#, filter_={'in_scope': True}):
        filter_ = self.get_filter(firm, on, employeur)
        body = {
            'query': {
                'bool': {
                    "filter": filter_
                    },
                },
            "size": 10000,
            }
        return self._get_response(body)
    
    def exact_match_most_recent(self, firm, on='noms', employeur=True):
        filter_ = self.get_filter(firm, on, employeur)
        body = {
            "query": {
                'bool': {
                    "filter": filter_
                    },
                },
            "size": 10000,
            "sort": [
                {
                  "date_creation": {
                    "order": "desc"
                  }
                }
                ]
            }
        return self._get_response(body)
    
    def exact_match_vote(
            self, firm, niv, on, employeur, seuil=0
            ):
        # Les aggs sont très lentes pour l'instant ...
        # body = {
        #     "query": {
        #         'bool': {
        #             'must': [{'match_phrase': {'noms': firm}}],
        #             "filter": [{ "term": filter_}]
        #             },
        #         },
        #     "size": 10000,
        #     "aggs": {
        #     "attribCount": {
        #         "terms": {
        #             "field": "naf.keyword",
        #             "size": 1000,
        #             }
        #         }
        #     }
        #     }
        res = self.exact_match_all(firm, on, employeur)
        return self.vote_on_match(res, niv, seuil)
    
    def vote_on_match(self, res, niv, seuil=0):
        NAF = None  # Init
        list_echo = res['hits']['hits']
        found = len(list_echo) # How many match
        if found > 10000:
            print("Warning: increase results size.")
        if found == 0:
            return [found, NAF]
        # Count frequence
        counter = Counter()
        for results in res['hits']['hits']:
            naf = results['_source'][niv]
            if naf in counter.keys():
                counter[naf] = counter[naf] + 1 
            else:
                counter[naf] = 1
        top = counter.most_common()
        score = top[0][1] / len(list_echo)
        if len(top) == 1 and score >= seuil:
            NAF = counter.most_common()[0][0]
        elif score >= seuil:
            if top[0][1] != top[1][1]: # No equality allowed
                NAF = counter.most_common()[0][0]
        return [found, NAF]

    def _get_response(self, body):
        return self.client.search(
            index=self.index_name, 
            body=body,
            request_timeout=30
            )
    
    def exact_match(
            self, firm, mode, niv='NIV1', on='noms', employeur=True,
            seuil=0
            ):
        """
        Retourne un unique secteur ou aucun, selon la méthode de matching.
        Retourne une seule NAF ou aucune si ambiguité.
        """
        niv = self.niv_dict[niv]
        if mode == 'unique':
            res = self.exact_match_all(firm, on, employeur)
            list_echo = res['hits']['hits']
            if len(list_echo) == 1:
                return [len(list_echo), list_echo[0]["_source"][niv]]
            else:
                return [len(list_echo), None]
        # elif mode == 'most_recent':
        #     res = self.exact_match_most_recent(firm, on, employeur)
        #     list_echo = res['hits']['hits']
        #     if len(list_echo) >= 1:
        #         return list_echo[0]["_source"][niv]
        #     else:
        #         return None
        elif mode == "vote":
            res = self.exact_match_vote(firm, niv, on, employeur, seuil)
            return res
            # return res['aggregations']['attribCount']['buckets']
        else:
            print("Mode not found (unique, most_recent or vote).")
            return None
        
    def approx_match(self, firm, niv):
        # niv = self.niv_dict[niv]
        niv = self.niv_dict[niv]
        list_echo = self._approx_match(firm)
        if len(list_echo) == 0:
            return None
        if len(list_echo) == 1:
            return list_echo[0]['_source'][niv]
        else:
            return None
        # if len(list_echo) > 0:
        #     return list_echo[0]["_source"][self.niv_dict[niv]]
        # else:
        #     return None
        if len(list_echo) > 10000:
            print("Warning: increase results size.")
        counter = Counter()
        for results in list_echo:
            naf = results['_source'][niv]
            # if results['_score'] > 20:
            #     return naf
            if naf in counter.keys():
                counter[naf] = counter[naf] + 1 
            else:
                counter[naf] = 1
        top = counter.most_common()
        if len(top) == 0:
            return None
        if len(top) > 1: # make sure there is no equality
            if top[0][1] == top[1][1]:
                return None
        return counter.most_common()[0][0]
    
    def _fuzzy_match(self, firm, fuzziness=1, employeur=True):
        body = {
            'query': {
                'fuzzy':{
                    "noms_clean.keyword":{
                        "value":firm,
                        "fuzziness":fuzziness
                        }
                    }
                },
            "size": 100
            }
        return self.client.search(
            index=self.index_name, 
            body=body,
            request_timeout=30
            )
    
    def fuzzy_match(self, firm, niv, fuzziness=1, seuil=1):
        res = self._fuzzy_match(firm, fuzziness)
        niv = self.niv_dict[niv]
        return self.vote_on_match(res, niv, seuil)
    
    def term_match(self, firm, niv, seuil=15):
        res = self._term_match(firm)
        niv = self.niv_dict[niv]
        # list_echo = res['hits']['hits']
        # if len(list_echo) == 0:
        #     return None
        # else:
        #     result = list_echo[0]
        #     if result['_score'] > seuil:
        #         return result['_source'][niv]
        return self.vote_on_match(res, niv, seuil)
    
    def _term_match(self, firm):
        body = {
            'query': {
                'match':{
                    "noms_clean":{
                        "query":firm,
                        # "operator": "or",
                        # 'fuzziness':1
                        }
                    }
                },
            # "size": 10000
            }
        return self.client.search(
            index=self.index_name, 
            body=body,
            request_timeout=30
            )

    def _approx_match(self, firm, filter_={'in_scope': True}):
        # body = {
        #     'query': {
        #         'bool': {
        #             'must': [{'match': {'noms': firm}}],
        #             "filter": [
        #                 { "term": {"carac_empl.keyword": 'O'}}
        #                 ]
        #             },
        #         }
        #     }
        body = {
            'query': {
                'fuzzy':{
                    "noms_clean.keyword":{
                        "value":firm,
                        "fuzziness":1
                        }
                    }
                
                # 'bool': {
                    # 'must': [{ "match": { "noms_clean": { "query": firm, "operator": "and", "fuzziness":2}}}],
                    # 'must': [{'match': {'prenom_nom_clean': firm}}],
                    # "filter": [
                    #     { "term": {"carac_empl.keyword": 'O'}}
                    #     ]
                    # 'must': [{'match': {'siren': firm}}]
                    #'must': [{'match': {'noms_clean': firm}}]
                    # },
                }
            }
        res = self.client.search(
            index=self.index_name, 
            body=body,
            request_timeout=30
            )
        return res['hits']['hits']
    
    def match_siren(self, firm, filter_={'in_scope': True}):
        body = {
            'query': {
                'bool': {
                    'must': [{'match': {'siren': firm}}],
                    },
                }
            }
        res = self.client.search(
            index=self.index_name, 
            body=body,
            request_timeout=30
            )
        return res['hits']['hits']
    
    def match_siret(self, firm, filter_={'in_scope': True}):
        body = {
            'query': {
                'bool': {
                    'must': [{'match': {'siret': firm}}],
                    },
                }
            }
        res = self.client.search(
            index=self.index_name, 
            body=body,
            request_timeout=30
            )
        return res['hits']['hits']
