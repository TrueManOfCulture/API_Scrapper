"""
Aptoide Scraper API
A FastAPI-based REST API that scrapes package metadata from Aptoide app store.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aptoide Scraper API",
    description="REST API to scrape package metadata from Aptoide app store",
)

#Response model for app metadata
class AppMetadata(BaseModel):
    name: Optional[str] = Field(None, description="App name")
    size: Optional[str] = Field(None, description="App size")
    downloads: Optional[str] = Field(None, description="Number of downloads")
    version: Optional[str] = Field(None, description="App version")
    release_date: Optional[str] = Field(None, description="Release date")
    min_screen: Optional[str] = Field(None, description="Minimum screen size")
    supported_cpu: Optional[str] = Field(None, description="Supported CPU architecture")
    package_id: Optional[str] = Field(None, description="Package identifier")
    sha1_signature: Optional[str] = Field(None, description="SHA1 signature")
    developer_cn: Optional[str] = Field(None, description="Developer common name")
    organization: Optional[str] = Field(None, description="Organization name")
    local: Optional[str] = Field(None, description="Developer location")
    country: Optional[str] = Field(None, description="Country code")
    state_city: Optional[str] = Field(None, description="State/City")

#Service class to handle Aptoide scraping logic
class AptoideScraperService:
    
    SEARCH_API_URL = "https://ws2-cache.aptoide.com/api/7/apps/search"
    TIMEOUT = 30.0
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    #Search for app using Aptoide API and get the app URL
    async def search_app_by_package(self, package_name: str) -> dict:
        
        try:
            params = {
                'query': package_name,
                'limit': 10
            }
            
            async with httpx.AsyncClient(headers=self.headers, timeout=self.TIMEOUT) as client:
                response = await client.get(self.SEARCH_API_URL, params=params)
                
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, 
                                      detail=f"Aptoide API returned HTTP {response.status_code}")
                
                data = response.json()
                
                if 'datalist' in data and 'list' in data['datalist']:
                    apps = data['datalist']['list']
                    
                    for app in apps:
                        if app.get('package') == package_name:
                            uname = app.get('uname', '')
                            store_name = app.get('store', {}).get('name', '')
                            
                            if uname:
                                app_url = f"https://{uname}.en.aptoide.com/app"
                            elif store_name:
                                app_url = f"https://{store_name}.en.aptoide.com/{package_name}"
                            else:
                                slug = package_name.replace('.', '-')
                                app_url = f"https://{slug}.en.aptoide.com/app"
                            
                            return {
                                'url': app_url,
                            }
                
                raise HTTPException(
                    status_code=404,
                    detail=f"Package '{package_name}' not found on Aptoide. Make sure the package name is correct."
                )
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timeout while searching Aptoide")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise HTTPException(status_code=503, detail="Unable to connect to Aptoide API")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error searching for package: {str(e)}")
    
    #Fetch the Aptoide page HTML
    async def fetch_page(self, url: str) -> str:
        
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.TIMEOUT, follow_redirects=True) as client:
                response = await client.get(url)
                
                if response.status_code == 404:
                    raise HTTPException(status_code=404, detail=f"App page not found at {url}")
                elif response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, 
                                      detail=f"Failed to fetch app page: HTTP {response.status_code}")
                
                return response.text
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timeout while fetching app page")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise HTTPException(status_code=503, detail="Unable to connect to Aptoide")
    
    #Parse HTML and extract app metadata, enriched with API data, basically scrapping it
    def parse_metadata(self, html: str, package_name: str) -> dict:
        
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {"package_id": package_name}
        
        # Extract app name
        name_elem = soup.find('h1', class_=re.compile(r'app-name|appName|app_name'))
        if not name_elem:
            name_elem = soup.find('h1')
        if name_elem:
            metadata['name'] = name_elem.get_text(strip=True)
        
        # Extract metadata from page content
        # Look for structured data in the page
        page_text = soup.get_text()
        
        # Extract Size
        size_match = re.search(r'Size:\s*(\d+\.?\d*\s*[KMGT]B)', page_text, re.IGNORECASE)
        if size_match:
            metadata['size'] = size_match.group(1)
        
        # Extract Downloads
        downloads_match = re.search(r'Downloads?:\s*([\d\.]+[KMB]?)', page_text, re.IGNORECASE)
        if downloads_match:
            metadata['downloads'] = downloads_match.group(1)
        
        # Extract Version
        version_match = re.search(r'Version\s*:?\s*(\d+\.[\d\.]+)', page_text, re.IGNORECASE)
        if version_match:
            metadata['version'] = version_match.group(1)
        
        # Extract Release Date
        date_match = re.search(r'Release Date:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', page_text)
        if date_match:
            metadata['release_date'] = date_match.group(1)
        
        # Extract Min Screen
        screen_match = re.search(r'Min Screen:\s*(\w+)', page_text, re.IGNORECASE)
        if screen_match:
            min_screen = screen_match.group(1).upper()
            metadata['min_screen'] = min_screen.removesuffix('SUPPORTED')
        
        # Extract Supported CPU
        cpu_match = re.search(r'Supported CPU:\s*([^\n]+)', page_text, re.IGNORECASE)
        if cpu_match:
            cpu_text = cpu_match.group(1).strip()
            cpu_text = re.split(r'Package ID|SHA1|Signature|\s{3,}', cpu_text, maxsplit=1)[0].strip()
            # Remove extra whitespace
            cpu_text = re.sub(r'\s+', ' ', cpu_text)
            if cpu_text and cpu_text not in ['', '-', 'None']:
                metadata['supported_cpu'] = cpu_text
        
        # Extract Package ID (verify)
        pkg_match = re.search(r'Package ID:\s*([a-zA-Z0-9._]+)', page_text)
        if pkg_match and pkg_match.group(1) == package_name:
            metadata['package_id'] = pkg_match.group(1)
        
        # Extract SHA1 Signature
        sha1_match = re.search(r'SHA1 Signature:\s*([A-F0-9:]{59})', page_text, re.IGNORECASE)
        if sha1_match:
            metadata['sha1_signature'] = sha1_match.group(1).upper()
        
        # Extract Developer CN
        dev_match = re.search(r'Developer\s*\(CN\):\s*([^\n]+)', page_text, re.IGNORECASE)
        if dev_match:
            dev_name = dev_match.group(1).strip()
            
            dev_name = re.split(r'Organization|Local|\s{2,}', dev_name, maxsplit=1)[0].strip()
            if dev_name and dev_name not in ['', '-', 'None']:
                metadata['developer_cn'] = dev_name
        
        # Extract Organization
        org_match = re.search(r'Organization\s*\(O\):\s*([^\n]+)', page_text, re.IGNORECASE)
        if org_match:
            org_name = org_match.group(1).strip()
            # Clean up - stop at Local or next section
            org_name = re.split(r'Local|Country|\s{2,}', org_name, maxsplit=1)[0].strip()
            if org_name and org_name not in ['', '-', 'None']:
                metadata['organization'] = org_name
        
        # Extract Local
        local_match = re.search(r'Local\s*\(L\):\s*([^\n]+)', page_text, re.IGNORECASE)
        if local_match:
            local_name = local_match.group(1).strip()
            # Clean up - stop at Country or next section
            local_name = re.split(r'Country|State|\s{2,}', local_name, maxsplit=1)[0].strip()
            if local_name and local_name not in ['', '-', 'None']:
                metadata['local'] = local_name
        
        # Extract Country
        country_match = re.search(r'Country\s*\(C\):\s*([A-Z]{2}|[^\n]+)', page_text, re.IGNORECASE)
        if country_match:
            country_code = country_match.group(1).strip()
            
            country_code = re.split(r'State|Local|\s{2,}', country_code, maxsplit=1)[0].strip()
            # If it's a valid 2-letter code, use it
            if len(country_code) == 2 and country_code.isalpha():
                metadata['country'] = country_code.upper()
            elif country_code and country_code not in ['', '-', 'None']:
                # Try to extract 2-letter code from longer text
                code_match = re.search(r'\b([A-Z]{2})\b', country_code)
                if code_match:
                    metadata['country'] = code_match.group(1)
                else:
                    metadata['country'] = country_code
        
        # Extract State/City
        state_match = re.search(r'State/City\s*\(ST\):\s*(\w+[^\n])', page_text, re.IGNORECASE)
        if state_match:
            state_name = state_match.group(1).strip()
            state_name = re.split(r'What|How|Can|Why|Where|Package ID|SHA1|FAQ|Download|Ratings|About|Description|\?|Latest', state_name, maxsplit=1)[0].strip()
            if any(word in state_name.lower() for word in ['what is', 'how to', 'can i', 'download', 'app?', 'facebook app', 'whatsapp']):
                location_match = re.match(r'^([A-Za-z\s]+?)(?=What|How|Can|Why|$)', state_name)
                if location_match:
                    state_name = location_match.group(1).strip()
                else:
                    state_name = None
            
            if state_name and state_name not in ['', '-', 'None'] and len(state_name) < 50:
                metadata['state_city'] = state_name
        
        # Set None for any empty or missing fields
        for key in metadata:
            if metadata[key] in ['', '-', 'None']:
                metadata[key] = None
        
        return metadata
    
    async def scrape_package(self, package_name: str) -> AppMetadata:
        """Main method to scrape package data"""
        logger.info(f"Scraping package: {package_name}")
        
        search_result = await self.search_app_by_package(package_name)
        app_url = search_result['url']
        
        logger.info(f"Found app at: {app_url}")
        
        html = await self.fetch_page(app_url)
        
        metadata = self.parse_metadata(html, package_name)
        
        return AppMetadata(**metadata)


scraper_service = AptoideScraperService()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Aptoide Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/aptoide?package_name=<package_id>",
            "docs": "/docs",
            "health": "/health"
        },
        "example": "curl 'http://localhost:8000/aptoide?package_name=com.whatsapp'"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/aptoide", response_model=AppMetadata)
async def scrape_aptoide_package(
    package_name: str = Query(
        ...,
        description="Package identifier (e.g., com.facebook.katana)",
        min_length=3,
        max_length=255,
        regex=r'^[a-zA-Z0-9._-]+$'
    )
):
    """
    Scrape package metadata from Aptoide app store
    
    This endpoint searches for an app by its package name using the Aptoide API,
    then scrapes the app page to extract comprehensive metadata.
    
    Args:
        package_name: The Android package identifier (e.g., com.facebook.katana)
    
    Returns:
        AppMetadata: JSON object containing app metadata including name, version,
                     size, downloads, certificate info, and more.
    
    Raises:
        HTTPException: If package not found or scraping fails
    
    Example:
        GET /aptoide?package_name=com.whatsapp
    """
    try:
        metadata = await scraper_service.scrape_package(package_name)
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)