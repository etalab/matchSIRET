# -*- coding: utf-8 -*-
"""
Sirene columns conversion.
"""

sirene_cols = {
    "entreprise" : {
        'dateDebut':"date_debut",
        'siren':'siren',
        'activitePrincipaleUniteLegale':'naf', 
        'nomenclatureActivitePrincipaleUniteLegale':'nomenclature_naf',
        "etatAdministratifUniteLegale" : 'etatadmin',
        "caractereEmployeurUniteLegale": 'carac_empl',
        "denominationUniteLegale": "nom1",
        "denominationUsuelle1UniteLegale" : "nom2",
        "denominationUsuelle2UniteLegale" : "nom3",
        "denominationUsuelle3UniteLegale": "nom4",
        'dateCreationUniteLegale': 'date_creation',
        "sigleUniteLegale":"sigle",
        "prenomUsuelUniteLegale":"prenom",
        "nomUniteLegale":"nom",
        "nomUsageUniteLegale":"nom_usage"
        },
    "etab" : {
        'dateDebut':"date_debut",
        'siret': 'siret',
        'siren':'siren',
        'activitePrincipaleEtablissement':'naf', 
        'nomenclatureActivitePrincipaleEtablissement':'nomenclature_naf',
        "etatAdministratifEtablissement" : 'etatadmin',
        "caractereEmployeurEtablissement": 'carac_empl',
        "denominationUsuelleEtablissement": "nom1",
        "enseigne1Etablissement" : "nom2",
        "enseigne2Etablissement" : "nom3",
        "enseigne3Etablissement": "nom4",
        "dateCreationEtablissement":"date_creation",
        "codePostalEtablissement":"postal_code",
    }
}

sirene_files = {
    "entreprise":["StockUniteLegale_utf8.zip", "StockUniteLegale_utf8.csv"],
    "etab":["StockEtablissement_utf8.zip", "StockEtablissement_utf8.csv"]
    }