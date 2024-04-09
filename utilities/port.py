import csv, json, argparse, os, re
 
# Function to convert a CSV to JSON
# Takes the file paths as arguments
def make_json(csvFilePath):
     

    data = []

    csvFilePath = os.path.join(os.getcwd(), 'utilities', csvFilePath['filename'])
    jsonFilePath = csvFilePath.split('.')[:-1]
    jsonFilePath.append('json')
    jsonFilePath = ".".join(jsonFilePath)

    with open(csvFilePath, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)

        for rows in csvReader:
            # key = rows['Small Find Number']
            data.append(rows)

    vals = []

    for x in data:
        chars = []
        a = {}
        for k, v in x.items():
            b = k.lower().replace(' ', '_')
            a[b] = {}
            a[b]['key'] = b
            a[b]['text'] = k
            a[b]['val'] = v
            a[b]['index'] = True
            if 'description' in b:
                a[b]['translate_key'] = True
                a[b]['translate_val'] = True
            if not len(v) <= 1:
                l = re.findall(r'\w+', v)
                if len(l):
                    for z in l:
                        if len(z) > 1:
                            chars.append(z)
        chars = f5(chars)
        a['text_search'] = " ".join(chars)
        a['thumbnail'] = '/images/default.png'
        vals.append(a)
 
    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(vals, indent=4))

    return 

def main():
    parser = argparse.ArgumentParser(description='Convert CSV to JSON')
    parser.add_argument('-f', '--filename', help='File name', required=False)
    args = vars(parser.parse_args())
    res = make_json(args)

def f5(seq, idfun=None): 
   if idfun is None:
       def idfun(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = idfun(item)
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result

if __name__ == "__main__":
    main()