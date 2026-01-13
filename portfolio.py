# portfolio.py - Fixed for your structure
import pandas as pd
import chromadb
import uuid
import os

class Portfolio:
    def __init__(self):
        # Set the correct path - relative to App folder
        self.csv_path = "resource/portfolio.csv"
        
        print(f"📁 Looking for portfolio at: {self.csv_path}")
        print(f"📁 Current directory: {os.getcwd()}")
        
        # Check if file exists
        if os.path.exists(self.csv_path):
            print(f"✅ Found portfolio CSV: {self.csv_path}")
            self.data = pd.read_csv(self.csv_path)
        else:
            # Create directory and sample file
            print(f"⚠️ File not found. Creating directory and sample portfolio...")
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            
            # Create sample data
            self.data = pd.DataFrame({
                'Techstack': [
                    'Python, Machine Learning, AI',
                    'React, JavaScript, Web Development',
                    'Data Science, SQL, Analytics'
                ],
                'Links': [
                    'https://github.com/example/ai-project, https://github.com/example/ml-project',
                    'https://github.com/example/web-project',
                    'https://github.com/example/data-project'
                ]
            })
            
            # Save to CSV
            self.data.to_csv(self.csv_path, index=False)
            print(f"✅ Created sample portfolio at: {self.csv_path}")
        
        print(f"📊 Loaded {len(self.data)} portfolio items")
        
        # Initialize ChromaDB
        try:
            self.chroma_client = chromadb.PersistentClient('vectorstore')
            self.collection = self.chroma_client.get_or_create_collection(name="portfolio")
            print("✅ ChromaDB collection ready")
        except Exception as e:
            print(f"⚠️ ChromaDB error: {e}")
            self.collection = None

    def load_portfolio(self):
        """Load portfolio into vector database"""
        if self.collection:
            if self.collection.count() == 0:
                print("🔄 Loading portfolio into ChromaDB...")
                for _, row in self.data.iterrows():
                    self.collection.add(
                        documents=row["Techstack"],
                        metadatas={"links": row["Links"]},
                        ids=[str(uuid.uuid4())]
                    )
                print(f"✅ Loaded {len(self.data)} items into ChromaDB")
            else:
                print(f"✅ ChromaDB already has {self.collection.count()} items")
        else:
            print("✅ Using local portfolio (no ChromaDB)")

    def query_links(self, skills):
        """Query portfolio for skills and return relevant links"""
        if not skills:
            return []
        
        print(f"🔍 Querying portfolio for skills: {skills}")
        
        # Method 1: Try ChromaDB first
        if self.collection:
            try:
                query_text = " ".join(skills) if isinstance(skills, list) else str(skills)
                results = self.collection.query(
                    query_texts=[query_text], 
                    n_results=3
                )
                
                links_list = []
                if results.get('metadatas'):
                    for metadata_group in results['metadatas']:
                        for metadata in metadata_group:
                            if 'links' in metadata:
                                # Split comma-separated links
                                links = [link.strip() for link in metadata['links'].split(',')]
                                links_list.extend(links)
                
                if links_list:
                    print(f"✅ Found {len(links_list)} links via ChromaDB")
                    return links_list[:5]
                    
            except Exception as e:
                print(f"⚠️ ChromaDB query failed: {e}")
        
        # Method 2: Fallback to simple text matching
        links_list = []
        for _, row in self.data.iterrows():
            techstack = str(row['Techstack']).lower()
            row_skills = [skill.strip().lower() for skill in techstack.split(',')]
            
            # Check if any skill matches
            for skill in skills:
                if isinstance(skill, str) and skill.lower() in row_skills:
                    # Extract links
                    row_links = str(row['Links']).split(',')
                    links_list.extend([link.strip() for link in row_links])
                    break  # Found a match, move to next row
        
        # Remove duplicates and limit
        unique_links = list(set(links_list))
        print(f"✅ Found {len(unique_links)} unique links")
        
        return unique_links[:5]

# Test
if __name__ == "__main__":
    print("🧪 Testing Portfolio class...")
    portfolio = Portfolio()
    portfolio.load_portfolio()
    
    # Test query
    test_skills = ["Python", "Machine Learning", "AI"]
    links = portfolio.query_links(test_skills)
    
    print(f"\n🔗 Portfolio links for {test_skills}:")
    for i, link in enumerate(links, 1):
        print(f"  {i}. {link}")