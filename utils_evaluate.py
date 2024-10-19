import pandas as pd
from datasets import Dataset
from nltk.translate.bleu_score import sentence_bleu

from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    answer_correctness,
)
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer, util

from utils_evaluate_objections import generate_objection_score


async def evaluate_objections(session):
    print("evaluate_objections()")

    for response in session.responses:
        question = response.get("question", "")
        answer = response.get("response", "")
        print(f"Question: {question}")
        print(f"Answer: {answer}")
        
        q_and_a = {
            "objection": question,
            "answer": answer
        }       
        print(q_and_a)
        score = await generate_objection_score(q_and_a)
        print(score)
        response["evaluation_score"] = score


def evaluate_answers(session):
    ragas_results = evaluate_with_ragas(session)
    session.ragas_results = ragas_results
    scores = []
    for response in session.responses:
        bleu_score = calculate_bleu_score(response.get("response", ""), response.get("ground_truth", ""))
        rouge_score = calculate_rouge_score(response.get("response", ""), response.get("ground_truth", ""))
        semantic_similarity_score = calculate_semantic_similarity(response.get("response", ""), response.get("ground_truth", ""))
        all_scores = {
            "bleu_score": bleu_score,
            "rouge_score": rouge_score,
            "semantic_similarity_score": semantic_similarity_score
        }
        scores.append(all_scores)
    session.scores = scores
    return scores

def evaluate_with_ragas(session):
    questions = [] 
    answers = []
    ground_truths = []
    contexts = []
    for i, response in enumerate(session.responses, 1):
        questions.append(response.get("question", ""))
        answers.append(response.get("response", ""))
        ground_truths.append(response.get("ground_truth", ""))
        contexts.append([session.company.product_description])

    evaluation_dataset = Dataset.from_dict({
        "question" : questions,
        "answer" : answers,
        "contexts" : contexts,
        "ground_truth" : ground_truths
    })

    print(evaluation_dataset)

    metrics = [
        # faithfulness,
        answer_relevancy,
        # context_recall,
        # context_precision,
        answer_correctness,
    ]
    results = evaluate(evaluation_dataset, metrics)
    print(results)
    return results

def calculate_bleu_score(answer, ground_truth):
    bleu_score = sentence_bleu([ground_truth.split()], answer.split())
    print(f"BLEU score: {bleu_score}")
    return bleu_score

def calculate_rouge_score(answer, ground_truth):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    rouge_scores = scorer.score(ground_truth, answer)
    print(f"ROUGE score: {rouge_scores}")
    return rouge_scores

def calculate_semantic_similarity(answer, ground_truth):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    answer_embedding = model.encode(answer)
    ground_truth_embedding = model.encode(ground_truth)
    similarity_score = util.cos_sim(answer_embedding, ground_truth_embedding)
    print(f"Semantic Similarity: {similarity_score.item()}")
    return similarity_score.item()