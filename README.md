# Setting up the Python environmentn installing dependencies and run the app

1. **Clone the repository**:
  ```
  git clone git@github.com:Mici7120/interactive_job_shop.git
  ```

2. **Create a virtual environment**:

  Navigate to the project directory, create a python virtual environment:
  ```
  python3 -m venv venv
  ```

3. **Activate the virtual environment**:
  - On Windows:
    ```
    venv\Scripts\activate
    ```
  - On macOS/Linux:
    ```
    source venv/bin/activate
    ```

4. **Install dependencies**:

  Run:
  ```
  pip install -r requirements.txt
  ```

4. **Run the flask app**:

  Run the flask app:
  ```
  python app.py
  ```

5. **Navigate to the app**:

  ```
  http://127.0.0.1:5000/
  ```
