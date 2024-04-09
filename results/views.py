# from http.client import HTTPResponse
import base64
import math
import re, os, json, csv
from io import BytesIO
from django.conf import settings
import os
from PIL import Image

from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse, HttpResponseRedirect
from django.utils.timezone import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import render
from results.forms import ImageUploadForm
from results.models import UploadedImage
from utilities.mongo import Mongo
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import get_language_from_request
from pymongo import errors
from bson import json_util
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from deep_translator import GoogleTranslator
from django.shortcuts import render, HttpResponse


FIELD_TYPES = {
    'string' : ['type', 'max_length', 'display', 'display_type', 'required', 'index', 'translate_key', 'translate_val'],
    'integer' : ['type', 'max_length', 'display', 'display_type', 'required', 'translate_key', 'translate_val'],
    'boolean' : ['type', 'required', 'display', 'display_type', 'index', 'translate_key', 'translate_val'],
    'date' : ['type', 'required', 'display', 'display_type', 'index', 'translate_key', 'translate_val'],
    'file' : ['type', 'required', 'max_size', 'display_type', 'file_types'],
}

def sanitize(row):
    row = { k : '' if v == ",," else v for k, v in row.items() }                                        # REMOVE DOUBLE COMMAS
    row = { k : 'null' if v == "" else v for k, v in row.items() }                                      # EMPTY VALUES TO NULL
    row = { k : v for k, v in row.items() if not (type(v) == str and v.lower() == 'null') }             # REMOVE ALL NULL VALUES
    row = { k : v.replace('  ', '') if type(v) == str and '  ' in v else v for k, v in row.items() }    # REMOVE DOUBLE SPACES
    row = { k : v.rstrip() if type(v) == str else v for k, v in row.items() }                           # REMOVE RIGHT WHITE SPACES
    row = { k : int(v) if (type(v) != int and v.isdigit()) else v for k, v in row.items() }             # NON-DIGITS TO DIGITS
    row = { k : bool(v) if v == "on" or v == "off" else v for k, v in row.items() }                     # BOOLEAN VALUES TO BOOLEAN VALUES
    return row

def upload_data(request):
    try:
        if request.method == 'POST' and request.FILES['data']:
            schema_name = 'default'
            if len(request.POST.get('collection_name')):
                schema_name = request.POST.get('collection_name')

            if len(request.POST.get('new_collection_name')):
                schema_name = request.POST.get('new_collection_name')

            # DETERMINE FILE-TYPE
            file = request.FILES['data']
            format = file.name.split('.')[-1]
            if 'csv' in format:
                records = [sanitize(row) for row in csv.DictReader(file.read().decode('utf-8').splitlines())]
            if 'json' in format:
                records = json.loads(request.FILES["data"].read())

            # ADD DATA TO MONGO
            res = mongo.insert_many(schema_name=schema_name, records=records)

            # keys, fields = mongo.fields(indexed=True)
            # mongo.index(keys)

            # index_info = mongo.collection.index_information()
            # keys = list(index_info)

            # indices = [{ 'key' : keys[idx], 'val' : x, 'order' : index_info[x]['key'][0] } for idx, x in enumerate(keys)]

            # return render(request, "results/load_data.html", { 'inserts' : res.inserted_ids, 'indices' : indices } )

            # if form.is_valid():
                # form.save()
                # file = request.FILES["file"].read()

            return HttpResponse('The file is saved')
        else:
            # form = UploadDataFileForm()
            collections =  mongo.get_collections(names_only=True)
            context = {
                'collections' : collections,
            }
        return render(request, 'upload_file.html', context)
    except Exception as e:
        return HttpResponse('There was an error processing this file:', e)

def schema_new(request):
    context = {}
    context['user'] = request.user
    if request.method == "POST":
        if len(request.POST.get('schema_name')):
            mongo.new_schema(request.POST.get('schema_name'))
    
    context['schemas'] = mongo.get_schema()
    context['field_names'] = mongo.get_field_names()
    html = render_to_string('schemas.html', context, request)
    return JsonResponse(html, safe=False)

def schema_drop(request):
    context = {}
    context['user'] = request.user
    if request.method == "POST":
        if len(request.POST.get('schema_name')):
            if mongo.drop_schema(schema_name=request.POST.get('schema_name')):
                print('success')
    context['schemas'] = mongo.get_schema()
    context['field_names'] = mongo.get_field_names()
    html = render_to_string('schemas.html', context, request)
    return JsonResponse(html, safe=False)

def schema_add_field(request):
    if request.method == "POST":
        try:
            field_data = { key : value for key, value in request.POST.items() }
            field_data = sanitize(field_data)
            
            schema_name = field_data['schema']
            field_name = field_data['name']
            # field_type = field_data['type']

            # field_data = 

            # for item in field_data:
                # if item not in FIELD_TYPES[field_type]:
                    # del field_data[item]

            field_data = { field_name : { k : v for k, v in field_data.items() if k in FIELD_TYPES[field_data['type']]} }
            
            mongo.add_field(schema_name=schema_name, field_data=field_data)

        except Exception as e:
            raise e

    context = {
        'user' : request.user,
        'schemas' : mongo.get_schema(),
        'field_names' : mongo.get_field_names()
    }
    html = render_to_string('schemas.html', context, request)
    return JsonResponse(html, safe=False)

from .forms import CustomUserCreationForm

mongo = Mongo()

# class HomeListView(ListView):
#     """Renders the home page, with a list of all messages."""
#     model = LogMessage

#     def get_context_data(self, **kwargs):
#         context = super(HomeListView, self).get_context_data(**kwargs)
#         return context

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('signin')
    template_name = 'registration/signup.html'

class SignInView(CreateView):
    
    success_url = reverse_lazy('signin')
    template_name = 'registration/signin.html'


#####################################
###   USER SIGN/IN/UP/OUT ROUTES  ###
#####################################
def user_signin(request):
    # perform login
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                redirect_to = request.GET.get('redirect_to', None)
                next = request.GET.get('next', None)

                # no idea why the failed get is being cast to a string
                if redirect_to is not None and redirect_to != 'None':
                    return HttpResponseRedirect(redirect_to)
                elif next is not None and next != 'None':
                    return HttpResponseRedirect(next)
                return HttpResponseRedirect(reverse('about'))
            else:
                return HttpResponse("Your account is inactivate.")
        else:
            messages.error(request, "Wrong username or password.")
            return HttpResponseRedirect(reverse('signin'))

    # show login form
    else:
        # render
        return render(request, 'signin.html', { 'redirect_to': request.GET.get('redirect_to') })


@login_required
def user_signout(request):
    logout(request)
    return HttpResponseRedirect(reverse('about'))



#####################################
###         MAIN ROUTES           ###
#####################################
def about(request):
    return render(request, "results/about.html")

def contact(request):
    return render(request, "results/contact.html")

#####################################
###         DB/COLLECTIONS        ###
#####################################

# ROUTES FOR INDICES
def schema_index_reindex(request):
    """
    This route will (re)index a field based on the selected collection
    """
    mongo.index(schema_name=request.POST.get('schema_name'), field_name=request.POST.get('field_name'))

    context = {
        'user' : request.user,
        'schemas' : mongo.get_schema(),
        'field_names' : mongo.get_field_names()
    }

    html = render_to_string('schemas.html', context, request)
    return JsonResponse(html, safe=False)

def schema_drop_field(request):
    context = {}
    context['user'] = request.user
    if request.method == "POST":
        mongo.drop_field(schema_name=request.POST.get('schema_name'), field_name=request.POST.get('field_name'))

    context['schemas'] = mongo.get_schema()
    context['field_names'] = mongo.get_field_names()

    html = render_to_string('schemas.html', context, request)
    return JsonResponse(html, safe=False)


def schema_index_drop(request):
    """
    This route drops an index from the selected collection
    """
    context = {}
    context['user'] = request.user
    if request.method == "POST":
        schema_name = request.POST.get('schema_name')
        field_name = request.POST.get('field_name')

        mongo.drop_index(schema_name=schema_name, field_name=field_name)

        # update_result = __collection_index_response(schema_name=collection)

        context['user'] = request.user
        context['schemas'] = mongo.get_schema()
        context['field_names'] = mongo.get_field_names()


        html = render_to_string('schemas.html', context, request)
        return JsonResponse(html, safe=False)

#####################################
###             SCHEMAS           ###
#####################################
def clear_schema_history(request):
    print('clear drop/index histories')
    html = ''
    return JsonResponse({ 'success' : True, 'HTML' : html })

def configuration(request):
    """ This route returns all available schemas """    
    return render(request, "configuration.html", { 
        'schemas' : mongo.get_schema(),
        'field_names' : mongo.get_field_names()
    })

def upload_file(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return JsonResponse({ 'success' : True })
        else:
            print(list(form.errors))
    else:
        form = ImageUploadForm()

        # _Welcome to the Meroë Archaeological Project database
    return render(request, 'result-show.html', {'form': form })

#####################################
###             SEARCH            ###
#####################################
def simple_search(request):
    if request.POST.get('term'):
        query = request.POST.get('term')

    records, stats = fetch(query, lang=get_language_from_request(request, check_path=True))

    population = sum([ item['population'] for item in stats.values() if type(item) is dict ])
    total = sum([item['total'] for item in stats.values() if type(item) is dict])
    pages = page_numbers(1, math.ceil(total/10))

    docs = generate_docs(records)

    return render(request, "result-show.html", { 
        'stats' : stats,
        'records' : docs,
        'population' : population, 
        'total' : total,
        'pages' : pages
    })

def log_message(request):
    """ This route returns the search results page """
    try:
        # form = LogMessageForm(request.POST or None)

        if request.method == "POST":
            pass
            # if form.is_valid():
            #     message = form.save(commit=False)
            #     message.log_date = datetime.now()
            #     message.save()
            #     return redirect("home")
        else:
            population, total, collections, records = get_collections(mongo.get_collections())
            return render(request, "results/result-show.html", { 
                'collections' : collections,
                'population' : population, 
                'total' : total,
                'records' : records,
                'default_collection' : list(collections.keys())[0]
            })
    except:
        raise

def search_collections_fetch(request):
    population, total, collections, records = get_collections(json.loads(request.POST.get('collections')))
    
    return JsonResponse({ 
        'success' : True, 
        'stats' : render_to_string('results/result-stats.html', { 'total' : total }),
        'results' : render_to_string('results/result-carousel.html', { 'records' : records })
    })


def search(request):
    """ This route processes the search request and updates the search-results page."""
    
    # REQUIRES MONGODB ATLAS
    if 'autocomplete' in request.POST:
        mongo.autocomplete(request.POST['autocomplete'])

    query = {}
    term = request.POST.get('term')
    page = request.POST.get('page')
    lang = get_language_from_request(request, check_path=True)

    if 'exact' in request.POST  and 'true' in request.POST.get("exact"):
        term = f'\"{request.POST.get("term")}\"'
    if request.POST.get('term'):
        collections = json.loads(request.POST.get('collections'))
        # terms = request.POST.get('term').split(' ')
        
        allfields = []
        
        for collection in collections:
            allfields += mongo.fields(schema=collection, as_one_list=True)

        field_vals = [x['val'].lower() for x in allfields]
        field_keys = { x['val'].lower() : x['key'] for x in allfields }

        # CHECK IF PART OF STRING IS A FIELD
        field_val = "".join([field_val for field_val in field_vals if field_val in request.POST.get('term').lower()])
        if len(field_val):
        # any([field_val for field_val in field_vals if field_val in request.POST.get('term').lower()]):
            # field_val = [field_val for field_val in field_vals if field_val in request.POST.get('term').lower()]
            # key = field_keys[field_vals.index(request.POST.get('term').lower())]
            term = term[len(field_val):].strip()
            query = { f'{field_keys[field_val]}.val' : { '$regex' : term,  '$options' : '/^/' } }
        else:
            query = { "$text" : {"$search": request.POST.get('term') }}

    population, total, collections, records = get_collections(json.loads(request.POST.get('collections')), query, int(page)-1, lang)

    pages = page_numbers(int(page), math.ceil(total/10))

    return JsonResponse({
        'success' : True,
        'population' : population,
        'results' : render_to_string('result-carousel.html', { 'records' : records }),
        'stats' : render_to_string('result-stats.html', { 'total' : total }),
        'pages' : render_to_string('result-pages.html', { 'pages' : pages })
    })

def page_numbers(page, total):
    pages = { 'start' : 1, 'pages' : [1], 'current' : page, 'total' : total }
    if page - 2 > 2: pages['pages'].append('...')
    for i in range(2, page+1 if page-2<=1 else page): pages['pages'].append(i)
    if page != 1 and page != total and page not in pages['pages']: pages['pages'].append(page)
    for i in range(page+1, total if page+2>=total else page+3): pages['pages'].append(i)
    if page + 2 < total - 1: pages['pages'].append('...')
    if total not in pages['pages']: pages['pages'].append(pages['total'])
    return pages

# def get_collections(collections, query={}, page=0, lang='en'):
#     results = {}
#     all_records = []

#     for collection_name in collections:
#         if collection_name != 'schemas':
#             records = fetch(collection_name, query, page, lang)
#             results[collection_name] = {
#                 'population' : population,
#                 'total' : total
#             }
#             all_records += records
    
#     totals = sum(x['total'] for x in results.values())
#     populations = sum(x['population'] for x in results.values())
    
#     return populations, totals, results, all_records


def fetch(query:str='', page:int=0, lang:str='en'):
    """ This helper function returns the search results, limited to 10, and the total in the database """
    try:
        
        stats, results = {}, {}
        
        query = { '$text' : { '$search' : query }}

        collections = mongo.get_collections()

        for collection_name in collections:
            if collection_name != 'schemas':
                stats[collection_name] = {}
                results[collection_name] = {}

                try:
                    stats[collection_name]['population'] = mongo.count_docs(collection_name)
                    results[collection_name]['temp_records'] = mongo.find(collection_name=collection_name, query=query, limit=10, page=page*10)[collection_name]
                    stats[collection_name]['total'] = len(results[collection_name]['temp_records'])
                except errors.OperationFailure as e:
                    raise e

                results[collection_name]['records'] = []
                
                if len(results[collection_name]['temp_records']):
                    translator = GoogleTranslator(source='auto', target=lang)
                    for record in results[collection_name]['temp_records']:
                        
                        new_record = {}

                        # CHECK IF ANY FIELD KEYS AND/OR VALUES NEEDS TO BE TRANSLATED
                        keys, vals = mongo.to_be_translated(schemas=collections['schemas']['docs'])

                        # TRANSLATE RECORDS
                        for key, val in record.items():
                            if key in keys[collection_name] and type(key) is str: new_record[translator.translate(key)] = val
                            if val in vals[collection_name] and type(val) is str: new_record[key] = translator.translate(val)

                        results[collection_name]['records'].append(new_record)

                    results[collection_name] = results[collection_name]['records']

        return results, stats
    except:
        raise
# def get_keys(request):
    # return JsonResponse({ 'success' : True, 'fields' : mongo.fields_all() })

def thumbnail(file):
    # GENERATE THUMBNAIL OF IMAGE
    dir = os.path.join(settings.BASE_DIR, 'static', 'media', 'thumbnails')
    if not os.path.exists(dir): os.makedirs(dir)

    thumb = Image.open(file)
    thumb.thumbnail((100, 100))
    
    # BUFFER IMAGE FOR BASE64 THUMBNAIL DEVELOPMENT
    buffer = BytesIO()
    thumb.save(buffer, format=thumb.format)
    
    return thumb, buffer

def add_data(request):
    """ This route returns the add new record page 
        Filenames are "id of record_timestamp-in-ms-since-1970_user-id_original-filename"
    """
    if request.method == 'POST':
        record = { k : v for k, v in request.POST.items() }
        schema_name = record['schema_name']
        del record['schema_name']
          
        if 'Thumbnail' in request.FILES:

            thumb, buffer = thumbnail(request.FILES['Thumbnail'])

            # STORE RECORD
            record['Thumbnail'] = { 
                'path' : f'{str((datetime.now() - datetime.utcfromtimestamp(0)).total_seconds() * 1000.0)}_{request.user.id}_{request.FILES["Thumbnail"].name}',
                'base64' : f'data:{request.FILES["Thumbnail"].content_type};base64,{base64.b64encode(buffer.getvalue()).decode("utf-8")}'
            }

            res = mongo.insert_one(schema_name, record)
        
            if res.acknowledged:

                file_name = f'{res.inserted_id}_{record["Thumbnail"]["path"]}'

                # STORE THUMBNAIL
                thumb.save(os.path.join(dir, file_name))

                # STORE ORIGINAL IMAGE
                dir = os.path.join(settings.BASE_DIR, 'static', 'media')
                
                with open(os.path.join(dir, file_name), 'wb+') as destination:
                    for chunk in request.FILES.get('Thumbnail').chunks():
                        destination.write(chunk)
        else:
            res = mongo.insert_one(schema_name, record)
            if res:
                print(res)

        context = {
            'user' : request.user,
            'schemas' : mongo.get_schema(),
            'records' : generate_docs()
        }

        html = render_to_string("data_overview.html", context, request)
        return JsonResponse(html, safe=False)
    else:
        return render(request, 'data_add.html', {
            'user' : request.user,
            'schemas' : mongo.get_schema(),
            'records' : generate_docs()
        })

def get_fields(request):
    print(request)

def generate_docs(documents:dict=mongo.find()):
    schemas = mongo.get_schema()
    docs = {}
    
    for schema_name in schemas:
        docs[schema_name] = []
        schema = schemas[schema_name]['Schema']
        
        for document in documents[schema_name]:
            doc = {}
            for field_name, val in document.items():
                
                if field_name == '_id':
                    doc['metadata'] = {
                        'collection' : schema_name,
                        'id' : str(val)
                    }
                
                if field_name in schema and 'display_type' in schema[field_name]:
                    if 'title' in schema[field_name]['display_type']:
                        doc['title'] = document[field_name]
                    if 'thumbnail' in schema[field_name]['display_type']:
                        doc['thumbnail'] = document[field_name]
                        doc['thumbnail']['id'] = str(document['_id'])
                    if 'description' in schema[field_name]['display_type']:
                        doc['description'] = document[field_name]
                    if 'other' in schema[field_name]['display_type']:
                        doc['other'] = document[field_name]
            
            doc['metadata']['absent'] = [field_name for field_name in schema.keys() if field_name not in document]
            doc['document'] = document

            docs[schema_name].append(doc)
    return docs

def add_field_to_record(request):
    if request.method == 'POST':
        print(request.POST)

def get_thumbnail(request, schema:str, name:str, time:str, id:str):
    print('ok')
    # if request.method == 'GET':
    #     doc = mongo.find(collection_name=schema, _id=id)[schema][0]
    #     file_name = f'{id}_{doc["Thumbnail"]["path"]}'
    #     dir = os.path.join(settings.BASE_DIR, 'static', 'media')
    #     return HttpResponse(f'{dir}/{file_name}')
        # mongo.find(collection_name=schema, { '_id' : oid(id) })
        # file_name = f'{res.inserted_id}_{record["Thumbnail"]["time"]}_{request.user.id}_{request.FILES["Thumbnail"].name}'
    
    
def add_record(request):
    print('record')

def schema_update_field_property(request):
    context = { 'user' : request.user }
    if request.method == 'POST':
        schema_name = request.POST.get('schema_name')
        field_name = request.POST.get('field_name')
        property_key = request.POST.get('property_key')
        property_val = request.POST.get('property_val')
        mongo.update_schema(schema_name=schema_name, field_name=field_name, property={ 'key' : property_key, 'val' : property_val })

    context['schemas'] = mongo.get_schema()
    context['field_names'] = mongo.get_field_names()

    html = render_to_string('schemas.html', context, request)
    return JsonResponse(html, safe=False)

def schema_update_field(request):
    context = { 'user' : request.user }
    if request.method == 'POST':
        schema_name = request.POST.get('schema_name')
        field_name = request.POST.get('field_name')
        field_value = request.POST.get('field_val')
        mongo.update_schema(schema_name=schema_name, field_name=field_name, field_value=field_value)

    context['schemas'] = mongo.get_schema()
    context['field_names'] = mongo.get_field_names()

    html = render_to_string('schemas.html', context, request)
    return JsonResponse(html, safe=False)

def update_schema(request):
    """ This route updates the current schema and adjusts the corresponding database collection """
    schema = mongo.load_schema()

    try:
        key = set([x[0].split('_')[0] for x in list(request.POST.lists())]).pop()
        pairs = [ { x[0].split('_')[1] : x[1][0] } for x in list(request.POST.lists())]

        if 'del' in key:
            field = set({ x[0].split('_')[1] : x[1][0] for x in list(request.POST.lists()) }).pop()
            if not field in schema['FieldNames']: pass
            else: schema = mongo.delete_field('data', field)
            
        if 'add' in key or 'update' in key:

            vals = [list(x.values())[0] for x in pairs]
            pairs = { x[0].split('_')[1] : x[1][0] for x in list(request.POST.lists()) }
            
            if any(val is '' for val in vals): pass
            else:               
                field = pairs['name'].replace(' ', '_').lower()
                
                # ADD A NEW FIELD IF IT DOESN'T EXIST YET
                if field not in schema['Schema']: schema['Schema'][field], schema['FieldNames'][field] = {}, {}

                # UPDATE SCHEMA
                mongo.add_field('data', field, pairs['name'], pairs['type'], True if 'required' in pairs else False, True if 'index' in pairs else False)
                # mongo.index(schema_name='data')
        
            return JsonResponse({ 'success' : True, 'html' : render_to_string('results/data_add_fields.html', { 'fields' : mongo.fields(keys=True, vals=True), 'messages' : "Successfully updated new field and updated the index " }) })
    
    except Exception as e:
        return render(request, "results/data_add.html", { 'fields' : mongo.fields(keys=True, vals=True), 'schema_name' : mongo.load_schema('data'), 'messages' : e })

def update(request):
    """ This route updates a record's fields """
    id = request.POST.get('id')
    value = request.POST.get('value')
    if 'key' in request.POST.get('field'):
        field = f'{request.POST.get("field").split("-")[1]}.val'
        message = f'Updated key {field} with {value} for record {id}'
    if 'val' in request.POST.get('field'):
        field = f'{request.POST.get("field").split("-")[1]}.val'
        message =  f'Updated value {field} with {value} for record {id}'

    res = mongo.update_one(id, field, value)

    return JsonResponse({ 'success' : True, 'message' : message })

def load(request):
    return render(request, "results/load_data.html")

# def upload_data(request):
#     """ This route loads user data into a collection """
#     # upFile = request.FILES["file"]
#     # if request.method == 'GET':
#         # if request.GET.get('file')
#     jsonFilePath = os.path.join(os.getcwd(), 'utilities', 'data.json')
#     f = open(jsonFilePath, "r")
#     dict= json.loads(f.read())
#     res = mongo.insert_many(dict)

#     keys, fields = mongo.fields(indexed=True)
#     mongo.index(keys)

#     index_info = mongo.collection.index_information()
#     keys = list(index_info)

#     indices = [{ 'key' : keys[idx], 'val' : x, 'order' : index_info[x]['key'][0] } for idx, x in enumerate(keys)]

#     return render(request, "results/load_data.html", { 'inserts' : res.inserted_ids, 'indices' : indices } )