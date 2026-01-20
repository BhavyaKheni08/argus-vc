# verify_system.py
# Prerequisite: pip install reportlab

from dotenv import load_dotenv
# Load environment variables FIRST
load_dotenv()

import os
import sys

# Add the project root to the python path so we can import src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from reportlab.pdfgen import canvas
except ImportError:
    print("Error: reportlab is not installed. Please run: pip install reportlab")
    sys.exit(1)

from src.modules.ingestion import GoogleIngestion
from src.graph import app

def create_dummy_pdf(filename):
    """Generates a dummy pitch deck PDF."""
    print(f"Generating dummy PDF: {filename}...")
    c = canvas.Canvas(filename)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Startup: OmniAGI")
    c.drawString(100, 730, "Founders: Alice Johnson (ex-Google), Bob Smith")
    c.drawString(100, 710, "Competitors: DeepMind, OpenAI")
    c.drawString(100, 690, "Financials: We have $0 revenue but project $100M in Year 1.")
    c.drawString(100, 670, "We have 500,000 waitlist users.")
    c.save()
    print("PDF generated.")

def verify_system():
    pdf_filename = "/Users/bhavyakheni/Desktop/argus_vc/bank_policy_manual.pdf"
    
    # Step 1: Generate Dummy Data
    create_dummy_pdf(pdf_filename)
    
    try:
        # Step 2: Run the Pipeline
        print("\n--- Starting Ingestion ---")
        ingestion = GoogleIngestion()
        
        # Check if API keys are set (basic check before proceeding)
        if not os.getenv("GOOGLE_API_KEY"):
            print("Error: GOOGLE_API_KEY is not set.")
            return

        file_object = ingestion.upload_to_gemini(pdf_filename, mime_type="application/pdf")
        print(f"File uploaded. URI: {file_object.uri}")
        
        print("\n--- Invoking Agent Graph ---")
        initial_state = {"pdf_file_uri": file_object.uri}
        
        # Invoke the graph
        final_state = app.invoke(initial_state)
        
        # Step 3: Report
        print("\n✅ Graph Execution Successful!")
        print("\n" + "="*50)
        print("FINAL INVESTMENT MEMO")
        print("="*50 + "\n")
        
        final_memo = final_state.get("final_memo", "No memo generated.")
        print(final_memo)
        
    except Exception as e:
        print(f"\n❌ System Verification Failed: {e}")
    
    finally:
        # Cleanup
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
            print(f"\nCleaned up local file: {pdf_filename}")

if __name__ == "__main__":
    verify_system()
