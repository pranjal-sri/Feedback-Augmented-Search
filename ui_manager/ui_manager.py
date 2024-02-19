import requests
from typing import List
import json

class UIManager:
    # constructor
    def __init__(self, API_KEY, engine_id, target_precision):
        self.API_KEY = API_KEY
        self.engine_id = engine_id
        self.target_precision = target_precision

    # called when initially the query is passed to search API
    def display_initial(self, current_query):
        print(f"\nParameters:")
        print(f"Client key  = {self.API_KEY}")
        print(f"Engine key  = {self.engine_id}")
        print(f"Query       = {current_query}")
        print(f"Precision   = {self.target_precision}")
    
    # called when we have to display the results and take feedback from the user
    def display_and_input_feedback(self, results_dictionary) -> List[int]:
        print("\nGoogle Search Results:")
        print("======================")
        user_feedback = []

        for index, result in enumerate(results_dictionary, 1):
            print(f"\nResult {index}")
            print("[")
            print(f"URL: {result['URL']}")
            print(f"Title: {result['Title']}")
            print(f"Summary: {result['Summary']}")
            print("]\n")

            # we check for lower case input as well, i.e., y/n are also valid inputs
            feedback = input("Relevant (Y/N)?").strip().upper()
            # we keep asking for feedback until user enters a valid feedback
            while feedback not in ['Y', 'N']:
                print("Invalid input. Please enter 'Y' or 'N'.")
                feedback = input("Relevant (Y/N)?").strip().upper()

            user_feedback.append(1 if feedback == 'Y' else 0)

        return user_feedback

    # called when we have to display the results of the search
    def display_feedback_summary(self, current_query, current_precision, update):
        print("\n======================")
        print("FEEDBACK SUMMARY")
        print(f"Query {current_query}")
        print(f"Precision {current_precision}")
        # here update will be None only on the final call of this function
        # i.e., when the current_precision >= self.target_precision meaning program was successfu
        # or when current_precision == 0.0 meaning no relevant document was found
        if update == None:
            if current_precision >= self.target_precision:
                print("Desired precision reached, done.")
            else:
                print("Below desired precision, but can no longer augment the query")
        else:
            # when update is not None, it means that there must be a necessary update to the query
            print(f"Still below the desired precision of {self.target_precision}")
            print("Indexing results ....")
            print("Indexing results ....")
            print(f"Augmenting by {update}")

if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    engine_id = os.environ.get('SEARCH_ENGINE_ID')

    # ui = UIManager(api_key, engine_id, 1)

    # results = []
    # with open('text_saving/cases.json') as user_file:
    #     for line in user_file:
    #         results.append(json.loads(line))

    # feedback = ui.display_and_input_feedback(results)

    # print(feedback)