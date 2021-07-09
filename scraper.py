import requests
from os import listdir, mkdir
from os.path import join, isdir, isfile
from random import shuffle

URL = "https://fa.wikipedia.org/w/api.php"

def get_page(title):

    PARAMS = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvslots": "*",
        "rvprop": "content",
        "formatversion": "2",
        "format": "json"
    }

    S = requests.Session()
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()    
    content = DATA['query']['pages'][0]['revisions'][0]['slots']['main']['content']
    
    return content


def get_category(cat):
    

    PARAMS = {
        "action": "query",
        "cmtitle": "رده:" + cat,
        "cmlimit": "1000",
        "list": "categorymembers",
        "format": "json"
    }

    S = requests.Session()
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()

    PAGES = DATA['query']['categorymembers']

    subcats = []
    docs = []

    for page in PAGES:
        title = page['title']

        if title.startswith('رده:'):
            subcats.append(title[4:])
        else:
            docs.append(title)

    shuffle(subcats)
    shuffle(docs)

    return subcats, docs


def fetch_documents():

    # creating a folder
    if not isdir('docs'):
        mkdir('docs')


    # searching wikipedia

    NUM_DOCS_IN_CATS = 50

    for cat in ['فیزیک‎', 'بهداشت', 'ریاضیات', 'فناوری', 'تاریخ']:

        if not isdir(join('docs', cat)):
            mkdir(join('docs', cat))

        num = 0
        queue = [cat]

        while (num < NUM_DOCS_IN_CATS) and queue != []:

            current_cat = queue.pop(0)
            subcats, docs = get_category(current_cat)

            for doc in docs:
                content = get_page(doc)
                f = open(join('docs', cat, doc), 'w')
                f.write(content)
                num += 1
                if num == NUM_DOCS_IN_CATS:
                    break
                
            queue = queue + subcats


if __name__ == "__main__":
    fetch_documents()
