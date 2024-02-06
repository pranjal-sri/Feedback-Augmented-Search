import sys
from query_manager import QueryManager
# from ui_manager import UIManager
# from query_augmenter import QueryAugmenter
import numpy


DEFAULT_QUERY_MANAGER_CONFIG ={'number_of_results':10,
                                
                                'feature_mapping': {
                                    'link': 'URL',
                                    'title': 'Title',
                                    'snippet': 'Summary'}}


def run(api_key, engine_id, target_precision, INITIAL_QUERY):
    qm = QueryManager(api_key, engine_id, **DEFAULT_QUERY_MANAGER_CONFIG)
    # um = UIManager()
    # qa = QueryAugmenter()

    current_query = INITIAL_QUERY
    current_results = qm.query(current_query)
    # um.display(results)
    # current_feedback = um.get_user_feedback() <An array of 1 and 0>
    current_feedback = None #Replace with line above
    current_precision = __calculate_precision(current_feedback)

    while(current_precision < target_precision): 
        # updated_query = qa.augment_query(current_query, current_results, current_feedback)
        updated_query = None #Replace with line above

        updated_results =  qm.query(updated_query)
        # um.display(updated_results)  
        # updated_feedback = um.get_user_feedback() 
        updated_feedback = None #Replace with line above

        current_precision = __calculate_precision(updated_feedback)
        current_query = updated_query
        current_feedback = updated_feedback
        current_results = updated_results

    # um.end_display()

def __calculate_precision(feedback):
    numpy.mean(feedback)

if __name__ == '__main__':
    API_KEY = sys.argv[1]
    SEARCH_ENGINE_ID = sys.argv[2]
    TARGET_PRECISION = float(sys.argv[3])
    INITIAL_QUERY = sys.argv[4]
    run(API_KEY, SEARCH_ENGINE_ID, TARGET_PRECISION, INITIAL_QUERY)