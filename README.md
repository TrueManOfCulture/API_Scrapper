# API_Scrapper
Python-based API that scrapes package data
## Setup
1. Create virtual environment: (Optional, you can install the package globally and run it without the virtual environment)
```bash
   python -m venv venv
   venv\Scripts\activate
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Run:
```bash
   python main.py
```

## Testing

### Method 1 : 

1. Go to `localhost:8000/docs` to check the documentation and test using SwaggerUI

2. Click on "Try it out"

3. Open `GET /aptoide` and input the package name in the parameter

4. Click on "Execute" and check for the results

### Method 2 : 

1. Using API testing tools like Insomnia or Postman when running the server send a GET request to localhost:8000/aptoide?package_name=com.facebook.katana
