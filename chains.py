import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

load_dotenv()

class Chain:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY not found in .env file")
        
        self.llm = ChatGroq(
            temperature=0, 
            groq_api_key=api_key, 
            model_name="llama-3.3-70b-versatile"
        )

    def extract_jobs(self, cleaned_text):
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the following keys: 
            `role`, `experience`, `skills` and `description`.
            Only return the valid JSON.
            
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm
        
        try:
            # Limit text to avoid token overflow
            limited_text = cleaned_text[:4000] if len(cleaned_text) > 4000 else cleaned_text
            res = chain_extract.invoke(input={"page_data": limited_text})
            
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
            
            return res if isinstance(res, list) else [res]
            
        except OutputParserException:
            # Try with smaller text
            try:
                limited_text = cleaned_text[:2000]
                res = chain_extract.invoke(input={"page_data": limited_text})
                json_parser = JsonOutputParser()
                res = json_parser.parse(res.content)
                return res if isinstance(res, list) else [res]
            except:
                raise OutputParserException("Context too big. Unable to parse jobs.")
        except Exception as e:
            raise Exception(f"Error extracting jobs: {str(e)}")

    def write_mail(self, job, links, person_name="Locket", company_name="CogniCore", person_role="Business Development Executive"):
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            {job_description}

            ### INSTRUCTION:
            You are {person_name}, {person_role} at {company_name}.
            
            COMPANY PROFILE:
            {company_name} is an AI & Software Consulting company dedicated to facilitating
            the seamless integration of business processes through automated tools. 
            Over our experience, we have empowered numerous enterprises with tailored solutions, fostering scalability, 
            process optimization, cost reduction, and heightened overall efficiency.
            
            PORTFOLIO LINKS:
            {link_list}
            
            TASK:
            Write a professional cold email to the client regarding this job opportunity.
            Describe how {company_name} can fulfill their needs based on our expertise.
            
            GUIDELINES:
            1. Use a professional business tone
            2. Connect our capabilities to their specific job requirements
            3. Mention relevant portfolio links naturally
            4. Include a clear call-to-action
            5. Signature should be: {person_name}, {person_role}, {company_name}
            
            ### EMAIL (NO PREAMBLE):
            """
        )
        
        chain_email = prompt_email | self.llm
        
        # Format links
        if links and isinstance(links, list):
            links_text = "\n".join([f"- {link}" for link in links[:3]])
        elif links:
            links_text = str(links)
        else:
            links_text = "Please visit our portfolio for relevant case studies."
        
        res = chain_email.invoke({
            "job_description": str(job), 
            "link_list": links_text,
            "person_name": person_name,
            "company_name": company_name,
            "person_role": person_role
        })
        
        return res.content

if __name__ == "__main__":
    # Test the initialization
    try:
        chain = Chain()
        print("✅ Chain initialized successfully")
        
        # Test with sample data
        test_job = {
            "role": "AI Engineer",
            "experience": "3-5 years",
            "skills": ["Python", "Machine Learning"],
            "description": "Looking for AI engineer with ML experience"
        }
        
        test_links = ["https://github.com/example/project1", "https://github.com/example/project2"]
        
        # Test with default parameters
        email1 = chain.write_mail(test_job, test_links)
        print("✅ Test email 1 generated")
        
        # Test with custom parameters
        email2 = chain.write_mail(
            test_job, 
            test_links,
            person_name="Alex Johnson",
            company_name="NeuroSync AI",
            person_role="Head of Business Development"
        )
        print("✅ Test email 2 generated with custom parameters")
        
        print("\n📧 Sample Email Output:")
        print("-" * 50)
        print(email2[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure .env file has GROQ_API_KEY")