# LLM_Working_Using_API

## To Run The LLM 
  * Create a python virual enviroment
  * python -m venv {Your_virtual_enviroment_name}
  * cd {Your_virtual_enviroment_name}/scripts/activate
  * You will get shell like this
    {Your_virtual_enviroment_name}$ pip install -r requirements.txt
  * As requirements.txt will help to install all the python packages

## Using the APIKEY
* create a .env file or use the above sampel .env file
* Load all the variables and the api key into it
* To **FIND ALL THE PUBLIC API** = "https://github.com/public-apis/public-apis"
* Go to the website to sign and create a account to the api
  "https://openweathermap.org/api" - weather data
  "https://spoonacular.com/food-api" - to the wine data
* So I have used a database on cloud to for free
  https://neon.tech/home - to get the database key
POSTGRES_DB_URL=your_postgres_connection_url
OPENAI_API_KEY=your_openai_api_key
SPOONACULAR_API_KEY=your_spoonacular_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

## Now How to Run
  - Data_fetch.py -> To get the weather data in a josn format in both the format "weather_full_data.json and weather_cleaned.json data as we now play round with the cleaned data.
  - wine_fetch.py -> To get the wine data in a cleend json format to play around.
  - merged_data.py -> Now we need to merge both "weather_cleaned.json" data and wine_train.json data to one single json format
  - Database.py -> Now we need to load the "merged_data.json" into the database.
  - llm.py -> now we need to use openai and the database where we have stored the "merged_data.json". When we want to generate the prompt we need to get the llm response should be stored in the database, but we don't what a duplicate entry with the same response. Once when we have the store the response in a new table in the database as it will be faster to fetch using the api.
  - main.py -> - **Endpoints**:
    - `POST /fetch_and_process`: Accepts a query like *“What’s the weather in Paris and what wine suits it?”* Calls the LLM and stores result.
    - `GET /results`: Returns all LLM-generated recommendations, optionally filtered by city.
    - `GET /analysis`: Returns only the latest summary (or latest per city).
   
## RUN PYTEST
 - Catch Bugs Early - You can find issues before they make it to production (like broken routes, DB errors, or incorrect logic).
 - Ensure Code Quality - Tests enforce a contract—if someone changes the logic in main.py, your tests can immediately catch regressions.
 - Enable Confident Refactoring - Want to change something in your code? Run the tests afterward to confirm nothing broke.
 - Automate Validation - Manually checking each endpoint or function is tedious. With pytest, you can validate all endpoints with a single command:
