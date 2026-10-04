import json
from pathlib import Path

import bm25s
import numpy as np

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder
)


# =========================================================
# 1. Load real Meta financial-report chunks
# =========================================================

CHUNKS_PATH = Path(
    "data/meta_q2_2026_chunks.json"
)


def load_chunks():

    with open(
        CHUNKS_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        chunks = json.load(f)

    return chunks


chunks = load_chunks()

documents = [
    chunk["text"]
    for chunk in chunks
]


# =========================================================
# 2. Load retrieval models
# =========================================================

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L6-v2"
)


# =========================================================
# 3. Build dense embeddings
# =========================================================

document_embeddings = embedding_model.encode(
    documents
)


# =========================================================
# 4. Build BM25 index
# =========================================================

corpus_tokens = bm25s.tokenize(
    documents
)

bm25_retriever = bm25s.BM25()

bm25_retriever.index(
    corpus_tokens
)


# =========================================================
# 5. Cosine similarity
# =========================================================

def cosine_similarity(a, b):

    return np.dot(a, b) / (
        np.linalg.norm(a)
        *
        np.linalg.norm(b)
    )


# =========================================================
# 6. Main retrieval function
# =========================================================

def retrieve_evidence(question):

    # -----------------------------------------------------
    # Dense retrieval
    # -----------------------------------------------------

    question_embedding = embedding_model.encode(
        question
    )

    dense_scores = []

    for index, embedding in enumerate(
        document_embeddings
    ):

        score = cosine_similarity(
            question_embedding,
            embedding
        )

        dense_scores.append(
            (
                score,
                index
            )
        )


    dense_scores.sort(
        reverse=True,
        key=lambda x: x[0]
    )


    dense_rank = {
        index: rank
        for rank, (score, index)
        in enumerate(
            dense_scores,
            start=1
        )
    }


    # -----------------------------------------------------
    # BM25 retrieval
    # -----------------------------------------------------

    query_tokens = bm25s.tokenize(
        question
    )

    bm25_results, bm25_scores = (
        bm25_retriever.retrieve(
            query_tokens,
            corpus=documents,
            k=len(documents)
        )
    )


    # Map returned text back to chunk index
    text_to_index = {
        text: index
        for index, text in enumerate(
            documents
        )
    }


    bm25_rank = {}

    for rank in range(
        1,
        len(documents) + 1
    ):

        document_text = str(
            bm25_results[0, rank - 1]
        )

        index = text_to_index[
            document_text
        ]

        bm25_rank[index] = rank


    # -----------------------------------------------------
    # RRF fusion
    # -----------------------------------------------------

    k = 60

    hybrid_scores = []


    for index in range(
        len(documents)
    ):

        r_dense = dense_rank[index]
        r_bm25 = bm25_rank[index]

        rrf_score = (
            1 / (k + r_dense)
            +
            1 / (k + r_bm25)
        )

        hybrid_scores.append(
            (
                rrf_score,
                index
            )
        )


    hybrid_scores.sort(
        reverse=True,
        key=lambda x: x[0]
    )


    # -----------------------------------------------------
    # Cross-Encoder reranking
    # -----------------------------------------------------

    candidate_indices = [
        index
        for score, index
        in hybrid_scores
    ]


    pairs = [
        (
            question,
            documents[index]
        )
        for index in candidate_indices
    ]


    reranker_scores = (
        reranker.predict(pairs)
    )


    reranked_results = []


    for index, score in zip(
        candidate_indices,
        reranker_scores
    ):

        reranked_results.append(
            (
                float(score),
                index
            )
        )


    reranked_results.sort(
        reverse=True,
        key=lambda x: x[0]
    )


    # -----------------------------------------------------
    # Best evidence
    # -----------------------------------------------------

    best_score, best_index = (
        reranked_results[0]
    )

    best_chunk = chunks[
        best_index
    ]


    # -----------------------------------------------------
    # Prepare Top 5 candidates
    # -----------------------------------------------------

    top_candidates = []

    for score, index in reranked_results[:5]:

        chunk = chunks[index]

        top_candidates.append({
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "page": chunk["page"],
            "source": chunk["source"],
            "company": chunk["company"],
            "period": chunk["period"],
            "document_type": chunk["document_type"],
            "reranker_score": float(score)
        })


    return {
        "evidence": best_chunk["text"],
        "chunk_id": best_chunk["chunk_id"],
        "page": best_chunk["page"],
        "source": best_chunk["source"],
        "company": best_chunk["company"],
        "period": best_chunk["period"],
        "reranker_score": best_score,
        "candidates": top_candidates,
        "all_results": reranked_results
    }