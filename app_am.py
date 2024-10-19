import os
from typing import List, Dict
from chainlit.types import AskFileResponse
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.storage import LocalFileStore
from langchain.embeddings import CacheBackedEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.globals import set_llm_cache
from langchain_openai import ChatOpenAI
from langchain_core.caches import InMemoryCache
from operator import itemgetter
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain.schema.runnable.config import RunnableConfig
from langsmith.evaluation import LangChainStringEvaluator, evaluate
from datetime import datetime
from utils_evaluate_objections import generate_response_to_objection
import pandas as pd 
import uuid
import chainlit as cl
import dotenv
import tempfile

## Aaron to improve
## add customer-based value prop to load: 
## compare and contract sales rep value prop & business domain
## use that list to generate objections that is close to sales opportunity 

# Load environment variables from .env file
dotenv.load_dotenv()

# Access the OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

set_llm_cache(InMemoryCache())

def process_value_prop_pdf(file: AskFileResponse) -> str:
    """
    Process the value proposition PDF file and return its content as a string.

    Args:
        file (AskFileResponse): The uploaded PDF file.

    Returns:
        str: The extracted content from the PDF.
    """
    # Create a temporary file to store the uploaded content
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
        temp_file.write(file.content)
        temp_file_path = temp_file.name

    # Load the PDF using PyMuPDFLoader
    loader = PyMuPDFLoader(temp_file_path)
    documents = loader.load()

    # Combine the content of all pages into a single string
    value_prop_text = "\n".join(doc.page_content for doc in documents)

    # Return the text extracted from the PDF
    return value_prop_text

text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n","\n"],chunk_size=200, chunk_overlap=20)

# QDrant Client Setup
collection_name = f"pdf_to_parse_{uuid.uuid4()}"
client = QdrantClient(":memory:")
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Embedding Model
core_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Internal object to store objections
objections = []

def process_text_file(file: AskFileResponse):
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with open(temp_file.name, "wb") as f:
            f.write(file.content)

    Loader = PyMuPDFLoader
    loader = Loader(temp_file.name)
    documents = loader.load()
    docs = text_splitter.split_documents(documents)
    for i, doc in enumerate(docs):
        doc.metadata["source"] = f"source_{i}"
    return docs

# Function to generate a response to the user's objection
def generate_response_to_objection(user_response, num):
    from langchain_openai import ChatOpenAI
    from ragas.llms.base import LangchainLLMWrapper
    openai_model = LangchainLLMWrapper(ChatOpenAI(model_name="gpt-4o"))
    scorer = SatisfyRate(llm=openai_model)
    
    satify_0_1 = scorer.single_turn_ascore(user_response['objection'][num], user_response['response'][num])
    # Implement your logic to generate a response based on the user's input
    return f"Response to your objection: {user_response['objection'][num],user_response['response'][num],  satify_0_1}" # Placeholder response


@cl.on_chat_start
async def on_chat_start():
    # Ask for the first PDF file (Potential Customer Business Domain)
    files = None
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload a PDF for Potential Customer Business Domain to begin!",
            accept=["application/pdf"],
            max_size_mb=2,
            timeout=180,
        ).send()

    first_file = files[0]

    # Notify the user that the file is being processed
    msg = cl.Message(
        content=f"Processing `{first_file.name}`...", disable_human_feedback=True
    )
    await msg.send()

    # Process the first file
    texts = process_text_file(first_file)
    print(f"Processing {len(texts)} text chunks from the first file")

    # Ask for the second PDF file (Value Proposition)
    files = None
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload our customer-specific value proposition PDF.",
            accept=["application/pdf"],
            max_size_mb=2,
            timeout=180,
        ).send()

    second_file = files[0]

    # Notify the user that the second file is being processed
    msg = cl.Message(
        content=f"Processing `{second_file.name}`...", disable_human_feedback=True
    )
    await msg.send()

    # Process the second file
    value_prop_content = process_value_prop_pdf(second_file)
    print(f"Processing {len(value_prop_content)} text chunks from the second file")
    #print(value_prop_content)
    
    
    
    # Create a Local File Store for caching
    store = LocalFileStore("./cache/")
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        core_embeddings, store, namespace=core_embeddings.model
    )

    # QDrant Vector Store Setup
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=cached_embedder
    )
    vectorstore.add_documents(texts)
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 5})

    chat_openai = ChatOpenAI() #model='gpt-4o')

    # RAG Chain for generating objections
    objection_prompt_template = """\
    Internally, review the value proposition information of sales rep's company then review your Context. 
    Internally, find areas where the sales' product/service could help add value and where it fails to fit.
    Internally, review this final list and think step-by-step on what likely objections to buying product/service.
    Using these thoughts, generate 5 Context-based sales objections.
    The output is numbered objections only.
    For example:
    '1. Our current pricing structure is already optimized and we do not see the immediate need for AI assistance in pricing complex structural options in Foreign Exchange.'
    '2. We have a dedicated team handling customer experience and efficiency, and we do not see how integrating AI for pricing options would significantly improve these aspects.',
    '3. While we acknowledge the importance of technology and innovation in banking, we are currently focusing on other areas for digital transformation and do not prioritize the use of AI in pricing at this time.'
    '4. Our customer base might not be ready for a shift towards AI-driven pricing models, and introducing such a change could potentially create confusion and resistance among our clients.',
    '5. We are cautious about the potential risks and uncertainties associated with relying heavily on AI for pricing, especially in the volatile Foreign Exchange market where human expertise and judgment are highly valued.'
    The output is NOT intro phrases or ** text **:
    Context: {context}
    Value Proposition: {{value_prop_content}}
    Sales Opportunity: {{sales_opportunity}}
    """

    # Create a chain for generating objections with the retrieved context
    objection_chain = (
        {"context": itemgetter("question") | retriever} 
        | RunnablePassthrough.assign(context=itemgetter("context")) 
        | ChatPromptTemplate.from_messages([
            ("system", "You a potential customer interested in the offering from this sales rep. Please use context business name and your name found in sales_opportunity."),
            ("human", objection_prompt_template)
        ])
        | chat_openai
    )

    # Ask the user for the sales opportunity
    sales_opportunity = await cl.AskUserMessage(
        content="Please describe the sales opportunity you want to discuss.", timeout=300
    ).send()

    #print(sales_opportunity['content'])
    # Retrieve the documents based on the query (here we're simulating with the sales opportunity)
    retrieved_docs = retriever.get_relevant_documents(value_prop_content)

    # Extract the content of the retrieved documents (chunks)
    context_chunks = [doc.page_content for doc in retrieved_docs]

    # Combine the retrieved context chunks into a single string
    context = "\n\n".join(context_chunks)

    # Log and display the retrieved chunks to Chainlit
    await cl.Message(content=f"Retrieved context chunks:\n{context}", author="retriever").send()
    
    #print (sales_opportunity["content"])
    # Generate objections using the chain, with the context included
    #print ({"question": "Generate sales objections from {{value_prop_content}}", "sales_opportunity": sales_opportunity["content"], "context": context})
    objection_response = objection_chain.invoke({"question": "Generate 3 sales objections", "sales_opportunity": sales_opportunity["content"], "context": context})

    objections.extend(objection_response.content.split('\n'))  # Assuming each objection is on a new line
    # Remove empty strings or strings with only spaces
    cleaned_objections = [objection for objection in objections if objection.strip()]

    # Output the cleaned list
    print(cleaned_objections)

    # Store the objection chain in user session
    cl.user_session.set("objection_chain", objection_chain)
    cl.user_session.set("objections", objections)

    await cl.Message(content="We are ready to enter Sales 'Sparring'. Ok? ").send()

@cl.on_message
async def main(message):
    """
    This function will be called every time a message is received from a session.

    We will use the LCEL RAG chain to generate a response to the user query.

    The LCEL RAG chain is stored in the user session, and is unique to each user session - this is why we can access it here.
    """
    await cl.AskUserMessage(
        content="Are you ready?", timeout=300
    ).send()

    objection_chain = cl.user_session.get("objection_chain")

    #msg = cl.Message(content="")

    # Retrieve the list of objections
    objections = cl.user_session.get("objections")
    #print (objections[0])
    objection_responses = {}

    # Iterate through each objection
    for i, objection in enumerate(objections):
        # Return the objection in the form of a question
        await cl.Message(content=f"Objection: {objection}").send()

        # Capture user input
        user_response = await cl.AskUserMessage(
            content="How would you respond to this objection?", timeout=600
        ).send()

        objection_responses[objection] = user_response['content']

        # Process the user's response (you can implement your logic here)
        #new_objection_response = generate_response_to_objection(user_response.content)

        # Send the response back to the user
        #await cl.Message(content=f"Response to objection {i + 1}: {new_objection_response}").send()
    print (objection_responses)
    data = []
    for objection, response in objection_responses.items():
        data.append({
            "timestamp": datetime.now(),  # Capture the current timestamp
            "objection": objection,
            "response": response
        })

    # Create a DataFrame
    user_response = pd.DataFrame(data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    #response = await generate_response_to_objection(user_response, 0)
    #user_response.to_csv(f'data/user_response_{timestamp}.csv', index=False)


