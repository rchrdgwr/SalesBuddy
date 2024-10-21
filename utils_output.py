import asyncio
import json
import re
from datetime import datetime

from utils_evaluate import evaluate_answers, evaluate_objections
from utils_prep import offer_initial_actions
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
    print("Checking evaluation and objection flags")
    print(session_state.do_evaluation)
    print(session_state.add_objections_to_analysis)
    hit_miss_ratio = "N/A"
    hit_miss_score = 0
    if session_state.do_evaluation:
        evaluate_answers(session_state) 
    elif session_state.add_objections_to_analysis:
        await evaluate_objections(session_state)
        for resp in session_state.responses:    
            if resp.get('evaluation_score', 'N/A') == 1 or resp.get('evaluation_score', 'N/A') == 0:
                hit_miss = resp.get('evaluation_score', 0)
                hit_miss_score += hit_miss
            hit_miss_ratio = (hit_miss_score / len(session_state.responses)) * 100
    await asyncio.sleep(1)

    output = f"**Session Summary**"
    await cl.Message(content=output).send()
    output = f"**Start Time:** {format_datetime(session_state.start_time)} \n"
    output = output + f"**End Time:** {format_datetime(session_state.end_time)} \n"
    output = output + f"**Duration:** {session_state.duration_minutes} minutes \n"
    output = output + f"**Total Number of Questions:** {len(session_state.questions)} \n"
    output = output + f"**Total Questions Answered:** {len(session_state.responses)} \n"
    await cl.Message(content=output).send()

    if session_state.do_ragas_evaluation:
        results_df = session_state.ragas_results.to_pandas()
        columns_to_average = ['answer_relevancy', 'answer_correctness']
        averages = results_df[columns_to_average].mean()

    await cl.Message(content="**Overall Summary (By SalesBuddy)**").send()
    output = f"**SalesBuddy Grade (1-10):** {session_state.responses[-1]['overall_score']} \n"
    output = output + f"**SalesBuddy Evaluation:** {session_state.responses[-1]['overall_evaluation']} \n"
    output = output + f"**SalesBuddy Final Mood Score (1-10):** {session_state.responses[-1]['mood_score']} \n"
    output = output + f"**Hit/Miss Ratio:** {hit_miss_ratio:.1f}% \n"
    await cl.Message(content=output).send()

    if session_state.do_ragas_evaluation:
        await cl.Message(content="**Average Scores - Based on RAGAS**").send()
        output = "Answer Relevancy: " + str(format_score(averages['answer_relevancy'])) + "\n"
        output = output + "Answer Correctness: " + str(format_score(averages['answer_correctness'])) + "\n"
        await cl.Message(content=output).send()

    await cl.Message(content="**Individual Question Scores**").send()

    for index, resp in enumerate(session_state.responses):
        eval_score = resp.get('evaluation_score', 0)
        if eval_score == 1:
            eval_output = "Hit"
        elif eval_score == 0:
            eval_output = "Miss"
        else:
            eval_output = "N/A"
        output = f"**Question:** {resp.get('question', 'N/A')}\n"
        output = output + f"**Answer:** {resp.get('response', 'N/A')}\n"
        output = output + f"**SalesBuddy Evaluation:** {resp.get('response_evaluation', 'N/A')}\n"
        output = output + f"**Hit/Miss:** {eval_output}\n"

        if session_state.do_ragas_evaluation:
            scores = session_state.scores[index]
            relevancy = scores.get('answer_relevancy', 'N/A')
            correctness = scores.get('answer_correctness', 'N/A')
            bleu_score = scores.get('bleu_score', 'N/A')
            rouge1_score = scores.get('rouge_score', {}).get('rouge1', 'N/A')
            rouge1_output = format_rogue_score(rouge1_score)
            rougeL_score = scores.get('rouge_score', {}).get('rougeL', 'N/A')
            rougeL_output = format_rogue_score(rougeL_score)
            semantic_similarity_score = scores.get('semantic_similarity_score', 'N/A')
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

    await offer_initial_actions()