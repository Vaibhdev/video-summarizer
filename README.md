
conda create -n lang6 python=3.11 -y

conda activate lang6

pip install -r requirements.txt



<!-- langchain==0.3.13
langchain-core==0.3.28
langchain-community==0.3.13
langchain-openai==0.2.14 -->


# run 
streamlit run app.py

uvicorn backend:app --reload