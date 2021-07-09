from os import listdir, mkdir
from os.path import join, isdir, isfile
from collections import Counter
import math
import re
import heapq


class SearchEngine:

    def __init__(self):
        pass


    def normalize(self, text):
        
        # removing numbers and symbols from the text
        text = re.sub('[0-9]|[۰-۹]|,|&|\(|\)|\[|\]|\.|/|«|»|-|،|:|؟||؛|\"|\'|–|\?|…', '', text)

        # removing these stuffs
        text = re.sub('ْ|ٌ|ٍ|ً|ُ|ِ|َ|ّ|', '', text)

        # taking care of these guys
        text = text.replace('ؤ', 'و')
        text = text.replace('ئ', 'ی')
        text = text.replace('أ', 'ا')
        text = text.replace('آ', 'ا')

        return text


    def stem(self, tokens):

        for i in range(len(tokens)):

            # removing 'تر' and 'ترین'
            if tokens[i].endswith('تر'):
                tokens[i] = tokens[i][0: len(tokens[i]) - 2]
            if tokens[i].endswith('ترین'):
                tokens[i] = tokens[i][0: len(tokens[i]) - 4]

            # removing plural 'ها'
            if tokens[i].endswith('‌ها'):  # (there is a 'نیم‌فاصله' before 'ها')
                tokens[i] = tokens[i][0: len(tokens[i]) - 3]

            # taking care of present and past continuous
            if tokens[i].startswith('می‌') or tokens[i].startswith('نمی‌'):  # (there is a 'نیم‌فاصله' after 'می')
                if tokens[i].startswith('نمی‌'):
                    t = tokens[i][4: ]
                else:
                    t = tokens[i][3: ]
                if t.endswith('ند') or t.endswith('ید') or t.endswith('ند'):
                    t =  t[0: len(tokens[i]) - 2]
                elif t.endswith('د') or t.endswith('ی') or t.endswith('م'):
                    t =  t[0: len(tokens[i]) - 1]
                tokens[i] = t

        return tokens


    def remove_stop_words(self, tokens):
        stop_words = [
            '', ' ',
            'از', 'و', 'با', 'تا', 'در', 'برای', 'است', 'نیز', 'یا', 'اما',
            'این', 'آن', 'اگر', 'آیا', 'باید', 'یک', 'ولی', 'همه', 'هم', 'اینکه'
            'هر', 'نیز', 'را', 'مانند', 'شاید', 'را', 'پس', 'به', 'بر', 'آیا'
            'من', 'تو', 'او', 'ما', 'شما', 'آن', 'ایشان',
        ]

        tokens = [t for t in tokens if t not in stop_words and len(t) < 20]
        return tokens


    def build_cluster(self, docs_directory, cluster_name):

        # creating clusters directory
        if not isdir('clusters'):
            mkdir('clusters')

        # creating a directory for the given cluster
        if not isdir(join('clusters', cluster_name)):
            mkdir(join('clusters', cluster_name))

        pairs = []

        # document vector length (which will be used in cosine similarity)
        docs_length = []

        # a dict that maps doc names to docID
        docName_docID = {}

        file_num = 0
        for f in listdir(docs_directory):

            file_name = f.split('.')[0]
            docName_docID[file_name] = file_num
            
            # reading the file
            file = open(join(docs_directory, f), 'r')
            text = file.read()

            # normalization
            text = self.normalize(text)
            
            # tokenization
            tokens = text.split() 

            # stemming
            tokens = self.stem(tokens)

            # removing stop words
            tokens = self.remove_stop_words(tokens)

            # adding tokens in 'pairs' list
            for token in tokens:
                pairs.append((token, file_num))

            # calculating docs_length
            length = 0
            for _, freq in Counter(tokens).items():
                length += freq**2

            docs_length.append((file_num, math.sqrt(length)))

            file_num += 1

                
        # sorting doc_length based on docID
        docs_length.sort(key=lambda x: x[0])

        # storing docName_docID in file system
        file = open(join('clusters', cluster_name, 'docName_docID'), 'w')
        for docName in docName_docID:
            file.write(docName)
            file.write(' ')
            file.write(str(docName_docID[docName]))
            file.write("\n")


        # storing doc_length in file system
        file = open(join('clusters', cluster_name, 'docs_length'), 'w')
        for dl in docs_length:
            file.write("{:.4f}".format(round(math.sqrt(dl[1]), 4)))
            file.write("\n")

        # storing the number of documents in the cluster in file system
        file = open(join('clusters', cluster_name, 'num_docs'), 'w')
        file.write(str(len(docs_length)))
        file.write("\n")

        # building inverted index

        # sorting by terms
        pairs.sort(key=lambda x: x[0])

        # creating 'index' directory
        if not isdir(join('clusters', cluster_name, 'index')):
            mkdir(join('clusters', cluster_name, 'index'))


        # creating inverted index and storing it into file system
        i = 0
        postings_list = []
        cluster_freq = 0  # a varialbe to store the frequency of a term inside a cluster
        while i < len(pairs):
            
            term = pairs[i][0]
            docID = pairs[i][1]

            # finding the frequency of the term in current document
            freq = 1
            while i + freq < len(pairs) and pairs[i] == pairs[i + freq]:
                freq += 1

            cluster_freq += freq
        
            # appending the (docID, frequency) to postings list
            postings_list.append((docID, freq))

            # if this is the last time that we're seeing this term
            if i + freq == len(pairs) or (pairs[i + freq][0] != term):

                # sorting postings list based on tf/doc_length (Champions List)
                postings_list.sort(key=lambda x: x[1]/docs_length[x[0]][1], reverse=True)

                # writing the postings list in file system
                file = open(join('clusters', cluster_name, 'index', term), 'w')

                # writing the average-tf (= sum(tf) in the postings, divided by
                # the number of docs in the cluster) in the first line
                file.write(str(cluster_freq / file_num))
                file.write('\n') 

                # writing ther number of docs in the postings
                file.write(str(len(postings_list)))
                file.write('\n') 

                for posting in postings_list:
                    file.write(str(posting[0]))
                    file.write(',')
                    file.write(str(posting[1]))
                    file.write(' ')
                
                # clearing the postings list
                postings_list = []
                cluster_freq = 0
                
            i += freq


    def search(self, query, k):

        r = 2 * k

        # normalizing the query
        query = self.normalize(query)

        # tokenizing
        q_terms = query.split()

        # stemming the query tokens
        q_terms = self.stem(q_terms)

        # converting query into (term: frequency) terms
        q_terms = Counter(q_terms)

        # total number of documents (in all the clusters)
        N = 0

        # finding the best cluster
        centroid_tfs = []
        dfs = [0 for _ in range(len(q_terms))]

        num_to_cluster = {}

        for i, f in enumerate(listdir('clusters')):

            num_to_cluster[i] = f

            # reading the number of documents in the cluster
            file  = open(join('clusters', f, 'num_docs'))
            N += int(file.readline())
            
            vector = []
            for i, q_term in enumerate(q_terms):

                # reading cluster's posting's list for the term, from file system
                file_name = join('clusters', f, 'index', q_term)
                if not isfile(file_name):
                    vector.append(0)
                    continue

                file = open(file_name)

                centroid_tf = float(file.readline())
                vector.append(centroid_tf)

                num_docs = int(file.readline())
                dfs[i] += num_docs

            centroid_tfs.append(vector)


        # calculating the tf-idf score of query terms
        q_scores = [0 for _ in range(len(dfs))]
        for i, q_term in enumerate(q_terms):
            idf = 0
            if dfs[i] != 0:
                idf = N / dfs[i]
            q_scores[i] = q_terms[q_term] * idf


        # finding the most similar centroid
        best_centroid_index = -1
        best_centroid_similarity = -10000
        for i in range(len(centroid_tfs)):
            similarity = sum([q_scores[j] * centroid_tfs[i][j] for j in range(len(q_scores))])
            if similarity > best_centroid_similarity:
                best_centroid_similarity = similarity
                best_centroid_index = i

        best_centroid = num_to_cluster[best_centroid_index]

        print(f'Resluts in {best_centroid} category:')


        # searching for the best documents in the best cluster

        # loading docs_length from file system
        file = open(join('clusters', best_centroid, 'docs_length'))
        records = file.read().split()
        docs_lengths = [float(r) for r in records]

        # loading docName_docID from file system
        file = open(join('clusters', best_centroid, 'docName_docID'))
        records = file.read().split('\n')
        docID_docName = {}
        for rec in records:
            if rec == '':
                continue
            idx = rec.rfind(' ')
            name = rec[:idx]
            docID = int(rec[idx:]) 
            docID_docName[docID] = name


        # finding top-k documents

        docs = {}
        for q_term in q_terms:

            # reading posting's list from file
            file_name = join('clusters', best_centroid, 'index', q_term)
            if not isfile(file_name):
                continue

            file = open(file_name)

            # throwing away the first 2 lines
            file.readline()
            file.readline()

            records = file.read().strip().split(' ')

            # calculating partial tf-idf score for the term in query
            N = len(docs_lengths)
            q_score = (1 + math.log(q_terms[q_term])) * math.log(N / len(records))

            for i in range(min(len(records), r)):

                docID, freq = map(int, records[i].split(',')) 

                # calculating partial tf score for the term in document
                d_score = 1 + math.log(freq)

                # partial cosine similarity
                partial_similarity = d_score * q_score

                if docID in docs:
                    docs[docID] = docs[docID] - partial_similarity
                else:
                    docs[docID] = - partial_similarity
        
            
        # creating a heap (also, normalizing scores by docs_length)
        heap = [(j / docs_lengths[i], i) for i, j in docs.items()]
        heapq.heapify(heap)

        # returning the top k documents
        result = []
        for _ in range(min(k, len(heap))):
            doc = heapq.heappop(heap)
            result.append((f'Document Name: {docID_docName[doc[1]]}', f'Similarity: {-doc[0]}'))
        return result
        

def main():

    search_engine = SearchEngine()

    # INDEXING (can be commented out after the first run)
    # search_engine.build_cluster(join('docs', 'ریاضیات'), 'ریاضیات')
    # search_engine.build_cluster(join('docs', 'تاریخ'), 'تاریخ')
    # search_engine.build_cluster(join('docs', 'فیزیک'), 'فیزیک')
    # search_engine.build_cluster(join('docs', 'فناوری'), 'فناوری')
    # search_engine.build_cluster(join('docs', 'بهداشت'), 'بهداشت')

    # SOME QUERIES
    result = search_engine.search('انتگرال', k=5)
    # result = search_engine.search('گاما', k=10)
    # result = search_engine.search('دانش روز', k=5)
    # result = search_engine.search('دانشمند', k=5)
    # result = search_engine.search('تابع', k=5)

    if result == []:
        print('Nothing!')
    else:
        for ent in result:
            print(ent)

if __name__ == "__main__":
    main()
