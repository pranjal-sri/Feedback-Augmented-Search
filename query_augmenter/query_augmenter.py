import requests
import json

class QueryAugmenter:
    def __init__(self):
        pass
    
    

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    engine_id = os.environ.get('SEARCH_ENGINE_ID')
