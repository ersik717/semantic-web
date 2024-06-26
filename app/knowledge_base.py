import json
import urllib.error
from collections import defaultdict
from importlib import reload

import requests
from SPARQLWrapper import SPARQLWrapper, JSON
import app.db as db
import app.utils as utils

for module in [db, utils]:
    reload(module)


class DBPediaKnowledgeBase:
    _db = db.DB()
    _prop_descr = _db.get_all_property_descr()
    _cached_prop_descr = _prop_descr.copy()
    _basic_entity_class = 'http://www.w3.org/2002/07/owl#Thing'
    # list of meaningless properties for QA system
    _prop_black_list = ['http://dbpedia.org/property/years',
                       'http://dbpedia.org/property/name']

    def __init__(self):
        self._sparql_uri = 'http://dbpedia.org/sparql'
        self._sparql_format = JSON
        self._lookup_uri = 'http://lookup.dbpedia.org/api/search/'

    def search(self, string, cls='', type_='Keyword', max_hits=1):
        url = self._lookup_uri + type_ + 'Search'
        params = {'QueryString': string,
                  'QueryClass':  cls,
                  'MaxHits':     max_hits}
        headers = {'Accept': 'application/json'}
        resp = json.loads(requests.
                          get(url=url, params=params, headers=headers).
                          text)
        if resp['results']:
            res = resp['results'][0]
            uri = res['uri']
            name = res['label']
            description = res['description']
            classes = [cls['uri'] for cls in res['classes']
                       if utils.is_dbpedia_link(cls['uri'])]
            if not classes:
                classes = [self._basic_entity_class]
            return uri, name, description, classes
        else:
            print('No results for <{0}> of class <{1}> (<{2}Search>)'.
                  format(string, cls, type_))
            return None

    def sparql(self, query):
        sparql = SPARQLWrapper(self._sparql_uri)
        sparql.setReturnFormat(self._sparql_format)
        sparql.setTimeout(60)
        sparql.setQuery(query)
        counter = 0
        while counter < 10:
            try:
                return sparql.query().convert()
            except (urllib.error.HTTPError, urllib.error.URLError):
                print('Rerun SPARQL query due to HTTP error.')
                counter += 1

    def get_entity_properties(self, entity_uri, entity_class):
        """
        Fetch properties for the given entity.
        Query example:
        select distinct ?property, ?subject, ?obj
        where {
             ?subject a <http://dbpedia.org/ontology/Place> .
             ?subject ?property ?obj .
             FILTER(?subject=<http://dbpedia.org/resource/Pavlohrad>)
        }
        :param entity_uri: URI of the entity
        :return: dictionary of pairs (property URI, property value)
        """

        # entity_class = 'http://dbpedia.org/ontology/Place'
        query = """
        select distinct ?property, ?subject, ?obj
        where {{
             ?subject a <{0}> .
             ?subject ?property ?obj .
             FILTER(?subject=<{1}>)
        }}
        """
        query_with_values = query.format(entity_class, entity_uri)
        r_json = self.sparql(query_with_values)
        prop_dict = defaultdict(list)
        for spo in r_json['results']['bindings']:
            # Add (property -> value) if property is from DBPedia and thus has description
            if utils.is_dbpedia_link(spo['property']['value']):
                # Add (property -> value) if lang is not defined (for links) or if it is
                # russian or english (thus eliminate 'de', 'jp', ...)
                if 'xml:lang' not in spo['obj'] or spo['obj']['xml:lang'] in ('ru', 'en'):
                    prop_uri = spo['property']['value']
                    prop_value = spo['obj']['value']
                    prop_dict[prop_uri] += [prop_value]
        return prop_dict

    def get_property_descr(self, property_uri):
        if property_uri in self._prop_black_list:
            # Just return empty description
            return ''
        if property_uri in self._cached_prop_descr:
            descr = self._cached_prop_descr[property_uri]
        else:
            print("Fetch property descr from DBpedia:", property_uri)

            rdfs_descr = {'label':   'http://www.w3.org/2000/01/rdf-schema#label',
                          'comment': 'http://www.w3.org/2000/01/rdf-schema#comment'}

            r_json = self.sparql('DESCRIBE <{0}>'.format(property_uri))
            descr_list = []
            for spo in r_json['results']['bindings']:
                # if the given predicate is description (label or comment for ontology/property)
                if spo['p']['value'] in rdfs_descr.values():
                    if spo['o']['lang'] == 'en':
                        descr_list.append(spo['o']['value'])
            descr = ' | '.join(descr_list)

            self._add_to_cached_prop_descr(property_uri, descr)
        return descr

    def _add_to_cached_prop_descr(self, property_uri: str, descr: str):
        self._cached_prop_descr[property_uri] = descr
        self._db.put_property_descr(property_uri, descr)


# 'é'.encode().decode()
# 'é'.encode()
# kdb = DBPediaKnowledgeBase()
# kdb.search('Lenin')
# DBPediaKnowledgeBase().search('Pavlohrad')