import requests
from typing import List

class UIManager:
    def __init__(self, API_KEY, engine_id, target_precision):
        self.API_KEY = API_KEY
        self.engine_id = engine_id
        self.target_precision = target_precision

    def display_initial(self, current_query):
        print(f"\nParameters:")
        print(f"Client key  = {self.API_KEY}")
        print(f"Engine key  = {self.engine_id}")
        print(f"Query       = {current_query}")
        print(f"Precision   = {self.target_precision}")
    
    def display_and_input_feedback(self, results_dictionary) -> List[int]:
        print("\nGoogle Search Results:")
        print("======================")
        user_feedback = []

        for index, result in enumerate(results_dictionary, 1):
            print(f"Result {index}")
            print("[")
            print(f"URL: {result['URL']}")
            print(f"Title: {result['Title']}")
            print(f"Summary: {result['Summary']}\n")
            print("]")

            feedback = input("Relevant (Y/N)?").strip().upper()
            while feedback not in ['Y', 'N']:
                print("Invalid input. Please enter 'Y' or 'N'.")
                feedback = input("Relevant (Y/N)?").strip().upper()

            user_feedback.append(1 if feedback == 'Y' else 0)

        return user_feedback

    def display_feedback_summary(self):
        print("\n======================")
        print("FEEDBACK SUMMARY")
        # think about this

if __name__ == '__main__':
    # complete this
    print("Somehow test this")