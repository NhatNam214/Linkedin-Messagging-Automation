import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from urllib.parse import quote

from utils import getCSV, phantom_fetch_output
from scrap.companyURLFind import CompanyURLFinder
from scrap.companyScraper import CompanyScraper
from scrap.searchExport import SearchExport
from outreachMessage import OutreachMessageGenerator
from JSONResponse import JSONResponse
from dotenv import load_dotenv
load_dotenv()
import time
def create_outreach_message(row):
    time.sleep(10)  # To avoid hitting the API rate limit
    generator = OutreachMessageGenerator(api_key=os.getenv("GOOGLE_API_KEY"))
    message = generator.generate_message(
        fullName=row["fullName"],
        jobTitle=row["jobTitle"],
        companyName=row["companyName"],
        description=row["description"],
        additional_context='''We’ve recently launched a new line of solar battery products that leverages advanced technology to enhance energy conversion efficiency and extend battery lifespan. 
        The solution is designed for both businesses and households seeking a more sustainable and cost-effective approach to energy usage. 
        I'm looking to connect with professionals in the clean energy space to exchange insights, explore potential collaborations, and discuss market opportunities where this solution can make a real impact.   
        ''',
        writing_style="Casual yet professional. Friendly greeting, acknowledges expertise, and includes a polite call to action."
    )

    print(message)
    return message
def simplify_url(url):
    return url.lower().replace("www.", "").rstrip("/")
def safe_str(val):
    if pd.isna(val):
        return ""
    return str(val)
def find_company_urls(spreadsheet_url:str) -> tuple[bool, str]:
    try:
        # Initialize scrapper
        scrapper = CompanyURLFinder(
            api_key=os.getenv("PHANTOM_API_KEY"),
            agent_id=os.getenv("COMPANY_URL_FINDER_API"),
            spreadsheet_url=spreadsheet_url,
        )
        # Launch scraping agent
        scrapper.launch_agent()

        # Fetch output URL from the agent
        csv_url = phantom_fetch_output(
            os.getenv("COMPANY_URL_FINDER_API"),
            os.getenv("PHANTOM_API_KEY")
        )
        if not csv_url:
            return None

        df = getCSV(csv_url, columns=["query","linkedinUrl"])
        if df is None or df.empty:
            return None
        df = df[df["query"] == spreadsheet_url]
        companyURL = df["linkedinUrl"].iloc[0]
        print("query:", spreadsheet_url)
        print("companyURL:", companyURL)
        return companyURL
    except Exception as e:
        raise Exception(f"find_company_urls failed: {str(e)}")
def scrpap_company(companyURL:str) -> tuple[dict, list[str]]:
    # roles = [
    #     "Chairman", "Chairwoman", "CEO", "President", "Founder", "Co-Founder",
    #     "COO", "CFO", "CMO", "CTO", "CIO", "CLO", "CHRO", "CDO", "CSO", "CCO", "CAO", "CPO", "CXO",
    #     "Board Member", "Owner", "Partner", "Proprietor",
    #     "Director", "Head of", "Principal", "Lead", "Leader",
    #     "Manager", "Controller", "Treasurer", "Supervisor",
    #     "Coordinator", "Administrator", "Accountant", "Senior"
    # ]
    roles = [
        "CEO", "Manager"
    ]
    try:
        # Initialize scraper
        scrapper = CompanyScraper(
            api_key=os.getenv("PHANTOM_API_KEY"),
            agent_id=os.getenv("COMPANY_SCRAPER_API"),
            spreadsheetUrl=companyURL,
            sessionCookie=os.getenv("SESSION_COOKIE")
        )
        # Launch scraping agent
        scrapper.launch_agent()

        # Get output CSV URL
        csv_url = phantom_fetch_output(
            os.getenv("COMPANY_SCRAPER_API"),
            os.getenv("PHANTOM_API_KEY")
        )
        if not csv_url:
            return None
        df = getCSV(csv_url, columns=["companyName", "companyUrl", "linkedinID", "description"])
        if df is None or df.empty:
            return None
        df = df.rename(columns={'linkedinID': 'companyID'})
        companyURL_simplified = simplify_url(companyURL)
        df["companyUrl"] = df["companyUrl"].apply(simplify_url)

        # Lọc theo URL đã chuẩn hóa
        df = df[df["companyUrl"] == companyURL_simplified]
        data = df.iloc[0].to_dict()
        
        company_id = data['companyID']
        company_name = quote(data['companyName'])
        search_urls = []
        
        for role in roles:
            encoded_role = quote(role)
            search_url = (
                f"https://www.linkedin.com/search/results/people/?currentCompany=%5B%22{company_id}%22%5D"
                f"&keywords={company_name}&titleFreeText={encoded_role}"
            )
            search_urls.append(search_url)
        return data, search_urls
    except Exception as e:
        raise Exception(f"scrpap_company failed: {str(e)}")

def ExportProfilesAndGenMessages(search_url:str) -> tuple[bool, str]:
    try:
        # Step 1: Export profiles from search agent
        scrapper = SearchExport(
            api_key=os.getenv("PHANTOM_API_KEY"),
            agent_id=os.getenv("SEARCH_EXPORT_API"),
            linkedInSearchUrl=search_url,
            identityId=os.getenv("IDENTITY_ID"),
            sessionCookie=os.getenv("SESSION_COOKIE"),
        )
        scrapper.launch_agent()

        # Step 2: Fetch exported CSV
        csv_url = phantom_fetch_output(
            os.getenv("SEARCH_EXPORT_API"),
            os.getenv("PHANTOM_API_KEY")
        )
        print("csv_url", csv_url)
        if not csv_url:
            return None
        
        data = getCSV(csv_url,columns=["query","fullName", "jobTitle","profileUrl", "error"])
        if data is None or data.empty:
            return None
        print("data", data)
        data = data[data["query"] == search_url].iloc[0].to_dict()
        if not data.get("error"):
            return None
        data.pop("error", None)
        data.pop("query", None)
        return data
    except Exception as e:
        raise Exception(f"ExportProfilesAndGenMessages failed: {str(e)}")

def crawl_generate(query:str, id:int) -> JSONResponse:
    """
    Function to crawl and generate outreach messages based on a given query.
    
    Args:
        query (str): The search query to use for crawling LinkedIn profiles.
    
    Returns:
        str: The generated outreach message.
    """
    try:
       
        # Step 1: Find company URLs
        companyURL = find_company_urls(query)
        if not companyURL:
            return JSONResponse(
                id=id,
                query=query,
                companyName="",
                companyID="",
                companyUrl="",
                description="",
                fullName="",
                jobTitle="",
                profileUrl="",
                outreachMessage="",
                status=3,
            )
        # Step 2: Scrape company details
        company, search_urls = scrpap_company(companyURL)
        if not company:
            return JSONResponse(
                id=id,
                query=query,
                companyName="",
                companyID="",
                companyUrl="",
                description="",
                fullName="",
                jobTitle="",
                profileUrl="",
                outreachMessage="",
                status=3,
            )
        # Step 3: Export profiles and generate messages
        for search_url in search_urls:
            print("search_url", search_url)
            user = ExportProfilesAndGenMessages(search_url)
            if not user:
                continue
            print("user", user) 
            profile_url = user.get("profileUrl")
            if not profile_url or pd.isna(profile_url):
                continue  
            data = user.copy()
            data["companyName"] = company["companyName"]
            data["companyUrl"] = company["companyUrl"]
            data["companyID"] = company["companyID"]
            data["description"] = company["description"]    
            # Step 4: Generate outreach message
            outreach_message = create_outreach_message(data)
            data["outreachMessage"] = outreach_message
            print("data", data)
            return JSONResponse(
                id=id,
                query=query,
                companyName=safe_str(data["companyName"]),
                companyID=safe_str(data["companyID"]),
                companyUrl=safe_str(data["companyUrl"]),
                description=safe_str(data["description"]),
                fullName=safe_str(data["fullName"]),
                jobTitle=safe_str(data["jobTitle"]),
                profileUrl=safe_str(data["profileUrl"]),
                outreachMessage=safe_str(data["outreachMessage"]),
                status=1,
            )
        print("No valid profiles found")
        return JSONResponse(
            id=id,
            query=query,
            companyName="",
            companyID="",
            companyUrl="",
            description="",
            fullName="",
            jobTitle="",
            profileUrl="",
            outreachMessage="",
            status=3,
        )
    except Exception as e:
        raise Exception(f"crawl_generate failed: {str(e)}")
    

    
    