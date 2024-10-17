import asyncio
import json
import re
from datetime import datetime

from utils_evaluate import evaluate_answers

async def display_llm_responses(cl, session_state):
    output = f"**Responses**"
    await cl.Message(content=output).send()
    for query, response in zip(session_state.queries, session_state.llm_responses):
        query_display = {
            "command": query["command"],
            "message": query["message"],
            "mood_score": query["mood_score"],
            "previous_question": query["previous_question"],
            "rep_answer": query["rep_answer"],
            "next_question": query["next_question"],
        }
        query_json = json.dumps(query_display, indent=2)
        await cl.Message(content="Query:").send()
        await cl.Message(content=query_json).send()
        await cl.Message(content="Response:").send()
        await cl.Message(content=response).send()

    remaining_queries = session_state.queries[len(session_state.llm_responses):]
    remaining_responses = session_state.llm_responses[len(session_state.queries):]

    for query in remaining_queries:
        await cl.Message(content=f"**Query:** {query}").send()

    for response in remaining_responses:
        await cl.Message(content=f"**Response:** {response}").send()

def format_score(score):
    if isinstance(score, (int, float)):
        return f"{score*100:.1f}%"
    return score 

def format_rogue_score(score):
    if isinstance(score, str):
        match = re.search(r'precision=([\d.]+), recall=([\d.]+), fmeasure=([\d.]+)', score)
        if match:
            precision = float(match.group(1))
            recall = float(match.group(2))
            fmeasure = float(match.group(3))
            return f"Precision: {precision*100:.1f}%, Recall: {recall*100:.1f}%, FMeasure: {fmeasure*100:.1f}%"
    else:
        precision = score.precision
        recall = score.recall
        fmeasure = score.fmeasure
        return f"Precision: {precision*100:.1f}%, Recall: {recall*100:.1f}%, FMeasure: {fmeasure*100:.1f}%"     
    return score  #

def format_datetime(dt):
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M") 
    return str(dt)  #

async def display_evaluation_results(cl, session_state):
    out_text = "*Preparing evaluation results ...*"
    await cl.Message(content=out_text).send()

    evaluate_answers(session_state) 
    await asyncio.sleep(1)

    output = f"**Session Summary**"
    await cl.Message(content=output).send()
    output = f"**Start Time:** {format_datetime(session_state.start_time)} \n"
    output = output + f"**End Time:** {format_datetime(session_state.end_time)} \n"
    output = output + f"**Duration:** {session_state.duration_minutes} minutes \n"
    output = output + f"**Total Number of Questions:** {len(session_state.questions)} \n"
    output = output + f"**Total Questions Answered:** {len(session_state.responses)} \n"
    await cl.Message(content=output).send()

    results_df = session_state.ragas_results.to_pandas()
    columns_to_average = ['answer_relevancy', 'answer_correctness']
    averages = results_df[columns_to_average].mean()

    await cl.Message(content="**Overall Summary (By SalesBuddy)**").send()
    output = f"**Overall Score:** {session_state.responses[-1]['overall_score']} \n"
    output = output + f"**Overall Evaluation:** {session_state.responses[-1]['overall_evaluation']} \n"
    output = output + f"**Final Mood Score:** {session_state.responses[-1]['mood_score']} \n"
    output = output + f"**Customer Next Steps:** {session_state.llm_next_steps} \n"
    await cl.Message(content=output).send()

    if session_state.do_ragas_evaluation:
        await cl.Message(content="**Average Scores - Based on RAGAS**").send()
        output = "Answer Relevancy: " + str(format_score(averages['answer_relevancy'])) + "\n"
        output = output + "Answer Correctness: " + str(format_score(averages['answer_correctness'])) + "\n"
        await cl.Message(content=output).send()

    await cl.Message(content="**Individual Question Scores**").send()

    for index, resp in enumerate(session_state.responses):
        scores = session_state.scores[index]
        relevancy = results_df.iloc[index].get('answer_relevancy', 'N/A')
        correctness = results_df.iloc[index].get('answer_correctness', 'N/A')
        bleu_score = scores.get('bleu_score', 'N/A')
        rouge1_score = scores.get('rouge_score', {}).get('rouge1', 'N/A')
        rouge1_output = format_rogue_score(rouge1_score)
        rougeL_score = scores.get('rouge_score', {}).get('rougeL', 'N/A')
        rougeL_output = format_rogue_score(rougeL_score)
        semantic_similarity_score = scores.get('semantic_similarity_score', 'N/A')
        output = f"""
            **Question:** {resp.get('question', 'N/A')}
            **Answer:** {resp.get('response', 'N/A')}
            **Ground Truth:** {resp.get('ground_truth', 'N/A')}  
        """
        if session_state.do_ragas_evaluation:
            numbers = f"""   
                **Answer Relevancy:** {format_score(relevancy)}
                **Answer Correctness:** {format_score(correctness)}
                **BLEU Score:** {format_score(bleu_score)}
                **ROUGE 1 Score:** {rouge1_output}
                **ROUGE L Score:** {rougeL_output}
                    **Semantic Similarity Score:** {format_score(semantic_similarity_score)}
            """ 
            await cl.Message(content=output).send()
            await cl.Message(content=numbers).send()
        else:
            await cl.Message(content=output).send()
