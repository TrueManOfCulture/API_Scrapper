# API_Scrapper
Python-based API that scrapes package data

## Features

- RESTful API endpoint to retrieve app metadata
- FastAPI with automatic Swagger documentation
- Error handling and input validation
- Virtual environment support

## Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd API_Scrapper

2. Create virtual environment: (Optional, you can install the package globally and run it without the virtual environment)
```bash
   python -m venv venv
   venv\Scripts\activate
```

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

4. Run:
```bash
   python main.py
```

## Usage

### Method 1: Swagger UI

1. Go to `localhost:8000/docs` to check the documentation and test using SwaggerUI

2. Click on "Try it out"

3. Open `GET /aptoide` and input the package name in the parameter

4. Click on "Execute" and check for the results

### Method 2: Direct API Calls

curl "http://localhost:8000/aptoide?package_name=com.facebook.katana"

### Method 3: API Clients

1. Using API testing tools like Insomnia or Postman when running the server send a GET request to localhost:8000/aptoide?package_name=com.facebook.katana

### Example Package Names

- com.whatsapp

- com.facebook.katana

- com.spotify.music

## Assumptions and Design Decisions

I created a model for the JSON response that has the same fields as the example presented in the challenge, this is assuming the response has to return these even if they're null.

I assumed that was all the relevant information required specially after checking the info section in the app's page, apk information could be added if that is considered relevant.

The regex used to search and scrape information was done by comparing the example and 2-3 apps in aptoide website, if there are different requirements for how a package name is defined, like it always starts with com. that could be fixed to verify for valid package names.
