import plotly.graph_objects as go

import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime



st.set_page_config(page_title="Video Content Summarizer", page_icon="🎥", layout="wide")


API_URL = "http://localhost:8000"
def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return None


def get_thumbnail(video_id):
    return f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"

if "history" not in st.session_state:
    st.session_state.history = []

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "summarize"



st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Summarize", "History", "Settings", "About"])

st.session_state.active_tab = page.lower()




if st.session_state.active_tab == "summarize":
    st.title("🎥 Video Content Summarizer")
    st.write("Upload a video or provide a YouTube link to get a concise summary.")

  
    input_method = st.radio("Choose Input Method:", ["YouTube URL", "Upload Video"])

    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            summary_format = st.selectbox(
                "Summary Format",
                ["markdown", "bullet", "narrative"],
                help="Choose the format of your summary"
            )
            
            summary_length = st.selectbox(
                "Summary Length",
                ["short", "medium", "long"],
                index=1,
                help="Short (100-150 words), Medium (250-300 words), Long (400-500 words)"
            )
        
        with col2:
            target_language = st.selectbox(
                "Output Language",
                ["english", "spanish", "french", "german", "chinese", "japanese", "arabic"],
                help="Translate the summary to this language"
            )
            
            include_sentiment = st.checkbox("Include Sentiment Analysis", value=False)
            include_keywords = st.checkbox("Extract Keywords", value=True)

    if input_method == "YouTube URL":
        url = st.text_input("Enter YouTube URL:", placeholder="https://youtube.com/watch?v=...")
        
        # Preview the video if URL is valid
        if url:
            video_id = extract_video_id(url)
            if video_id:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(get_thumbnail(video_id), use_column_width=True)
                with col2:
                    st.write("Ready to summarize this video. Click the button below to process.")
        
        if st.button("Generate Summary", key="youtube_summary_btn"):
            if url:
                with st.spinner("Processing video..."):
                    try:
                        # Prepare the request with options
                        request_data = {
                            "url": url,
                            "options": {
                                "format": summary_format,
                                "length": summary_length,
                                "language": target_language,
                                "include_sentiment": include_sentiment,
                                "include_keywords": include_keywords
                            }
                        }
                        
                        response = requests.post(
                            f"{API_URL}/summarize/youtube",
                            json=request_data
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success("Summary generated successfully!")
                            
                            # Create tabs for different sections
                            tab1, tab2, tab3 = st.tabs(["Summary", "Details", "Full Transcript"])
                            
                            with tab1:
                                st.markdown(data["summary"])
                                
                                # Download options
                                st.download_button(
                                    "Download Summary (TXT)",
                                    data["summary"],
                                    file_name="summary.txt",
                                    mime="text/plain"
                                )
                            
                            with tab2:
                                # Display metadata
                                if "metadata" in data:
                                    metadata = data["metadata"]
                                    
                                    # Video info
                                    if "title" in metadata:
                                        st.subheader("Video Information")
                                        st.write(f"**Title:** {metadata.get('title', 'N/A')}")
                                        st.write(f"**Author:** {metadata.get('author', 'N/A')}")
                                        st.write(f"**Length:** {metadata.get('length_seconds', 0)} seconds")
                                        st.write(f"**Views:** {metadata.get('views', 'N/A')}")
                                        
                                    # Sentiment analysis
                                    if "sentiment" in metadata:
                                        st.subheader("Sentiment Analysis")
                                        sentiment = metadata["sentiment"]
                                        
                                       
                                        compound_score = sentiment["scores"]["compound"]
                                        fig = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=compound_score,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "Sentiment Score"},
                                            gauge={
                                                'axis': {'range': [-1, 1]},
                                                'bar': {'color': "darkblue"},
                                                'steps': [
                                                    {'range': [-1, -0.25], 'color': "red"},
                                                    {'range': [-0.25, 0.25], 'color': "gray"},
                                                    {'range': [0.25, 1], 'color': "green"}
                                                ]
                                            }
                                        ))
                                        st.plotly_chart(fig, key="youtube_sentiment_gauge")
                                        
                                        st.write(f"**Overall Sentiment:** {sentiment['overall'].capitalize()}")
                                        
                                        # Detailed sentiment scores
                                        scores = sentiment["scores"]
                                        st.write("Detailed Scores:")
                                        score_df = pd.DataFrame({
                                            "Metric": ["Positive", "Neutral", "Negative", "Compound"],
                                            "Score": [scores["pos"], scores["neu"], scores["neg"], scores["compound"]]
                                        })
                                        st.dataframe(score_df)
                                    
                                    # Keywords
                                    if "keywords" in metadata:
                                        st.subheader("Top Keywords")
                                        keywords = metadata["keywords"]
                                        st.write(", ".join(keywords))
                            
                            with tab3:
                                st.text_area("Full Transcript", data["transcript"], height=300)
                            
                            # Add to history
                            st.session_state.history.append(data)
                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error processing request: {str(e)}")
            else:
                st.warning("Please enter a YouTube URL!")

    else:  # Upload Video option
        uploaded_file = st.file_uploader("Upload Video File", type=["mp4", "avi", "mov", "mkv"])
        
        if uploaded_file:
            st.video(uploaded_file)
        
        if uploaded_file and st.button("Generate Summary", key="upload_summary_btn"):
            with st.spinner("Processing video..."):
                try:
                    # Prepare the form data
                    files = {"file": uploaded_file.getvalue()}
                    
                    # Add options as form data
                    params = {
                        "format": summary_format,
                        "length": summary_length,
                        "language": target_language,
                        "include_sentiment": str(include_sentiment).lower(),
                        "include_keywords": str(include_keywords).lower()
                    }
                    
                    response = requests.post(
                        f"{API_URL}/summarize/upload",
                        files=files,
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("Summary generated successfully!")
                        
                        # Create tabs for different sections
                        tab1, tab2, tab3 = st.tabs(["Summary", "Details", "Full Transcript"])
                        
                        with tab1:
                            st.markdown(data["summary"])
                            
                            # Download options
                            st.download_button(
                                "Download Summary (TXT)",
                                data["summary"],
                                file_name="summary.txt",
                                mime="text/plain"
                            )
                        
                        with tab2:
                            # Display metadata
                            if "metadata" in data:
                                metadata = data["metadata"]
                                
                                # Video info
                                st.subheader("Video Information")
                                st.write(f"**Filename:** {metadata.get('filename', 'N/A')}")
                                st.write(f"**Duration:** {metadata.get('duration_seconds', 0)} seconds")
                                
                                # Sentiment analysis
                                if "sentiment" in metadata:
                                    st.subheader("Sentiment Analysis")
                                    sentiment = metadata["sentiment"]
                                    
                                    # Display sentiment score with a gauge chart
                                    compound_score = sentiment["scores"]["compound"]
                                    fig = go.Figure(go.Indicator(
                                        mode="gauge+number",
                                        value=compound_score,
                                        domain={'x': [0, 1], 'y': [0, 1]},
                                        title={'text': "Sentiment Score"},
                                        gauge={
                                            'axis': {'range': [-1, 1]},
                                            'bar': {'color': "darkblue"},
                                            'steps': [
                                                {'range': [-1, -0.25], 'color': "red"},
                                                {'range': [-0.25, 0.25], 'color': "gray"},
                                                {'range': [0.25, 1], 'color': "green"}
                                            ]
                                        }
                                    ))
                                    st.plotly_chart(fig, key="upload_sentiment_gauge")
                                    
                                    st.write(f"**Overall Sentiment:** {sentiment['overall'].capitalize()}")
                                
                                # Keywords
                                if "keywords" in metadata:
                                    st.subheader("Top Keywords")
                                    keywords = metadata["keywords"]
                                    st.write(", ".join(keywords))
                        
                        with tab3:
                            st.text_area("Full Transcript", data["transcript"], height=300)
                        
                        # Add to history
                        st.session_state.history.append(data)
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")

elif st.session_state.active_tab == "history":
    st.title("📚 Summary History")
    
    # Add refresh button to fetch history from API
    if st.button("Refresh History"):
        try:
            response = requests.get(f"{API_URL}/summaries")
            if response.status_code == 200:
                st.session_state.history = response.json()
                st.success("History refreshed successfully!")
            else:
                st.error("Failed to refresh history")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Display history
    if st.session_state.history:
        # Search functionality
        search_term = st.text_input("Search in summaries:", "")
        
        for i, item in enumerate(reversed(st.session_state.history)):
            # Skip if search term doesn't match
            if search_term and search_term.lower() not in item["summary"].lower() and search_term.lower() not in item["transcript"].lower():
                continue
                
            # Extract title or ID for the expander
            title = item.get("metadata", {}).get("title", f"Summary {i+1}")
            timestamp = item.get("metadata", {}).get("timestamp", "")
            if timestamp:
                try:
                    timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            with st.expander(f"{title} ({timestamp})"):
                # Display tabs with content
                tab1, tab2 = st.tabs(["Summary", "Details"])
                
                with tab1:
                    st.markdown(item["summary"])
                    
                    # Download options
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.download_button(
                            "Download as TXT",
                            item["summary"],
                            file_name=f"summary_{i}.txt",
                            mime="text/plain"
                        )
                    
                    with col2:
                        # Generate MD download
                        md_content = f"# {title}\n\n## Summary\n\n{item['summary']}\n\n## Metadata\n\n"
                        for k, v in item.get("metadata", {}).items():
                            if k not in ["options", "timestamp"]:
                                md_content += f"- **{k}**: {v}\n"
                        
                        st.download_button(
                            "Download as MD",
                            md_content,
                            file_name=f"summary_{i}.md",
                            mime="text/markdown"
                        )
                    
                    with col3:
                        # Generate JSON download
                        st.download_button(
                            "Download as JSON",
                            json.dumps(item, indent=2),
                            file_name=f"summary_{i}.json",
                            mime="application/json"
                        )
                
                with tab2:
                    # Display metadata in a more structured way
                    metadata = item.get("metadata", {})
                    
                    if "video_id" in metadata:
                        video_id = metadata["video_id"]
                        st.image(get_thumbnail(video_id), width=320)
                    
                    # Create a clean display of metadata
                    meta_df = pd.DataFrame(
                        [(k, str(v)) for k, v in metadata.items() if k not in ["sentiment", "keywords", "options"]],
                        columns=["Property", "Value"]
                    )
                    st.dataframe(meta_df, use_container_width=True)
                    
                    # Display transcript - FIXED: Using checkbox instead of nested expander
                    show_transcript = st.checkbox(f"Show Full Transcript", key=f"transcript_{i}_{item.get('id', '')}")
                    if show_transcript:
                        st.text_area("Full Transcript", item["transcript"], height=300, key=f"transcript_text_{i}_{item.get('id', '')}")
                    
                    # Delete button
                    if "id" in item:
                        if st.button(f"Delete this summary", key=f"delete_{item['id']}"):
                            try:
                                response = requests.delete(f"{API_URL}/summaries/{item['id']}")
                                if response.status_code == 200:
                                    st.success("Summary deleted successfully!")
                                    # Remove from local history too
                                    st.session_state.history = [h for h in st.session_state.history if h.get("id") != item["id"]]
                                    st.rerun()
                                else:
                                    st.error("Failed to delete summary")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
    else:
        st.info("No summaries in history yet. Try summarizing a video first!")

elif st.session_state.active_tab == "settings":
    st.title("⚙️ Settings")
    
    # API Configuration
    st.subheader("API Configuration")
    api_url = st.text_input("API URL", value="http://localhost:8000")
    
    if st.button("Save Settings"):
        # In a real app, you would save these settings
        st.session_state.api_url = api_url
        st.success("Settings saved successfully!")
    
    # Language and LLM Model Settings
    st.subheader("Model Settings")
    
    llm_model = st.selectbox(
        "LLM Model",
        ["gpt-3.5-turbo-16k", "gpt-4"],
        index=0,
        help="The OpenAI model to use for summarization"
    )
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Controls randomness in generation (0 = deterministic, 1 = creative)"
    )
    
    # Default Summary Settings
    st.subheader("Default Summary Settings")
    
    default_format = st.selectbox(
        "Default Format",
        ["markdown", "bullet", "narrative"],
        index=0
    )
    
    default_length = st.selectbox(
        "Default Length",
        ["short", "medium", "long"],
        index=1
    )
    
    default_language = st.selectbox(
        "Default Output Language",
        ["english", "spanish", "french", "german", "chinese", "japanese", "arabic"],
        index=0
    )
    
    # Save default settings button
    if st.button("Save Default Settings"):
        # In a real app, these would be saved to a config file or database
        st.session_state.default_settings = {
            "format": default_format,
            "length": default_length,
            "language": default_language,
            "model": llm_model,
            "temperature": temperature
        }
        st.success("Default settings saved!")
    
    # Clear History Option
    st.subheader("Data Management")
    if st.button("Clear History"):
        if st.session_state.history:
            st.session_state.history = []
            st.success("History cleared successfully!")
        else:
            st.info("No history to clear.")
    
    # API Status
    st.subheader("API Status")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.success(f"API is online. Version: {response.json().get('api_version', 'Unknown')}")
        else:
            st.error("API is not responding correctly")
    except Exception as e:
        st.error(f"Could not connect to API: {str(e)}")

elif st.session_state.active_tab == "about":
    st.title("ℹ️ About Video Content Summarizer")
    
    st.markdown("""
    ## Overview
    
    This application helps you summarize video content quickly and effectively. Whether you have a YouTube URL 
    or a video file, our tool can generate concise summaries, analyze sentiment, and extract key information.
    
    ## Features
    
    - **YouTube Video Summarization**: Summarize any YouTube video by providing its URL
    - **Video File Processing**: Upload and summarize your own video files
    - **Customizable Summaries**: Adjust the format, length, and language of your summaries
    - **Sentiment Analysis**: Understand the emotional tone of the video content
    - **Keyword Extraction**: Identify the most important topics covered in the video
    - **Export Options**: Download summaries in various formats (TXT, MD, JSON)
    - **History Management**: Access your past summaries anytime
    
    ## How It Works
    
    1. For YouTube videos, we extract the transcript using YouTube's API
    2. For uploaded videos, we convert speech to text using speech recognition
    3. The transcript is processed by an AI language model to generate a concise summary
    4. Additional analysis is performed to extract sentiment and keywords
    5. Results are presented in an easy-to-navigate interface
    
    ## Technologies Used
    
    - **Frontend**: Streamlit
    - **Backend**: FastAPI
    - **AI Model**: OpenAI's GPT models
    - **Speech Recognition**: Google Speech Recognition API
    - **Sentiment Analysis**: NLTK's VADER
    
    ## Contact
    
    If you have any questions, suggestions, or need support, please contact us at support@videosummarizer.com
    """)
    
    # Version information
    st.sidebar.info("Version 1.1.0")
    
# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 Video Content Summarizer")