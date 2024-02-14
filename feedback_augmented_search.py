import sys
from query_manager import QueryManager
from ui_manager import UIManager
from query_augmenter import QueryAugmenter
import numpy


DEFAULT_QUERY_MANAGER_CONFIG ={'number_of_results':10,
                                
                                'feature_mapping': {
                                    'link': 'URL',
                                    'title': 'Title',
                                    'snippet': 'Summary'}}


def run(api_key, engine_id, target_precision, INITIAL_QUERY):
    qm = QueryManager(api_key, engine_id, **DEFAULT_QUERY_MANAGER_CONFIG)
    um = UIManager(api_key, engine_id, target_precision)
    qa = QueryAugmenter()

    current_query = INITIAL_QUERY
    um.display_initial(current_query)
    current_results = qm.query(current_query)
    current_feedback = um.display_and_input_feedback(current_results)
    current_precision = __calculate_precision(current_feedback)

    while(current_precision < target_precision and current_precision != 0.0):
        updated_query, update = qa.augment_query(current_query, current_results, current_feedback)
        um.display_feedback_summary(current_query, current_precision, update)
        um.display_initial(updated_query)
        updated_results =  qm.query(updated_query)
        updated_feedback = um.display_and_input_feedback(updated_results)
        current_precision = __calculate_precision(updated_feedback)
        current_query = updated_query
        current_feedback = updated_feedback
        current_results = updated_results

    um.display_feedback_summary(current_query, current_precision, None)

def __calculate_precision(feedback):
    return numpy.mean(feedback)

if __name__ == '__main__':
    API_KEY = sys.argv[1]
    SEARCH_ENGINE_ID = sys.argv[2]
    TARGET_PRECISION = float(sys.argv[3])
    INITIAL_QUERY = sys.argv[4]
    run(API_KEY, SEARCH_ENGINE_ID, TARGET_PRECISION, INITIAL_QUERY)