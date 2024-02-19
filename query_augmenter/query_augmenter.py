import regex as re
from math import log
import spacy
from itertools import permutations

class QueryAugmenter:
    def __init__(self):
        self.pattern = re.compile(r"’s|’t|’re|’ve|’m|’ll|’d| ?\w+")

        self.nlp = spacy.load("en_core_web_md")

        self.stop_words = set()
        with open(
            "./stop_words.txt", "r"
        ) as stop_words_file:
            for line in stop_words_file:
                self.stop_words.add(line.strip())
        self.window_size = 2
        self.k = 0.6 # min ratio of relevant docs for selecting words_to_search
        self.frequency_weight = 1.0
        self.dependency_weight = 1.0
        self.threshold_for_append = 0.2

    def augment_query(self, current_query, current_results, current_feedback):
        '''
        augments a query based on feedback and the results.
        '''
        # terms in the query
        query_terms = current_query.strip().split()

        # filtered words and the vocab in the results
        documents, vocab = self.extract_words(current_results, query_terms)
        # Step 1: get the inverse lists for words
        inverse_list = self.construct_inverse_list(documents, vocab, query_terms)

        # Step 2: candidate words to append in the query
        words_to_search = self.get_words_to_search(
            current_feedback, vocab, query_terms, inverse_list
        )
        words_to_search.extend(query_terms) # We want to also rank the query terms for ordering

        # Step 3: get gini rankings, enhanced by frequency and dependency weights
        rankings = self.get_gini_rankings(
            words_to_search, inverse_list, current_feedback
        )
        self.weigh_ranking_by_frequency(rankings, inverse_list, current_feedback)
        self.weigh_ranking_by_dependency(
            rankings, current_results, current_feedback, query_terms
        )

        # Step 4: Choose new words and the new order to append, return the new query
        return self.get_new_query(rankings, current_results, current_feedback, query_terms)

    def extract_words(self, result_list, query_terms):
        """
        parses the results to convert all words to lowercase and eliminate any stop words in the results.
        Returns a dictionary of the same format as results (dict with "title" and "summary" keys).
        """
        documents = []
        vocab = set()
        for result in result_list:
            title = result.get("Title", "")
            snippet = result.get("Summary", "")
            
            title_words = re.findall(self.pattern, title.lower())
            title_words = [
                word.strip()
                for word in title_words
                if (word.strip() not in self.stop_words) # Filter all the stop words
                or (word.strip() in query_terms) # Do not filter query terms
            ]

            snippet_words = re.findall(self.pattern, snippet.lower())
            snippet_words = [
                word.strip()
                for word in snippet_words
                if (word.strip() not in self.stop_words) # Filter all the stop words 
                or (word.strip() in query_terms) # Do not filter query terms
            ]
            
            vocab.update(title_words + snippet_words)
            documents.append({"title": title_words, "summary": snippet_words})
        return documents, vocab

    def is_query_term_in_window(self, words, index, query_terms):
        """
        takes a list of words, and an index. Returns true if any word of the query_terms is
        within a window of the index parametrised by self.window_size
        """
        for i in range(index - self.window_size, index + self.window_size + 1):
            if i < 0 or i >= len(words) or i == index:
                continue
            if words[i] in query_terms:
                return True

        return False

    def construct_inverse_list(self, documents, vocab, query_terms):
        """
        Constructs inverse list which has entries of the form:
        {word: {doc_i: {'frequency': int, 'close_to_query': True/False}}}
        """
        # Intialise empty word_dicts for each word
        inverse_list = {word: {} for word in vocab}

        for doc_i, document in enumerate(documents):
            # All the words in a document
            # We append '\' as an extra character separating title and summary
            doc_words = (
                document["title"] + ["\\"] * self.window_size + document["summary"]
            )

            for word_i, word in enumerate(doc_words):
                if word == "\\":
                    continue

                # Get the word_dict associated with the word
                word_dict = inverse_list[word]
                if doc_i not in inverse_list[word]:
                    # If the word_dict does not have the current_document, initialise it
                    word_dict[doc_i] = {"frequency": 0, "close_to_query": False}

                # Update frequency and close_to_query
                word_dict[doc_i]["frequency"] = word_dict[doc_i]["frequency"] + 1
                word_dict[doc_i]["close_to_query"] = self.is_query_term_in_window(
                    doc_words, word_i, query_terms
                )

        return inverse_list

    @staticmethod
    def gini(n_relevant_docs, n_irrelevant_docs):
        """
        Calculates gini impurity of a given set of documents with
        n_relevant_docs and n_irrelevant_docs
        """
        eps = 1e-7
        p_relevance = n_relevant_docs / (n_irrelevant_docs + n_relevant_docs + eps)
        p_irrelevance = n_irrelevant_docs / (n_irrelevant_docs + n_relevant_docs + eps)
        return 1 - p_irrelevance**2 - p_relevance**2

    def gini_gain(self, word, inverse_list, feedback):
        """
        Return gini gain of a word based on documents it is present in and not present in.
        """
        docs_with_word = list(inverse_list[word])

        all_documents = set(range(0, len(feedback)))
        relevant_docs = set([i for i in range(len(feedback)) if feedback[i] == 1])

        docs_with_word = set(inverse_list[word].keys())
        docs_without_word = all_documents - docs_with_word

        n_relevant_with_word = len(docs_with_word.intersection(relevant_docs))
        n_irrelevant_with_word = len(docs_with_word) - n_relevant_with_word

        n_relevant_without_word = len(docs_without_word.intersection(relevant_docs))
        n_irrelevant_without_word = len(docs_without_word) - n_relevant_without_word

        w1 = len(docs_with_word) / len(all_documents)
        w2 = 1.0 - w1

        # gini of the base results
        base_gini = self.gini(len(relevant_docs), len(all_documents - relevant_docs))

        # gini after dividing the results into docs with the word, and docs without the word
        word_gini = w1 * self.gini(n_relevant_with_word, n_irrelevant_with_word) \
                    + w2 * self.gini(n_relevant_without_word, n_irrelevant_without_word)

        gini_gain = base_gini - word_gini
        return gini_gain

    def get_words_to_search(self, feedback, vocab, query_terms, inverse_list):
        '''
        Returns a list of words which have a higher ratio of relevant docs in their inverse list
        than self.k
        '''
        words_to_search = []
        relevant_docs = set([i for i in range(len(feedback)) if feedback[i] == 1])

        for word in vocab:
            if word in query_terms:
                continue
            # all the documents that have the word
            word_docs = set(inverse_list[word].keys())

            # if ratio of relevant docs with word to all docs with word is greater than k
            if len(word_docs.intersection(relevant_docs)) / len(word_docs) >= self.k:
                words_to_search.append(word)
        # if we get atleast 2 words to search, we return the list, else we repeat the process with lower k
        if len(words_to_search) >= 2:
            return words_to_search
        else:
            self.k = self.k - 0.1
            return self.get_words_to_search(feedback, vocab, query_terms, inverse_list)

    def get_gini_rankings(self, words_to_search, inverse_list, feedback):
        '''
        returns gini_rankings of words in words_to_search
        '''
        rankings = {}
        for word in words_to_search:
            rankings[word] = self.gini_gain(word, inverse_list, feedback)

        return rankings

    def weigh_ranking_by_frequency(self, rankings, inverse_list, feedback):
        '''
        Enhances the ranking of words based on frequency in relevant docs
        '''
        relevant_docs = set([i for i in range(len(feedback)) if feedback[i] == 1])
        for word in rankings.keys():
            word_docs = set(inverse_list[word].keys())
            relevant_word_docs = word_docs.intersection(relevant_docs)

            # Count total occurences in relevant docs of the word
            total_relevant_freq = 0
            for doc in relevant_word_docs:
                total_relevant_freq += inverse_list[word][doc]['frequency']

            # enhance ranking of the word by tf_word = log(1+f_word) 
            rankings[word] += self.frequency_weight * log(1.0 + total_relevant_freq)

    def has_query_terms(self, term_list, query_terms):
        '''
        Returns true if a term_list has any word from query_terms.
        '''
        for term in term_list:
            if term.lower().strip() in query_terms:
                return True
        return False

    def weigh_ranking_by_dependency(self, rankings, results, feedback, query_terms):
        '''
        Uses dependency parsing, and adds weightage to all the words that are related to 
        the query terms syntactically.  
        '''
        # all the relevant result blocks
        relevant_results = [
            results[i] for i in range(len(feedback)) if feedback[i] == 1
        ]
        # initialise the freq of occurence of a word in a dependency to query terms as 0
        freq_of_dependency_occurence = {i: 0 for i in rankings.keys()}

        for result in relevant_results:
            doc = self.nlp(result["Summary"])
            for token in doc:
                # all the text in token
                token_text = list(re.findall(self.pattern, token.text))
                
                # all the text in children of token
                token_children = []
                for child in token.children:
                    token_children.extend(list(re.findall(self.pattern, child.text)))

                # if token_text has any query term, increase the frequency of all dependent children
                if self.has_query_terms(token_text, query_terms):
                    for word in token_children:
                        if word.lower().strip() not in rankings:
                            continue
                        freq_of_dependency_occurence[word.lower().strip()] += 1.0
                # if token is a root token, and children has any query term, 
                # increase the frequency of all children
                elif token.dep_ == "ROOT" and self.has_query_terms(
                    token_children, query_terms
                ):
                    for word in token_children:
                        if word.lower().strip() not in rankings:
                            continue
                        freq_of_dependency_occurence[word.lower().strip()] += 1.0

        # enhance the rankings of all words by log(1+d_word)
        for word in rankings.keys():
            rankings[word] += self.dependency_weight * log(
                1.0 + freq_of_dependency_occurence[word]
            )


    def get_new_query(self, rankings, current_results, current_feedback, current_query_terms):
        """
        Takes rankings and current_query_terms to generate a new query by choosing new
        words to append and the ordering of the new query. Uses n-grams logic for reordering.
        """
        # Keep a track of relevant results
        relevant_results = []
        # We need the combined string of relevant documents
        for i in range(len(current_results)):
            if current_feedback[i] == 1:
                result = current_results[i]
                final_string = result['Title'] + '' + result['Summary']
                final_words  = [w.strip().lower() for w in re.findall(self.pattern, final_string)]
                final_string = " ".join(final_words)
                relevant_results.append(final_string)

        # Initial query terms have to be included in the new query
        new_query_terms = [term for term in current_query_terms]

        # Only terms other than query terms are ranked as candidates
        possible_append_terms = [term for term in rankings.keys() if term not in current_query_terms]
        candidates = sorted(possible_append_terms, key=lambda x: -rankings[x])[:2]

        # If the difference in rankings of the top 2 candidates is more than threshold_for_append,
        # then only include the top candidate, else include both the candidates
        if rankings[candidates[0]] - rankings[candidates[1]] <= self.threshold_for_append:
            appended_terms = candidates[0], candidates[1]
            new_query_terms.extend([candidates[0], candidates[1]])
        else:
            appended_terms = candidates[0]
            new_query_terms.append(candidates[0])

        # Reorder the new query terms using the order with the highest subsequence count
        reordered_terms = self.reorder(new_query_terms, relevant_results)

        return " ".join(reordered_terms), appended_terms
    
    def reorder(self, terms, original_relevant_docs):
        """
        Reorders terms based on their subsequence count in original relevant documents.
        """
        orders = []

        # Create permutations of orderings
        n = len(terms)
        orders.extend(permutations(terms, n))

        # Calculate the score of each order based on the number of occurences of the order subsequence in the corpus
        order_scores = {
            order: sum(self.subsequence_count_of_order(order, doc) for doc in original_relevant_docs) 
            for order in orders
        }

        # Sort orders based on their subsequence count scores
        sorted_orders = sorted(order_scores.keys(), key=lambda x: -order_scores[x])
        
        # Reorder terms based on the order with highest subsequence count
        reordered_terms = [term for term in sorted_orders[0]]
        
        return reordered_terms

    def subsequence_count_of_order(self, order, doc):
        '''
        Returns the number of times a particular order has appeared in the doc in that same order of words
        '''
        subsequence_pat = re.compile('.*?' + '.*?'.join(order) + '.*?')
        return len(re.findall(subsequence_pat, doc))


if __name__ == "__main__":
    pass
