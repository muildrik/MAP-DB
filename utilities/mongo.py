import json, os
from typing import Iterable
# from results.models import CollectionModel
from results.schema import default_template
from pymongo import MongoClient, IndexModel, ASCENDING, DESCENDING, TEXT
from bson.objectid import ObjectId
from bson.code import Code
from pymongo.collection import ReturnDocument
from collections import namedtuple
from utilities.globals import *
import datetime

class Mongo:

    def __init__(self, collection='default'):
        self.client = MongoClient(host=MONGO_DB_HOST, port=MONGO_DB_PORT, username=MONGO_DB_USER, password=MONGO_DB_PASS)
        self.db = MONGO_DB_NAME
        self.collection = self.client[self.db][collection]
        
        self.load_schemas()

    def db(self, db):
        if db:
            self.db = db
        else:
            return self.db

    def find_one_by_id(self, collection:str='default', id:str=None):
        if self.collection: 
            return self.collection.find_one({ '_id' : ObjectId(id) })

    def update_one(self, id, field, value):
        if self.collection:
            return self.collection.find_one_and_update({ '_id' : ObjectId(id) }, { '$set' : { field : value }}, upsert=False, return_document=ReturnDocument.AFTER)

    def update_many(self, field, value):
        if self.collection:            
            return self.collection.update_many({ f'{field}.index' : not value }, { '$set' : { f'{field}.index' : value } })

    def insert_one(self, schema_name:str='default', document:dict={}):
        return self.client[self.db][schema_name].insert_one(document)

    def insert_many(self, schema_name:str='default', records=[]):
        try:
            result = self.build_schema(schema_name=schema_name, records=records)
            if result.acknowledged:
                res = self.client[self.db][schema_name].insert_many(records)
                if res.acknowledged:
                    return True
                else:
                    raise('There was a problem inserting the records in the collection')
            else:
                raise('There was a problem building/updating the schema for this collection')
        except Exception as e:
            raise e

    # COLLECTIONS
    def get_schema(self, schema_name:str=False):
        """
        Return a specific schema from the schemas collection or all schemas in the schemas collection
        """
        return self.schemas[schema_name] if schema_name else self.schemas

    def get_collection(self, collection_name:str='default'):
        """
        Returns all records in a collection
        """
        return self.client[self.db][collection_name].find()

    def get_field_names(self):
        return { name : schema['FieldNames'] for name, schema in self.schemas.items() }

    def get_collections(self, names_only=False):
        """
        Returns all collections in the current database
        """
        try:
            if names_only:
                collections = self.client[self.db].list_collection_names()
                if 'schemas' in collections: collections.remove('schemas')
                return collections
            
            collections = {}
            for collection in self.client[self.db].list_collection_names():
                collections[collection] = { 
                    'name' : collection, 
                    'docs' : [x for x in self.client[self.db].get_collection(collection).find()],
                    'schema' : [x for x in self.client[self.db]['schemas'].find()]
                }

            return collections
        except Exception as e:
            raise e

    def new_schema(self, schema_name='default'):
        try:
            if schema_name not in self.get_collections():
                res = self.client[self.db].create_collection(schema_name)
                if res:
                    print(res)

            return True if self.add_schema(schema_name, self.basic_schema(schema_name)).acknowledged else False

        except Exception as e:
            raise e

    def count_docs(self, collection_name:str='default', filter:dict={}):
        return self.client[self.db][collection_name].count_documents(filter=filter)

    def to_be_translated(self, schema_name:str='default', schemas:list=None):
        """
        Pass in either schema_name or list of docs

        Returns
        -------
        - keys to be translated
        - vals to be translated

        """
        keys, vals = {}, {}
        if schemas:
            for schema in schemas:
                keys[schema['SchemaInfo']['schema_name']] = []
                vals[schema['SchemaInfo']['schema_name']] = []
                for field_name, properties in schema['Schema'].items():
                    if properties['translate_key']: keys[schema['SchemaInfo']['schema_name']].append(field_name)
                    if properties['translate_val']: vals[schema['SchemaInfo']['schema_name']].append(field_name)
        return keys, vals

    # SCHEMA
    def basic_schema(self, schema_name:str='default'):
        """
        Returns basic schema information
        """
        return {
                "SchemaInfo": {
                    "schema_name": schema_name,
                    "system_fields": [],
                    "indexed_fields": [],
                    "unindexed_fields": [],
                    "index_log": {
                        "indexed": {},
                        "dropped": {}
                    }
                },
                'Schema' : {},
                "FieldNames": []
            }

    def build_schema(self, schema_name:str='default', records:Iterable=[]):
        """
        Generates a schema based on a set of records
        """

        schema = [x for x in self.client[self.db]['schemas'].find({ 'SchemaInfo.schema_name' : schema_name })]
        schema = schema[0] if len(schema) else self.basic_schema(schema_name)

        if type(records) is list:
            for record in records:
                self.add_to_schema(schema=schema, record=record)
        if type(records) is dict:
            self.add_to_schema(schema=schema, record=[records])
                
        return self.add_schema(schema=schema)

    def add_to_schema(self, schema:dict={}, record:dict={}):

        for prop_key, prop_val in record.items():
            if prop_key not in schema['FieldNames']: 
                schema['FieldNames'].append(prop_key)
                schema['Schema'][prop_key] = prop_val
                if 'file_types' in prop_val:
                    if any([x for x in ['jpg', 'png', 'jpeg', 'tiff', 'tif'] if x in prop_val['file_types']]):
                    
                        schema['Schema'][prop_key]['image'] = True

                if 'display_type' in prop_val and prop_val['display_type'] == 'thumbnail':
                    schema['Schema'][prop_key]['thumbnail'] = True

                if 'index' in prop_val:
                    schema['Schema'][prop_key]['last_indexed'] = [datetime.datetime.now()]
                    schema['Schema'][prop_key]['last_dropped'] = []
                    self.index(schema_name=schema['SchemaInfo']['schema_name'], field_name=prop_key)
            else:
                continue            

    def add_schema(self, schema_name:str='default', schema:dict={}):
        return self.client[self.db]['schemas'].replace_one({ 'SchemaInfo.schema_name' : schema_name }, schema, upsert=True)

    def update_schema(self, schema_name:str='default', field_name:str=None, field_value:any=None, property:dict=None):
        if property and not field_value:
            if 'Name' in field_name or 'Name' in property['key']:
                self.schemas[schema_name]['Schema'][property['val']] = self.schemas[schema_name]['Schema'][field_name]
                del self.schemas[schema_name]['Schema'][field_name]
                self.schemas[schema_name]['FieldNames'].remove(field_name)
                field_name = property['val']
                self.schemas[schema_name]['FieldNames'].append(field_name)
            if property['key'] in self.schemas[schema_name]['Schema'][field_name] and type(self.schemas[schema_name]['Schema'][field_name][property['key']]) is bool:
                value = False if property['val'] in ['off', 'false'] else True
                self.schemas[schema_name]['Schema'][field_name][property['key']] = value
            # if field_name in self.schemas[schema_name]['Schema']:
            #     if 'Name' in property['key']:
            #         field = self.schemas[schema_name]['Schema'][field_name]
            #         self.schemas[schema_name]['Schema'][property['val']] = field
            #         del self.schemas[schema_name]['Schema'][field_name]

        else:
            self.schemas[schema_name]['Schema'][field_name] = field_value

        # UPDATE DOCUMENTS THAT USE THIS SCHEMA
        self.client[self.db][schema_name].update_many({ 'SchemaInfo.schema_name' : schema_name, f'Schema.{field_name}' : { '$exists' : True } }, { "$rename" : { f'Schema.{property["key"]}' : f'Schema.{property["val"]}' }})

        return self.client[self.db]['schemas'].replace_one({ 'SchemaInfo.schema_name' : schema_name }, self.schemas[schema_name], upsert=True)

    def find(self, collection_name:str='default', _id:str=None, query:dict={}, limit:int=10, page:int=0):
        if _id is not None: query = { '_id' : ObjectId(_id) }
        return { collection_name : [x for x in self.client[self.db][collection_name].find(query).limit(10).skip(page)] }

    def fields_all(self):
        """This method returns all fields in Mongo"""
        if self.collection:
            fields = self.f5([y for x in list(self.collection.find()) for y in x.keys() if '_id' not in y])
            return fields
    
    def fields(self, schema_name='default', keys=None, vals=None, as_one_list:bool=False, system:bool=False, indexed:bool=False, include:list=[]):
        """
        This method returns a schema's fields and assumes the default schema if none is provided
        ### Parameters
        - collection
        - 
        - include : list
            -   Optional list to mark system fields to include in the return

        """

        
        return self.schemas[schema_name]['Schema']

        # self.load_schema(collection)
        # result = namedtuple("fields", ["indexed", "unindexed"])

        # FILTER OUT SYSTEM FIELDS
        # if not system:
        #     for field in schema['SchemaInfo']['system_fields']:
        #         if field in include and field not in schema['SchemaInfo']['indexed_fields']:
        #             schema['SchemaInfo']['indexed_fields'].append(field)
        #         else:
        #             if field in schema['SchemaInfo']['indexed_fields']:
        #                 schema['SchemaInfo']['indexed_fields'].remove(field)
        #             if field in schema['SchemaInfo']['unindexed_fields']:
        #                 schema['SchemaInfo']['unindexed_fields'].remove(field)

        # return schema[schema_name]['Schema']
        
        # RETURN KEYS ONLY
        # if keys and not vals:
        #     if as_one_list:
        #         return schema['SchemaInfo']['indexed_fields'] + schema['SchemaInfo']['unindexed_fields']
        #     else:
        #         return result(
        #             schema['SchemaInfo']['indexed_fields'], 
        #             schema['SchemaInfo']['unindexed_fields']
        #         )        
        
        # # RETURN VALS ONLY
        # if vals and not keys:
        #     if as_one_list:
        #         return [schema['FieldNames'][field]['val'] for field in schema['SchemaInfo']['indexed_fields']] + [schema['FieldNames'][field]['val'] for field in schema['SchemaInfo']['unindexed_fields']]
        #     else:
        #         return result(
        #             [schema['FieldNames'][field]['val'] for field in schema['SchemaInfo']['indexed_fields']], 
        #             [schema['FieldNames'][field]['val'] for field in schema['SchemaInfo']['unindexed_fields']]
        #         )

        # # RETURN VALS AND KEYS
        # if (keys and vals) or (not keys and not vals):
        #     if as_one_list:
        #         return [{ 'key' : field, 'val' : schema['FieldNames'][field]['val'] } for field in schema['SchemaInfo']['indexed_fields']] + [{ 'key' : field, 'val' : schema['FieldNames'][field]['val'] } for field in schema['SchemaInfo']['unindexed_fields']]
        #     else:
        #         return result(
        #             [{ 'key' : field, 'val' : schema['FieldNames'][field]['val'] } for field in schema['SchemaInfo']['indexed_fields']],
        #             [{ 'key' : field, 'val' : schema['FieldNames'][field]['val'] } for field in schema['SchemaInfo']['unindexed_fields']]
        #         )


    def delete_field(self, collection, fields):
        schema = self.load_schema(collection)

        for field in fields:
            del schema['Schema'][field]
            del schema['FieldNames'][field]
            if field in schema['SchemaInfo']['indexed_fields']: schema['SchemaInfo']['indexed_fields'].remove(field)
            if field in schema['SchemaInfo']['unindexed_fields']: schema['SchemaInfo']['unindexed_fields'].remove(field)
                
        return self.save_schema(schema, schema['SchemaInfo']['schema_name'])

    # def get_collections(self):
    #     """
    #     Fetch collections in database
    #     """
    #     return self.client[self.db].list_collection_names()

    def drop_schema(self, schema_name:str='default') -> bool:
        """
        Drop a schema and its Mongo collection. The default schema and collection always exist.
        """
        try:
            res = self.client[self.db].drop_collection(schema_name)
            if res:
                print(res)

            if schema_name in self.schemas: del self.schemas[schema_name]

            res = self.client[self.db]['schemas'].find_one_and_delete({ 'SchemaInfo.schema_name' : schema_name })
            if res:
                print(res)

            return self.new_schema(schema_name) if schema_name == 'default' else True

        except Exception as e:
            raise e

    def get_indices(self, schema_name:str='default'):
        return [index for index in self.client[self.db][schema_name].index_information()]
        
    def drop_index(self, schema_name:str='default', field_name:str=None):
        try:

            if field_name in self.get_indices():

                self.schemas[schema_name]['Schema'][field_name]['last_dropped'].append(datetime.datetime.now())
                self.schemas[schema_name]['Schema'][field_name]['indexed'] = False

                res = self.client[self.db]['schemas'].find_one_and_replace({ 'SchemaInfo.schema_name' : schema_name }, self.schemas[schema_name])
                if res:

                    # DROP INDEX IN MONGO
                    self.client[self.db][schema_name].drop_index(field_name)

        except Exception as e:
            raise e

    def add_logs(self, schema_name:str='default', fields={}):
        """ This helper function adds the last indexed/dropped timestamps to fields of the relevant schema to be returned """
        schema = self.schemas[schema_name]

        for x in fields.indexed:
            if x['key'] not in schema['SchemaInfo']['system_fields']:
                last_index = schema['SchemaInfo']['index_log']['indexed'][x['key']]
                last_drop = schema['SchemaInfo']['index_log']['dropped'][x['key']]
                u = {}
                u['last_index'] = datetime.datetime.fromisoformat(last_index[-1]).strftime("%m/%d/%Y at %H:%M:%S") if len(last_index) else ''
                u['last_drop'] = datetime.datetime.fromisoformat(last_drop[-1]).strftime("%m/%d/%Y at %H:%M:%S") if len(last_drop) else ''
                x.update(u)

        for x in fields.unindexed:
            if x['key'] not in schema['SchemaInfo']['system_fields']:
                last_index = schema['SchemaInfo']['index_log']['indexed'][x['key']]
                last_drop = schema['SchemaInfo']['index_log']['dropped'][x['key']]
                u = {}
                u['last_index'] = datetime.datetime.fromisoformat(last_index[-1]).strftime("%m/%d/%Y at %H:%M:%S") if len(last_index) else ''
                u['last_drop'] = datetime.datetime.fromisoformat(last_drop[-1]).strftime("%m/%d/%Y at %H:%M:%S") if len(last_drop) else ''
                x.update(u)

    def add_translations(self, schema_name:str='default', fields={}):
        # translate_keys = [k for k, v in schema['Schema'].items() if 'translate_key' in v]
        # translate_vals = [k for k, v in schema['Schema'].items() if 'translate_val' in v]
        schema = self.schemas[schema_name]

        for field in fields.indexed:
            u = {}
            if 'translate_key' in schema['Schema'][field['key']]:
                u['translate_key'] = True
            if 'translate_val' in schema['Schema'][field['key']]:
                u['translate_val'] = True
            field.update(u)

        for field in fields.unindexed:
            u = {}
            if 'translate_key' in schema['Schema'][field['key']]:
                u['translate_key'] = True
            if 'translate_val' in schema['Schema'][field['key']]:
                u['translate_val'] = True
            field.update(u)

    def add_field(self, schema_name:str='default', field_data:dict={}):
        schema = self.schemas[schema_name]
        self.add_to_schema(schema=schema, record=field_data)
        res = self.client[self.db]['schemas'].find_one_and_replace({ 'SchemaInfo.schema_name' : schema_name }, schema)

        # schema = self.load_schema(collection)
        
        # schema['Schema'][field].update({
            # "type" : type,
            # "required" : required,
            # "index" : index
        # })
        # schema['FieldNames'][field].update({ 
            # 'key' : field,
            # 'val' : name
        # })
        # schema['SchemaInfo']['unindexed_fields'].append(field)
        
        # return self.save_schema(schema, schema['SchemaInfo']['schema_name'])
    
    # REQUIRES MONGODB ATLAS
    def autocomplete(self, term:str=''):
        print('not implemented')
        # for collection in self.client[self.db].list_collection_names():
        #     if 'schemas' not in collection:
        #         pipeline = [
        #             {"$unwind": "$tags"},
        #             {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        #             {"$sort": SON([("count", -1), ("_id", -1)])}
        #         ]
        #         object_list = list(self.client[self.db][collection].aggregate([
        #             {
        #                 '$match' : { 
        #                     'index ' : 'Name',
        #                     'compound' : {
        #                         'must' : {
        #                             'text' : {
        #                                 'query': term,
        #                                 'path' : 'name',
        #                                 'fuzzy': { 
        #                                     'maxEdits' : 2
        #                                 }
        #                             }
        #                         }
        #                     }
        #                 }
        #             }
        #         ]))
        #         print(object_list)

    def drop_field(self, schema_name:str='default', field_name:str=None):
        if schema_name in self.get_collections() or schema_name in self.get_field_names():
            
            # REMOVE THE FIELD FROM THE SCHEMA
            field_names = self.get_field_names()
            if field_name in field_names[schema_name]:
                self.schemas[schema_name]['FieldNames'].remove(field_name)
                del self.schemas[schema_name]['Schema'][field_name]

            self.client[self.db]['schemas'].find_one_and_replace({ 'SchemaInfo.schema_name' : schema_name }, self.schemas[schema_name], upsert=True)

            # DROP ANY INDEX
            self.drop_index(schema_name=schema_name, field_name=field_name)

            # DELETE THE FIELD FROM ALL RECORDS
            res = self.client[self.db][schema_name].update_many({ field_name : { "$exists" : True } }, { "$unset" : { field_name : 1} }, False)

            if res:
                print(res)

    def index(self, schema_name='default', field_name:str=None):
        try:
            self.drop_index(schema_name=schema_name, field_name=field_name)
            self.client[self.db][schema_name].create_index(keys=[(field_name, TEXT)], name=field_name, background=True)
            self.schemas[schema_name]['Schema'][field_name]['indexed'] = True
            self.client[self.db]['schemas'].find_one_and_replace({ 'SchemaInfo.schema_name' : schema_name }, self.schemas[schema_name], upsert=True)
        except Exception as e:
            raise e

#####################################
###      SCHEMA MAINTENANCE       ###
#####################################
    def load_schemas(self):
        try:
            self.schemas = { x['SchemaInfo']['schema_name'] : { 'SchemaInfo' : x['SchemaInfo'], 'Schema' : x['Schema'], 'FieldNames' : x['FieldNames'] } for x in self.client[self.db]['schemas'].find() }

            if not len(self.schemas):

                # CHECK IF ANY COLLECTIONS EXIST
                collections = self.get_collections()
                if not len(collections):
                    collections['default'] = {}

                    # ADD DEFAULT SCHEMAS FOR ANY EXISTING COLLECTIONS
                for schema_name in collections.keys():
                    if schema_name == 'schemas':
                        continue
                    self.schemas[schema_name] = self.basic_schema(schema_name=schema_name)
                    if schema_name not in collections:
                        res = self.client[self.db].create_collection(schema_name)
                        if res:
                            print(res)
                    res = self.add_schema(schema_name=schema_name, schema=self.schemas[schema_name])
                    if res:
                        print(res)
        except Exception as e:
            raise e

    # def load_schemas(self):
    #     """
    #     Fetch all schemas in json format
    #     """
    #     try:
    #         p = os.path.join(os.getcwd(), 'results', 'schemas')
    #         files = [f for f in os.listdir(p) if os.path.isfile(os.path.join(p, f))]
    #         schemas = {}
    #         for file in files:
    #             with open(os.path.join(os.getcwd(), 'results', 'schemas', file), 'r', encoding='utf-8') as schema:
    #                 schema_json = json.loads(schema.read())
    #                 schemas[schema_json['SchemaInfo']['schema_name']] = schema_json
    #                 schema.close()
    #         return schemas
    #     except:
    #         raise

    def load_schema(self, schema_name:str=None):
        """
        Load a single schema from file into memory
        ### Parameters
        - schema_name : str
            -   Name of the schema to (re)load from file
        ### Returns
        - dict
            -   The schema in memory
        """
        # schemas = self.load_schemas()
        # try:
        #     if len(self.schemas):
        #         if schema_name is None:
        #             schema = list(self.schemas.items())[0][1]
        #         else:
        #             schema = self.schemas[schema_name]
        #     else:
                
        #         # PRODUCE DEFAULT SCHEMA IF NONE ARE PRESENT
        #         with open(os.path.join(os.getcwd(), 'results', 'schemas', 'default.json'), 'w', encoding='utf-8') as json_file:
        #             json_file.write(json.dumps(default_template, indent=4))
        #             self.schemas['default'] = default_template
        #             schema = self.schemas['default']
                    
        #             self.client[self.db].create_collection('default')
            
        #     return schema
        # except Exception as e:
        #     raise e

                # json_file.close()
            # json_file.write(json.dumps(self.schema if new_schema is None else new_schema, indent=4))

        # return self.schema
        # try:
        #     with open(os.path.join(os.getcwd(), 'results', 'schemas', f'{schema}.json')) as json_file:
        #         schema_json = json.load(json_file)
        #         json_file.close()
        #         self.schemas[schema] = schema_json
        #         self.schema = schema_json
        #         return self.schema
        # except:
        #     raise

    def save_schema(self, schema_name:str, new_schema:dict):
        """
        Save a single schema from memory to file. This will overwrite existing schema files.
        ### Parameters
        - schema : str
            -   The name of the schema to save
        - new_schema : dict, default=None
            -   The new schema to be saved
        ### Returns
        - dict
            -   The saved schema in memory
        """
        try:
            with open(os.path.join(os.getcwd(), 'results', 'schemas', f'{schema_name}.json'), 'w', encoding='utf-8') as file:
                file.write(json.dumps(new_schema, indent=4))
                file.close()
                self.schemas[schema_name] = new_schema
                return new_schema
        except:
            raise

def f5(seq, idfun=None): 
   # order preserving
   if idfun is None:
       def idfun(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = idfun(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result