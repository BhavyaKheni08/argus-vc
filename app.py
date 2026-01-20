import streamlit as st
import os
import shutil
from src.modules.ingestion import GoogleIngestion
from src.graph import app

# Page Config
st.set_page_config(page_title="Argus VC", layout="wide")

# Header
st.title("Argus VC: Autonomous Investment Committee")

# Sidebar Configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Key Checks
    google_key = os.getenv("GOOGLE_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if google_key:
        st.success("Google API Key detected", icon="✅")
    else:
        st.error("Missing Google API Key", icon="❌")
        
    if tavily_key:
        st.success("Tavily API Key detected", icon="✅")
    else:
        st.error("Missing Tavily API Key", icon="❌")

# File Uploader
uploaded_file = st.file_uploader("Upload Pitch Deck (PDF)", type=["pdf"])

if uploaded_file and st.button("Analyze Pitch Deck"):
    if not google_key or not tavily_key:
        st.error("Please configure your API keys in the .env file.")
        st.stop()

    # Step A: Save File locally
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        # Step B: Ingest
        ingestion = GoogleIngestion()
        with st.spinner("Uploading to Gemini 1.5 Flash..."):
            file_object = ingestion.upload_to_gemini(file_path, mime_type="application/pdf")
        
        st.success(f"File uploaded successfully! (URI: {file_object.uri})")

        # Step C: Execute Graph
        with st.spinner("The Committee is deliberating... (Sherlock, Researcher, CFO, and Critic are working)"):
            initial_state = {"pdf_file_uri": file_object.uri}
            final_state = app.invoke(initial_state)

        # Step D: Display Results
        final_memo = final_state.get("final_memo", "No memo generated.")
        
        st.divider()
        st.subheader("Final Investment Memo")
        st.markdown(final_memo)
        
        # Bonus: Hot Seat Questions Expander
        # We'll just display the whole memo, but also look for a section if possible. 
        # Since the memo structure is markdown, we rely on the user reading it, 
        # but we can explicitly parse if needed. For now, we'll follow the simpler instruction
        # to just use an expander if we *find* it or just generally for "Founders Hot Seat".
        if "Hot Seat" in final_memo or "Questions" in final_memo:
             with st.expander("Founders Hot Seat (Quick View)"):
                 st.info("Check the 'Hot Seat Questions' section in the memo above.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
    finally:
        # Step D: Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            # print(f"Deleted temp file: {file_path}")
