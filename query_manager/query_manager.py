import requests
class QueryManager:

    # initializing object constructor with required parameters
    def __init__(self, API_KEY, engine_id, number_of_results = 10, feature_mapping = None):
        self.API_KEY = API_KEY
        self.engine_id = engine_id
        self.number_of_results = number_of_results
        if feature_mapping is not None:
            self.feature_mapping = feature_mapping
        else: 
            self.feature_mapping = {'link': 'URL',
                                    'title': 'Title',
                                    'snippet': 'Summary'}
    
    def __repr__(self) -> str:
        return f'\nQueryManager(API_KEY={self.API_KEY}, engine_id={self.engine_id},\n number_of_results = {self.number_of_results}, feature_mapping = {self.feature_mapping})'
    
    def query(self, query):
        search_string = f'https://www.googleapis.com/customsearch/v1?key={self.API_KEY}&cx={self.engine_id}&q={query}' 
        
        try:
            response = requests.get(search_string)
            search_results =  response.json()
            # verifying search results as per instructions mentioned in the homework description
            self.__verify_results(search_results)
            items = self.__parse_results(search_results)
            return items
        
        # chekcing for all other types of errors in case of using requests.get()
        except requests.exceptions.Timeout:
            print("QUERY ERROR: Timeout occured")
            raise
        except requests.exceptions.TooManyRedirects:
            print("QUERY ERROR: Too many redirects")
            raise
        except requests.exceptions.JSONDecodeError:
            print("QUERY ERROR: JSON response can't be parsed")
            raise
        except requests.exceptions.RequestException as e:
            print("QUERY ERROR: Connection error")
            raise

    def __verify_results(self, search_results: dict):

        # if search results does not contain the items keyword
        if not 'items' in search_results:
            raise ValueError("QUERY ERROR: API result does not have items")
        
        # if search results does not contain even 10 results irrespective of type i.e., text/html/application/pdf/etc.
        if len(search_results['items']) < self.number_of_results:
            raise ValueError("QUERY ERROR: Too few results")

    def __parse_results(self, search_results):
        # taking the first 10 results only
        results = search_results['items'][:self.number_of_results]
        items = []
        for result in results:
            # we decided to not specifically handle non html files since
            # most of application/pdf type files also contained the 3 things needed by us - link, title and snippet
            # we just check for the presence of those 3 keywords and then do the mapping
            # this ensures that we select x out of first 10 results, where x is emperically observed to be == 10
            if set(self.feature_mapping.keys()).issubset(set(result.keys())):
                item = {mapping: result[feature] for feature, mapping in self.feature_mapping.items()}
                items.append(item)
            else:
                continue
        return items

if __name__ == '__main__':
    pass