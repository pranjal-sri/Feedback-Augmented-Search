import regex as re
from math import log
import spacy

class QueryAugmenter:
    def __init__(self):
        self.pattern = re.compile(r'''
            ’s|’t|’re|’ve|’m|’ll|’d| ?\p{L}+| ?\p{N}+”
            ''')

        self.nlp = spacy.load("en_core_web_md")

        self.stop_words = set()
        with open('stop_words.txt', 'r') as stop_words_file:
            for line in stop_words_file:
                self.stop_words.add(line.strip())
        self.window_size = 2
        self.k = 0.6
        self.frequency_weight = 1.0
        self.proximity_weight = 1.0
        self.dependency_weight = 2.0
    
    def extract_words(self, result_list, query_terms):
        documents = []
        vocab = set()
        for result in result_list:
            title = result.get('Title', '')
            snippet = result.get('Summary', '')
            title_words = re.findall(self.pattern, title.lower())
            title_words = [word.strip() for word in title_words if (word.strip() not in self.stop_words) 
                                                                        or (word.strip() in query_terms)]
            snippet_words = re.findall(self.pattern, snippet.lower())
            snippet_words = [word.strip() for word in snippet_words if (word.strip() not in self.stop_words) 
                                                                    or (word.strip() in query_terms)]
            
            vocab.update(title_words + snippet_words)
            documents.append({'title': title_words, 'summary': snippet_words})
        return documents, vocab
    
    @staticmethod
    def gini(n_relevant_docs, n_irrelevant_docs):
        eps = 1e-7
        p_relevance = n_relevant_docs/(n_irrelevant_docs+n_relevant_docs+eps)
        p_irrelevance = n_irrelevant_docs/(n_irrelevant_docs+n_relevant_docs+eps)
        return 1 - p_irrelevance**2 - p_relevance**2
    
    def is_query_term_in_window(self, words, index, query_terms):
        for i in range(index - self.window_size, index+self.window_size+1):
            if i < 0 or i>=len(words) or i == index: 
                continue
            if words[i] in query_terms: 
                return True
        
        return False

    def construct_inverse_list(self, documents, vocab, query_terms ):
        inverse_list = {word:{} for word in vocab}
        for doc_i, document in enumerate(documents):
            doc_words = document['title'] + ['\\']*self.window_size + document['summary']
            
            for word_i, word in enumerate(doc_words):
                if word == '\\': 
                    continue

                word_dict = inverse_list[word]
                if doc_i not in inverse_list[word]:
                    word_dict[doc_i] = {'frequency': 0, 'close_to_query': False}
                
                word_dict[doc_i]['frequency'] = word_dict[doc_i]['frequency']+1
                word_dict[doc_i]['close_to_query'] = self.is_query_term_in_window(doc_words, word_i, query_terms)
        
        return inverse_list
                
    def gini_gain(self, word, inverse_list, feedback):
        docs_with_word = list(inverse_list[word])

        all_documents = set(range(0, len(feedback)))
        relevant_docs = set([i for i in range(len(feedback)) if feedback[i] == 1])

        docs_with_word = set(inverse_list[word].keys())
        docs_without_word = all_documents - docs_with_word

        n_relevant_with_word = len(docs_with_word.intersection(relevant_docs))
        n_irrelevant_with_word = len(docs_with_word)- n_relevant_with_word

        n_relevant_without_word = len(docs_without_word.intersection(relevant_docs))
        n_irrelevant_without_word = len(docs_without_word) - n_relevant_without_word

        w1 = len(docs_with_word)/len(all_documents)
        w2 = 1.0 - w1

        base_gini = self.gini(len(relevant_docs), len(all_documents - relevant_docs))
        word_gini = w1*self.gini(n_relevant_with_word, n_irrelevant_with_word) \
                    + w2*self.gini(n_relevant_without_word, n_irrelevant_without_word)

        gini_gain = base_gini-word_gini
        return gini_gain
    
    def get_words_to_search(self, feedback, vocab, query_terms, inverse_list):
        words_to_search = []
        relevant_docs = set([i for i in range(len(feedback)) if feedback[i] == 1])

        for word in vocab:
            if word in query_terms:
                continue
            word_docs = set(inverse_list[word].keys())
            if len(word_docs.intersection(relevant_docs))/len(word_docs) >= self.k:
                words_to_search.append(word)
        
        return words_to_search
    
    def get_gini_rankings(self, words_to_search, inverse_list, feedback):
        rankings = {}
        for word in words_to_search:
            rankings[word] = self.gini_gain(word, inverse_list, feedback)
        
        return rankings
    
    def weigh_ranking_by_frequency(self, rankings, inverse_list, feedback):
        relevant_docs = set([i for i in range(len(feedback)) if feedback[i] == 1])
        for word in rankings.keys():
            word_docs = set(inverse_list[word].keys())
            relevant_word_docs = word_docs.intersection(relevant_docs)
            total_relevant_freq = 0
            for doc in relevant_word_docs:
                total_relevant_freq += 1
            

            rankings[word]+= self.frequency_weight*log(1.0 + total_relevant_freq)
    
    def has_query_terms(self, term_list, query_terms):
      for term in term_list:
          if term.text.lower().strip() in query_terms:
            return True
      return False
    
    def weigh_ranking_by_dependency(self, rankings, results, feedback, query_terms):
        relevant_results = [results[i] for i in range(len(feedback)) if feedback[i] == 1]
        freq_of_dependency = {i:0 for i in rankings.keys()}

        for result in relevant_results:
          doc = self.nlp(result['Summary'])
          for token in doc:
            if token.text.lower().strip() in query_terms:
              for word in token.children:
                if not word.text.lower().strip() in rankings:
                  continue
                freq_of_dependency[word.text.lower().strip()] += 1.0
            if token.dep_ == 'ROOT' and self.has_query_terms(token.children, query_terms):
              for word in token.children:
                if not word.text.lower().strip() in rankings:
                  continue
                freq_of_dependency[word.text.lower().strip()] += 1.1
        
        for word in rankings.keys():
          rankings[word] += self.dependency_weight*log(1.0+freq_of_dependency[word])

    def weigh_ranking_by_proximity(self, rankings, inverse_list, feedback):
        relevant_docs = set([i for i in range(len(feedback)) if feedback[i] == 1])
        for word in rankings.keys():
            word_docs = set(inverse_list[word].keys())
            relevant_word_docs = word_docs.intersection(relevant_docs)
            total_close_to_query_occurences = 0
            for doc in relevant_word_docs:
                if inverse_list[word][doc]['close_to_query']:
                    total_close_to_query_occurences+=1
            
            rankings[word] += self.proximity_weight*log(1.0+total_close_to_query_occurences)

    def augment_query(self, current_query, current_results, current_feedback):
        # import pdb; pdb.set_trace()
        query_terms = current_query.strip().split()
        documents, vocab = self.extract_words(current_results, query_terms)
        inverse_list = self.construct_inverse_list(documents, vocab, query_terms)
        # all_documents = set(range(1, len(documents)+1))
        # percentage_of_relevant_docs = {}
        # for word, docs in inverse_list.items():
        #     number_of_relevant_docs = 0
        #     for doc in docs:
        #         number_of_relevant_docs += current_feedback[doc - 1]
        #     percentage_of_relevant_docs[word] = number_of_relevant_docs/len(docs)
        # k = 0.6
        words_to_search = self.get_words_to_search(current_feedback, vocab, query_terms, inverse_list)
        rankings = self.get_gini_rankings(words_to_search, inverse_list, current_feedback)
        self.weigh_ranking_by_frequency(rankings, inverse_list, current_feedback)
        self.weigh_ranking_by_proximity(rankings, inverse_list, current_feedback)
        self.weigh_ranking_by_dependency(rankings, current_results, current_feedback, query_terms)
        # for word in words_to_search:
        #     gini = self.gini_impurity(inverse_list[word], all_documents - inverse_list[word], feedback = {k+1:f for k, f in enumerate(current_feedback)})
        #     w1 = len(inverse_list[word])/len(all_documents)
        #     w2 = 1.0 - w1
        #     ranking[word] = ( w1*gini[0] + w2*gini[1])

        res = sorted(words_to_search, key= lambda x: -rankings[x])
        update = ' ' + res[0] + ' ' + res[1]
        updated_query = current_query + update
        return updated_query, update
    

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    engine_id = os.environ.get('SEARCH_ENGINE_ID')
    # qa = QueryAugmenter()

    # results = []
    # with open('text_saving/cases.json') as user_file:
    #     for line in user_file:
    #         results.append(json.loads(line))

    # feedback = [0, 0, 1, 0, 0, 0, 0, 0, 0, 1]

    # updated_query, update = qa.augment_query("cases", results, feedback)

    # print(updated_query)
