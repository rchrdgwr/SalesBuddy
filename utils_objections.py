import chainlit as cl
import tempfile
import uuid
from chainlit.types import AskFileResponse
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from operator import itemgetter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams



async def create_objections(session_state):
    if session_state.use_objection_cache:

        objections = [
            "1. Can you provide customer references in the banking and financial services industry?",
            "2. Second question, what training options are available for our team, given the number of employees and their global distribution?",
            "3. Last but not least, your pricing seems high compared to some other solutions we've seen. Can you provide any flexibility with HSBC's pricing?",
        ]

    else:
        customer_document_file = session_state.customer_research_report_pdf
        customer_file_path = "reports/" + customer_document_file
        bettertech_document_file = session_state.bettetech_value_proposition_pdf
        bettertech_file_path = "data/" + bettertech_document_file
        objections = await process_files(customer_file_path, bettertech_file_path)
    return objections



def process_value_prop_pdf(file_path) -> str:
    """
    Process the value proposition PDF file and return its content as a string.

    Args:
        file (AskFileResponse): The uploaded PDF file.

    Returns:
        str: The extracted content from the PDF.
    """
    # Create a temporary file to store the uploaded content
    # with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
    #     temp_file.write(file.content)
    #     temp_file_path = temp_file.name

    # Load the PDF using PyMuPDFLoader
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()

    # Combine the content of all pages into a single string
    value_prop_text = "\n".join(doc.page_content for doc in documents)

    # Return the text extracted from the PDF
    return value_prop_text

def process_text_file(file_path: str):
    # import tempfile
    text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n","\n"],chunk_size=200, chunk_overlap=20)
    # with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
    #     with open(temp_file.name, "wb") as f:
    #         f.write(file.content)

    loader = PyMuPDFLoader(file_path)
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
    return f"Response to your objection: {user_response['objection'][num],user_response['response'][num],  satify_0_1}"


async def process_files(customer_document, bettertech_document):
    objections = []
    core_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    collection_name = f"pdf_to_parse_{uuid.uuid4()}"
    qdrant_client = QdrantClient(":memory:")
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

    # msg = cl.Message(
    #     content=f"Processing Customer Business Domain...", disable_human_feedback=True
    # )
    # await msg.send()
    # Process the customer
    texts = process_text_file(customer_document)
    print(f"Processing {len(texts)} text chunks from Customer Research Report")


    # Notify the user that the second file is being processed
    # msg = cl.Message(
    #     content=f"Processing BetterTech Value Proposition...", disable_human_feedback=True
    # )
    # await msg.send()

    # Process the second file
    value_prop_content = process_value_prop_pdf(bettertech_document)
    print(f"Processing {len(value_prop_content)} text chunks from BetterTech Value Proposition")
    
    
    # Create a Local File Store for caching
    store = LocalFileStore("./cache/")
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        core_embeddings, store, namespace=core_embeddings.model
    )

    # QDrant Vector Store Setup
    vectorstore = QdrantVectorStore(
        client=qdrant_client,
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
    # sales_opportunity = await cl.AskUserMessage(
    #     content="Please describe the sales opportunity you want to discuss.", timeout=300
    # ).send()
    sales_opportunity = "Developing analytic capabilities for the loan origination system"
    #print(sales_opportunity['content'])
    # Retrieve the documents based on the query (here we're simulating with the sales opportunity)
    retrieved_docs = retriever.get_relevant_documents(value_prop_content)

    # Extract the content of the retrieved documents (chunks)
    context_chunks = [doc.page_content for doc in retrieved_docs]

    # Combine the retrieved context chunks into a single string
    context = "\n\n".join(context_chunks)

    # Log and display the retrieved chunks to Chainlit
    # await cl.Message(content=f"Retrieved context chunks:\n{context}", author="retriever").send()
    
    #print (sales_opportunity["content"])
    # Generate objections using the chain, with the context included
    #print ({"question": "Generate sales objections from {{value_prop_content}}", "sales_opportunity": sales_opportunity["content"], "context": context})
    objection_response = objection_chain.invoke({"question": "Generate 3 sales objections", "sales_opportunity": sales_opportunity, "context": context})

    objections.extend(objection_response.content.split('\n'))  # Assuming each objection is on a new line
    # Remove empty strings or strings with only spaces
    cleaned_objections = [objection for objection in objections if objection.strip()]

    # Output the cleaned list
    # print(cleaned_objections)

    # Store the objection chain in user session
    cl.user_session.set("objection_chain", objection_chain)
    cl.user_session.set("objections", objections)
    return cleaned_objections
    #await cl.Message(content="We are ready to enter Sales simulation. Ok? ").send()