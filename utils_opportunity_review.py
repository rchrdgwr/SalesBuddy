import json
import os
from langchain.document_loaders import CSVLoader, PyPDFLoader, Docx2txtLoader
from langgraph.graph import StateGraph, END
from langchain.prompts import PromptTemplate
from langchain.schema import Document, AIMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pathlib import Path
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any

from pydantic import BaseModel, Field
from typing import Dict, Any


llm = ChatOpenAI(model_name="gpt-4o")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
qdrant = QdrantClient(":memory:")  # In-memory Qdrant instance

# Create collection
qdrant.create_collection(
    collection_name="opportunities",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

class State(BaseModel):
    file_path: str
    document_processed: str = ""
    opportunity_evaluation: Dict[str, Any] = Field(default_factory=dict)
    next_action: Dict[str, Any] = Field(default_factory=dict)

    def dict_representation(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "document_processed": self.document_processed,
            "opportunity_evaluation": self.opportunity_evaluation,
            "next_action": self.next_action
        }

async def prep_opportunity_review(session_state):
    file_path = prep_document()            
    structured_results = run_analysis(file_path)
    opportunity_review_report = create_opportunity_review_report(structured_results)
    session_state.opportunity_review_results = structured_results
    session_state.opportunity_review_report = opportunity_review_report
    

def prep_document():
    file_path = "data/HSBC Opportunity Information.docx"
    path = Path(file_path)

    if path.exists():
        if path.is_file():
            print(f"File found: {path}")
            print(f"File size: {path.stat().st_size / 1024:.2f} KB")
            print(f"Last modified: {path.stat().st_mtime}")
            print("File is ready for processing.")
            if os.access(path, os.R_OK):
                print("File is readable.")
            else:
                print("Warning: File exists but may not be readable. Check permissions.")
        else:
            print(f"Error: {path} exists but is not a file. It might be a directory.")
    else:
        print(f"Error: File not found at {path}")
        print("Please check the following:")
        print("1. Ensure the file path is correct.")
        print("2. Verify that the file exists in the specified location.")
        print("3. Check if you have the necessary permissions to access the file.")

        parent = path.parent
        if not parent.exists():
            print(f"Note: The directory {parent} does not exist.")
        elif not parent.is_dir():
            print(f"Note: {parent} exists but is not a directory.")

    file_path_for_processing = str(path)
    return file_path_for_processing

def load_and_chunk_document(file_path: str) -> List[Document]:
    """Load and chunk the document based on file type."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    _, file_extension = os.path.splitext(file_path.lower())
    
    if file_extension == '.csv':
        loader = CSVLoader(file_path)
    elif file_extension == '.pdf':
        loader = PyPDFLoader(file_path)
    elif file_extension == '.docx':
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")
    
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_documents(documents)

def agent_1(file_path: str) -> str:
    """Agent 1: Load, chunk, embed, and store document in Qdrant."""
    try:
        chunks = load_and_chunk_document(file_path)
        points = []
        for i, chunk in enumerate(chunks):
            vector = embeddings.embed_query(chunk.page_content)
            points.append(PointStruct(id=i, vector=vector, payload={"text": chunk.page_content}))
        
        qdrant.upsert(
            collection_name="opportunities",
            points=points
        )
        return f"Document processed and stored in Qdrant. {len(chunks)} chunks created."
    except Exception as e:
        print(f"Error in agent_1: {str(e)}")
        return f"Error processing document: {str(e)}"
    
def agent_2() -> Dict[str, Any]:
    """Agent 2: Evaluate opportunity based on MEDDIC criteria."""
    try:
        results = qdrant.scroll(collection_name="opportunities", limit=100)
        if not results or len(results[0]) == 0:
            raise ValueError("No documents found in Qdrant")

        full_text = " ".join([point.payload.get("text", "") for point in results[0]])
        
        meddic_template = """
        Analyze the following opportunity information using the MEDDIC sales methodology:

        {opportunity_info}

        Assign an overall opportunity score (1-100) with 100 means that the opportunity is a sure win.

        Provide a Summary of the opportunity.

        Evaluate the opportunity based on each MEDDIC criterion and assign a score for each criterion:
        1. Metrics
        2. Economic Buyer
        3. Decision Criteria
        4. Decision Process
        5. Identify Pain
        6. Champion

        Format your response as follows:
        Summary: [Opportunity Summary]
        Score: [Overall Opportunity Score between 1 to 100 based on MEDDIC criteria]
        MEDDIC Evaluation:
        - Metrics: [Score on Metrics, Evaluation on Metrics criterion]
        - Economic Buyer: [Score on Economic Buyer, Evaluation on Economic Buyer criterion]
        - Decision Criteria: [Score on Decision Criteria, Evaluation on Decision Criteria criterion]
        - Decision Process: [Score on Decision Process, Evaluation on Decision Process criterion]
        - Identify Pain: [Score on Identify Pain, Evaluation on Identify Pain criterion]
        - Champion: [Score on Champion, Evaluation on Champion criterion]
        """

        meddic_prompt = PromptTemplate(template=meddic_template, input_variables=["opportunity_info"])
        meddic_chain = meddic_prompt | llm
        
        response = meddic_chain.invoke({"opportunity_info": full_text})
        
        if isinstance(response, AIMessage):
            response_content = response.content
        elif isinstance(response, str):
            response_content = response
        else:
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Parse the response content
        lines = response_content.split('\n')
        summary = next((line.split('Summary:')[1].strip() for line in lines if line.startswith('Summary:')), 'N/A')
        score = next((int(line.split('Score:')[1].strip()) for line in lines if line.startswith('Score:')), 0)
        meddic_eval = {}
        current_criterion = None
        for line in lines:
            if line.strip().startswith('-'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    current_criterion = parts[0].strip('- ')
                    meddic_eval[current_criterion] = parts[1].strip()
            elif current_criterion and line.strip():
                meddic_eval[current_criterion] += ' ' + line.strip()

        return {
            'summary': summary,
            'score': score,
            'meddic_evaluation': meddic_eval
        }

    except Exception as e:
        print(f"Error in agent_2: {str(e)}")
        return {
            'summary': "Error occurred during evaluation",
            'score': 0,
            'meddic_evaluation': str(e)
        }
    
def agent_3(meddic_evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Agent 3: Suggest next best action and talking points."""
    try:
        next_action_template = """
        Based on the following MEDDIC evaluation of an opportunity:

        {meddic_evaluation}

        Suggest the next best action for the upcoming customer meeting and provide the top 3 talking points.
        Format your response as follows:
        Next Action: [Your suggested action]
        Talking Points:
        1. [First talking point]
        2. [Second talking point]
        3. [Third talking point]
        """

        next_action_prompt = PromptTemplate(template=next_action_template, input_variables=["meddic_evaluation"])
        next_action_chain = next_action_prompt | llm
        
        response = next_action_chain.invoke({"meddic_evaluation": json.dumps(meddic_evaluation)})
        
        if isinstance(response, AIMessage):
            response_content = response.content
        elif isinstance(response, str):
            response_content = response
        else:
            raise ValueError(f"Unexpected response type: {type(response)}")
        
        # Parse the response content
        lines = response_content.split('\n')
        next_action = next((line.split('Next Action:')[1].strip() for line in lines if line.startswith('Next Action:')), 'N/A')
        talking_points = [line.split('.')[1].strip() for line in lines if line.strip().startswith(('1.', '2.', '3.'))]

        return {
            'next_action': next_action,
            'talking_points': talking_points
        }
    except Exception as e:
        print(f"Error in agent_3: {str(e)}")
        return {
            'next_action': "Error occurred while suggesting next action",
            'talking_points': [str(e)]
        }
    
def process_document(state: State) -> State:
    print("Agent 1: Processing document...")
    file_path = state.file_path
    result = agent_1(file_path)
    return State(file_path=state.file_path, document_processed=result)

def evaluate_opportunity(state: State) -> State:
    print("Agent 2: Evaluating opportunity...")
    result = agent_2()
    return State(file_path=state.file_path, document_processed=state.document_processed, opportunity_evaluation=result)

def suggest_next_action(state: State) -> State:
    print("Agent 3: Suggesting next actions...")
    result = agent_3(state.opportunity_evaluation)
    return State(file_path=state.file_path, document_processed=state.document_processed, opportunity_evaluation=state.opportunity_evaluation, next_action=result)

def define_graph() -> StateGraph:
    workflow = StateGraph(State)
    
    workflow.add_node("process_document", process_document)
    workflow.add_node("evaluate_opportunity", evaluate_opportunity)
    workflow.add_node("suggest_next_action", suggest_next_action)
    
    workflow.set_entry_point("process_document")
    workflow.add_edge("process_document", "evaluate_opportunity")
    workflow.add_edge("evaluate_opportunity", "suggest_next_action")
    
    return workflow


def run_analysis(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    graph = define_graph()
    initial_state = State(file_path=file_path)
    
    try:
        app = graph.compile()
        final_state = app.invoke(initial_state)
        
        # Convert the final state to a dictionary manually
        structured_results = {
            "file_path": final_state["file_path"],
            "document_processed": final_state["document_processed"],
            "opportunity_evaluation": final_state["opportunity_evaluation"],
            "next_action": final_state["next_action"]
        }
        
        # Print a summary of the results
        print("\n--- Analysis Results ---")
        print(f"Document Processing: {'Successful' if 'Error' not in structured_results['document_processed'] else 'Failed'}")
        print(f"Details: {structured_results['document_processed']}")
        
        if isinstance(structured_results['opportunity_evaluation'], dict):
            print("\nOpportunity Evaluation:")
            print(f"Summary: {structured_results['opportunity_evaluation'].get('summary', 'N/A')}")
            print(f"Score: {structured_results['opportunity_evaluation'].get('score', 'N/A')}")
            print("MEDDIC Evaluation:")
            for criterion, evaluation in structured_results['opportunity_evaluation'].get('meddic_evaluation', {}).items():
                print(f"{criterion}: {evaluation}")
        else:
            print("\nOpportunity Evaluation:")
            print(f"Error: {structured_results['opportunity_evaluation']}")
        
        if isinstance(structured_results['next_action'], dict):
            print("\nNext Action:")
            print(f"Action: {structured_results['next_action'].get('next_action', 'N/A')}")
            print("Talking Points:")
            for i, point in enumerate(structured_results['next_action'].get('talking_points', []), 1):
                print(f"  {i}. {point}")
        else:
            print("\nNext Action:")
            print(f"Error: {structured_results['next_action']}")
        
        return structured_results
    
    except Exception as e:
        print(f"An error occurred during analysis: {str(e)}")
        return {"error": str(e)}

def create_opportunity_review_report(structured_results):
    opportunity_review_report = ""
    opportunity_review_report += "**Analysis Results**\n\n"
    if 'Error' in structured_results['document_processed']:
        opportunity_review_report += f"Opportunity Analysis Failed\n"

    else:
        if isinstance(structured_results['opportunity_evaluation'], dict):
            opportunity_review_report += f"**Summary:** {structured_results['opportunity_evaluation'].get('summary', 'N/A')}\n\n"
            opportunity_review_report += f"**Score:** {structured_results['opportunity_evaluation'].get('score', 'N/A')}\n\n"
            opportunity_review_report += "**MEDDIC Evaluation:**\n\n"
            for criterion, evaluation in structured_results['opportunity_evaluation'].get('meddic_evaluation', {}).items():
                opportunity_review_report += f"**{criterion}:** {evaluation}\n"
        
        if isinstance(structured_results['next_action'], dict):
            opportunity_review_report += "\n\n**Next Steps**\n\n"
            opportunity_review_report += f"{structured_results['next_action'].get('next_action', 'N/A')}\n\n"
            opportunity_review_report += "**Talking Points:**\n\n"
            for i, point in enumerate(structured_results['next_action'].get('talking_points', []), 1):
                opportunity_review_report += f"  {i}. {point}\n"
    file_path = "reports/HSBC Opportunity Review Report.md"
    save_md_file(file_path, opportunity_review_report)
    return opportunity_review_report

def save_md_file(file_path, file_content):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Existing file deleted: {file_path}")
        
        with open(file_path, 'w', encoding='utf-8') as md_file:
            md_file.write(file_content)
        print(f"File saved successfully: {file_path}")
    except PermissionError:
        print(f"Permission denied when trying to delete or save file: {file_path}")       
    
    return None 