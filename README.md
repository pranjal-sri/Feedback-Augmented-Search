# Feedback-Augmented-Search
**CS6111 Project 1**

**Team:**

- **Your Name:** Pranjal Srivastava
  - **Columbia UNI:** ps3392

- **Teammate's Name:** Shreyas Chatterjee
  - **Columbia UNI:** sc5290

**List of Files:**
1. `main.py`
2. `query_manager.py`
3. `ui_manager.py`
4. `query_augmenter.py`
5. `README.md`
6. (Any other relevant files)

**Running the Program:**

To run the project, follow these steps:

1. **Setting Up Environment:**
   - Ensure you have Python installed on your system.

2. **Install Dependencies:**
    ```bash
    pip3 install -r requirements.txt

3. **Running the main python file:**
    ```bash
    python3 main.py [API_KEY] [SEARCH_ENGINE_ID] [TARGET_PRECISION] [INITIAL_QUERY]


**Internal Design:**

The project consists of the following main components:

**main.py:**
- Orchestrates the overall execution of the project.
- Initiates instances of `QueryManager`, `UIManager`, and `QueryAugmenter`.
- Manages the query feedback loop until the desired precision is reached.

**query_manager.py:**
- Handles communication with the Google Custom Search Engine API.
- Parses and verifies API responses.
- Filters and processes search results.

**ui_manager.py:**
- Manages user interface interactions.
- Displays initial information and feedback summaries.
- Collects user feedback on search results.

**query_augmenter.py:**
- Implements the core query modification method.
- Extracts relevant information from search results.
- Selects new keywords to add in each round based on various criteria.

**Query Modification Method:**

The query modification process involves the following steps:

1. **Extraction of Keywords:**
   - Extracts relevant keywords from the search results' titles and summaries.

2. **Calculating Gini Gain:**
   - Calculates Gini gain for each candidate keyword based on relevance.

3. **Weighting Rankings:**
   - Weights the rankings based on frequency, proximity to the query, and dependency.

4. **Selecting New Keywords:**
   - Selects new keywords with the highest ranking for query augmentation.

**Google Custom Search Engine API Key and Engine ID:**
- **API Key:** [Your API Key]
- **Engine ID:** [Your Engine ID]

**Additional Information:**
- Ensure your Google Custom Search Engine is configured to allow the specified API Key and Engine ID.
- Detailed information on handling non-HTML files is provided in the `query_manager.py` section of the README.