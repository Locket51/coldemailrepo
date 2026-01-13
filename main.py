import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from helpers import clean_text
import hashlib

def create_streamlit_app(llm, portfolio):
    st.title("📧 AI Cold Email Generator")
    
    # 🚨 ADD THIS: Track last processed URL
    if 'last_processed_url' not in st.session_state:
        st.session_state.last_processed_url = None
    
    # Sidebar for user details
    with st.sidebar:
        st.header("👤 Your Details")
        person_name = st.text_input("Your Name", "Steve")
        company_name = st.text_input("Company Name", "CogniCore")
        person_role = st.text_input("Your Role/Title", "Business Development Executive")
        
        # Optional contact info
        st.markdown("---")
        st.subheader("📞 Contact Info (Optional)")
        user_email = st.text_input("Your Email", "")
        phone_number = st.text_input("Phone", "")
        website = st.text_input("Website", "")
        
        st.markdown("---")
        st.info("💡 Your name, company, and role will be used in the generated emails.")
    
    # Main content area
    st.subheader("🔗 Enter Job Posting URL")
    default_url = " "
    url_input = st.text_input("Job URL:", default_url, label_visibility="collapsed")
    
    submit_button = st.button("🚀 Generate Email", type="primary", use_container_width=True)
    
    # Initialize session state for tracking processed jobs
    if 'processed_jobs' not in st.session_state:
        st.session_state.processed_jobs = set()
    
    # 🚨 CHANGE THIS: Add URL check to prevent re-processing
    should_process = (submit_button and 
                     url_input and 
                     url_input != st.session_state.last_processed_url)
    
    if should_process:
        # 🚨 ADD THIS: Store the URL we're about to process
        st.session_state.last_processed_url = url_input
        
        with st.spinner("Analyzing job description and generating email..."):
            try:
                # Load and clean webpage content
                loader = WebBaseLoader([url_input])
                data = loader.load()
                if data:
                    cleaned_data = clean_text(data[0].page_content)
                    
                    # Load portfolio
                    portfolio.load_portfolio()
                    
                    # Extract job details
                    jobs = llm.extract_jobs(cleaned_data)
                    
                    if jobs:
                        # Create a hash of the URL to use as a base key
                        url_hash = hashlib.md5(url_input.encode()).hexdigest()[:8]
                        
                        # Filter out duplicates (if any)
                        unique_jobs = []
                        seen_job_keys = set()
                        
                        for job in jobs:
                            # Create a unique key for this job
                            job_key = f"{job.get('role', '')}_{job.get('company', '')}"
                            job_hash = hashlib.md5(job_key.encode()).hexdigest()[:8]
                            
                            if job_hash not in seen_job_keys:
                                seen_job_keys.add(job_hash)
                                unique_jobs.append((job, job_hash))
                        
                        for idx, (job, job_hash) in enumerate(unique_jobs):
                            # Check if we've already processed this job
                            if job_hash in st.session_state.processed_jobs:
                                continue
                            
                            skills = job.get('skills', [])
                            
                            # Query portfolio for matching skills
                            links = portfolio.query_links(skills)
                            
                            # Generate email with DYNAMIC PARAMETERS
                            email = llm.write_mail(
                                job, 
                                links,
                                person_name=person_name,
                                company_name=company_name,
                                person_role=person_role
                            )
                            
                            # Store in session state
                            st.session_state.processed_jobs.add(job_hash)
                            
                            # Display results
                            st.success(f"✅ Email Generated for: {job.get('role', 'Position')}")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("📋 Job Details")
                                st.json(job)
                            
                            with col2:
                                st.subheader("📧 Generated Email")
                                email_display = st.text_area(
                                    "Email Content", 
                                    email, 
                                    height=400, 
                                    key=f"email_area_{url_hash}_{job_hash}"
                                )
                                
                                # Download button
                                st.download_button(
                                    label="📥 Download Email",
                                    data=email,
                                    file_name=f"cold_email_{company_name.replace(' ', '_')}_{job_hash}.txt",
                                    mime="text/plain",
                                    key=f"download_{url_hash}_{job_hash}"
                                )
                            
                            # Show portfolio links if available
                            if links:
                                st.subheader("🔗 Relevant Portfolio Links")
                                for link_idx, link in enumerate(links[:3]):
                                    st.markdown(f"{link_idx + 1}. {link}")
                            
                            # Add a separator between multiple jobs
                            if idx < len(unique_jobs) - 1:
                                st.divider()
                    else:
                        st.warning("⚠️ No job details found in the URL.")
                else:
                    st.error("❌ Could not load content from the URL.")
                    
            except Exception as e:
                st.error(f"❌ An Error Occurred: {str(e)}")
                st.info("Make sure the URL is accessible and contains job information.")
    
    # 🚨 ADD THIS: Show message if same URL is submitted again
    elif submit_button and url_input == st.session_state.last_processed_url:
        st.info("📢 This URL was already processed. Enter a new URL or refresh the page.")
    
    elif submit_button:
        st.warning("⚠️ Please enter a URL first.")

if __name__ == "__main__":
    # Set page config first
    st.set_page_config(
        layout="wide", 
        page_title="Cold Email Generator", 
        page_icon="📧",
        initial_sidebar_state="expanded"
    )
    
    # Initialize components
    try:
        chain = Chain()
        portfolio = Portfolio()
        
        # Create the app
        create_streamlit_app(chain, portfolio)
        
    except ImportError as e:
        st.error(f"❌ Missing dependencies: {str(e)}")
        st.code("pip install streamlit langchain-community beautifulsoup4", language="bash")
    
    except Exception as e:
        st.error(f"❌ Initialization Error: {str(e)}")
        st.info("Check if all required modules are properly configured.")