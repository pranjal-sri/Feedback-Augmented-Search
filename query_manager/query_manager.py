import requests
import json

class QueryManager:
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
    
    def query(self, query, return_pages = False):
        search_string = f'https://www.googleapis.com/customsearch/v1?key={self.API_KEY}&cx={self.engine_id}&q={query}' 
        
        try:
            response = requests.get(search_string)
            search_results =  response.json()
            self.__verify_results(search_results)
            
            items = self.__parse_results(search_results)

            if not return_pages:
                return items
            
            else:
                pages = self.download_pages(items)
                return items, pages
        
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
        if not 'items' in search_results:
            raise ValueError("QUERY ERROR: API result does not have items")
        
        if len(search_results['items']) < self.number_of_results:
            raise ValueError("QUERY ERROR: Too few results")
        
        for i in range(self.number_of_results):
            if set(self.feature_mapping.keys()) not in set(search_results['items'][i].keys()):
                raise ValueError("QUERY ERROR: Features missing in the response. Check feature_mapping.")

    def __parse_results(self, search_results):
        results = search_results['items'][:self.number_of_results]
        items = []
        for result in results:
            item = {mapping: result[feature] for feature, mapping in self.feature_mapping.items()}
            items.append(item)
        
        return items
    # TODO: Implement download pages
    def download_pages(self, items):
        pass

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    engine_id = os.environ.get('SEARCH_ENGINE_ID')
    qm = QueryManager(api_key,engine_id)
    result = qm.query('per se')
    

    with open('per_se.json', 'w') as file:
        json.dump(result, file)
