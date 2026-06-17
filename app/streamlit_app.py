import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from src.llm.answer import answer_question
from src.storage.article_store import load_articles_jsonl, filter_by_recency
from src.retrieval.domain_filter import filter_domain_relevant_articles
from src.retrieval.semantic_retriever import prepare_retrieval_corpus, embed_texts


st.set_page_config(
    page_title="Gold Intelligence",
    page_icon="🥇",
    layout="centered"
)

# helper function to convert bias to colored dot
def bias_color(bias):
    if bias == "supportive":
        return "🟢"
    elif bias == "negative":
        return "🔴"
    elif bias == "mixed":
        return "🟡"
    return "⬜"

# helper function to load and embed articles, cached for Streamlit
@st.cache_resource
def load_and_embed_articles():
    articles = load_articles_jsonl("data/processed/articles.jsonl")
    if not articles:
        return None, None
    recent_articles = filter_by_recency(articles, days=30)
    if not recent_articles:
        return None, None
    domain_articles, _ = filter_domain_relevant_articles(recent_articles)
    if not domain_articles:
        return None, None
    corpus = prepare_retrieval_corpus(domain_articles)
    embeddings = embed_texts(corpus)
    return domain_articles, embeddings

# load and embed articles when app starts
domain_articles, embeddings = load_and_embed_articles()


st.title("🥇 Gold Intelligence")
st.caption("AI-Powered Market Research for Precious Metals")

st.divider()

question = st.text_input(
    "Ask anything about gold or silver...",
    placeholder="Why is gold rising today?"
)

days = st.selectbox(
    "Time window",
    options=[7, 14, 30, 90],
    index=2
)

submit = st.button("Analyze", type="primary")

if submit and question:
    with st.spinner("Analyzing market data..."):
        result = answer_question(question, domain_articles=domain_articles, embeddings=embeddings)

    st.divider()

    st.subheader("Market Bias")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="Gold",
            value=f"{bias_color(result['gold_bias'])} {result['gold_bias'].upper()}"
        )
    with col2:
        st.metric(
            label="Silver",
            value=f"{bias_color(result['silver_bias'])} {result['silver_bias'].upper()}"
        )

    st.divider()

    st.subheader("Analysis")
    st.markdown(result["answer"])