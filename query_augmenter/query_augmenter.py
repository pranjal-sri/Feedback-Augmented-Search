import requests
import json
import regex as re

class QueryAugmenter:
    def __init__(self):
        self.pattern = re.compile(r'''
            ’s|’t|’re|’ve|’m|’ll|’d| ?\p{L}+| ?\p{N}+”
            ''')
        self.stop_words = set()
        with open('stop_words.txt', 'r') as stop_words_file:
            for line in stop_words_file:
                self.stop_words.add(line.strip())
    
    def extract_words(self, result_list):
        word_lists = []
        vocab = set()
        for result in result_list:
            title = result.get('Title', '')
            snippet = result.get('Snippet', '')
            title_words = re.findall(self.pattern, title.lower())
            title_words = [word.strip() for word in title_words if word.strip() not in self.stop_words]
            snippet_words = re.findall(self.pattern, snippet.lower())
            snippet_words = [word.strip() for word in snippet_words if word.strip() not in self.stop_words]
            vocab.update(title_words + snippet_words)
            word_lists.append({'title': title_words, 'snippet': snippet_words})
        return word_lists, vocab
    
    def gini_impurity(self, word, docs_with_word, docs_without_word, feedback):
        relevant_docs_with_word = 0
        relevant_docs_without_word = 0
        for doc in docs_with_word:
            relevant_docs_with_word += feedback[doc]
        for doc in docs_without_word:
            relevant_docs_without_word += feedback[doc]
        prob_relevant_with_word = relevant_docs_with_word/len(docs_with_word)
        prob_irrelevant_with_word = 1 - prob_relevant_with_word
        prob_relevant_without_word = relevant_docs_without_word/len(docs_without_word)
        prob_irrelevant_without_word = 1 - prob_relevant_without_word
        impurity_with_word = 1 - (prob_relevant_with_word**2 + prob_irrelevant_with_word**2)
        impurity_without_word = 1 - (prob_relevant_without_word**2 + prob_irrelevant_without_word**2)
        return impurity_with_word, impurity_without_word
    
    def augment_query(self, current_query, current_results, current_feedback):
        wl, vocab = self.extract_words(current_results)
        inverse_list = {word: set() for word in vocab}
        for i, document in enumerate(wl):
            for word in document['title'] + document['snippet']:
                inverse_list[word].add(i+1)
        all_documents = set(range(1, 10+1))
        percentage_of_relevant_docs = {}
        for word, docs in inverse_list.items():
            number_of_relevant_docs = 0
            for doc in docs:
                number_of_relevant_docs += current_feedback[doc - 1]
            percentage_of_relevant_docs[word] = number_of_relevant_docs/len(docs)
        k = 0.6
        words_to_search = [word for word in vocab if percentage_of_relevant_docs[word]>k]
        ranking = {}
        for word in words_to_search:
            gini = self.gini_impurity(word, inverse_list[word], all_documents - inverse_list[word], feedback = {k+1:f for k, f in enumerate(current_feedback)})
            w1 = len(inverse_list[word])/len(all_documents)
            w2 = 1.0 - w1
            ranking[word] = ( w1*gini[0] + w2*gini[1])
        res = sorted(words_to_search, key= lambda x: ranking[x])
        update = ' ' + res[0] + ' ' + res[1]
        updated_query = current_query + update
        return updated_query, update

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    engine_id = os.environ.get('SEARCH_ENGINE_ID')
    qa = QueryAugmenter()

    results = []
    with open('text_saving/cases.json') as user_file:
        for line in user_file:
            results.append(json.loads(line))

    feedback = [0, 0, 1, 0, 0, 0, 0, 0, 0, 1]

    updated_query, update = qa.augment_query("cases", results, feedback)

    print(updated_query)
