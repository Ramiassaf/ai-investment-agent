from src.storage.article_store import ArticleRecord
from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_retrieval_text(article: ArticleRecord) -> str:
    """"
    Build one clean semantic retrieval text from a single article.

    version 1 design:
    -use title
    -use clean_text
    -use tags
    -do not use raw text
    """
    title = (article.title or "").strip()
    clean_text = (article.clean_text or "").strip()
    tags = " ".join(article.tags or []).strip()

    parts =[]
    if title:
        parts.append(f"Title:{title}")

    if clean_text:
        parts.append(f"Content:{clean_text}")
    
    if tags:
        parts.append(f"Tags:{tags}")

    return "\n".join(parts)


def prepare_retrieval_corpus(articles: list[ArticleRecord]) -> list[str]:
    """
    Convert a list of ArticleRecord objects into a list of retrieval text.

    Important: the returned list preserves alignment with the orginal article list
    that means courpus[i] corresponds to articles[i]
    """
    return [build_retrieval_text(article) for article in articles]


def embed_texts(texts:list[str]) -> list[list[float]]:
    """
    Convert a list of texts into embeddings using OpenAI
    """
    response = client.embeddings.create(
        input = texts,
        model = "text-embedding-3-small"
    )
    return[item.embedding for item in response.data]


def embed_query(query:str) -> list[float]:
    """
    Convert a query string into embedding using OpenAI
    """
    response = client.embeddings.create(
        input = [query],
        model = "text-embedding-3-small"
    )
    return response.data[0].embedding


def cosine_similarity(a:list[float], b:list[float])->float:
    """
    Compute cosine similarity between two vectors
    """
    a = np.array(a)
    b = np.array(b)
    return np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))


def deduplicate_articles_by_url(articles: list[ArticleRecord]) -> list[ArticleRecord]:
    """
    Remove duplicate articles based on URL while preserving order.
    """
    seen_urls = set()
    unique_articles = []

    for article in articles:
        url = (article.url or "").strip()

        if url in seen_urls:
            continue

        seen_urls.add(url)
        unique_articles.append(article)

    return unique_articles



def semantic_search(
    query: str,
    articles: list,
    embeddings: list[list[float]],
    top_k: int = 5
    ):
    """
    Perform semantic search and return top_k matching articles.
    """

    query_embedding = embed_query(query)

    scores = []
    
    if len(articles) != len(embeddings):
        raise ValueError("Articles and embeddings must have the same length")

    for i, emb in enumerate(embeddings):
        score = cosine_similarity(query_embedding, emb)
        scores.append((i, score))

    scores.sort(key=lambda x: x[1], reverse=True) # Sort by score in descending order
    ranked_articles = [articles[idx] for idx, _ in scores] 
    unique_ranked_articles = deduplicate_articles_by_url(ranked_articles)
    return unique_ranked_articles[:top_k]
       