from ragas.metrics.base import MetricWithLLM, SingleTurnMetric
from ragas.prompt.pydantic_prompt import PydanticPrompt
from pydantic import BaseModel, Field
import pandas as pd
from typing import List, Tuple
from datetime import datetime
import sys
from dataclasses import dataclass, field
from ragas.metrics.base import MetricType
from ragas.messages import AIMessage, HumanMessage, ToolMessage, ToolCall
from ragas import SingleTurnSample, MultiTurnSample
import typing as t
import asyncio
import dotenv
import os
# Load environment variables from .env file
dotenv.load_dotenv()

# Access the OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class ObjectionInput(BaseModel):
    user_input: str = Field(description="The objection text")
    response: str = Field(default="", description="The response to the objection")
    reference: str = Field(default="", description="Any reference related to the objection")


class ObjectionOutput(BaseModel):
    satisfy: bool = Field(description="Boolean indicating if the objection was satisfied")

def process_salesbud_file(file_path: str) -> List[Tuple[ObjectionInput, ObjectionOutput]]:
    """
    Process the salesbud CSV file and return a list of examples for ObjectionlPrompt.

    Args:
        file_path (str): The path to the salesbud CSV file.

    Returns:
        List[Tuple[ObjectionInput, ObjectionOutput]]: A list of tuples containing ObjectionInput and ObjectionOutput.
    """
    # Print the timestamp and the file being processed
    print(f"{datetime.now()}: Processing file: salesbud_examples.csv")

    # Read the CSV file into a DataFrame
    df = pd.read_csv('data/salesbud_examples.csv')

    # List to hold the processed objections
    examples = []  # List to hold examples

    # Process each row in the DataFrame
    for index, row in df.iterrows():
        # Create an ObjectionInput instance for each row
        objection_input = ObjectionInput(
            user_input=row['objection'],  # Assuming your CSV has a column named 'objection'
            response=row.get('response', ""),  # Use .get() to avoid KeyError if the column doesn't exist
            reference=row.get('reference', "")  # Use .get() to avoid KeyError if the column doesn't exist
        )
        
        # Create an ObjectionOutput instance (you can modify the logic for 'satisfy' as needed)
        objection_output = ObjectionOutput(
            satisfy= row['satisfy']
        ) 
        # Append the example tuple to the examples list
        examples.append((objection_input, objection_output))
    #print (examples[0])
    return examples

class ObjectionlPrompt(PydanticPrompt[ObjectionInput, ObjectionOutput]):
    instruction = "You are an expert technology sales rep that is tasked with judging if response satisfies potential customer's objection (user input). \
    Given an user input and sales rep response, output True if the response satisfies the objection by the potential customer"
    input_model = ObjectionInput
    output_model = ObjectionOutput
    examples = process_salesbud_file('salesbud_examples.csv')

@dataclass
class SatisfyRate(MetricWithLLM, SingleTurnMetric):
    name: str = "satisfy_rate"
    _required_columns: t.Dict[MetricType, t.Set[str]] = field(
        default_factory=lambda: {MetricType.SINGLE_TURN: {"response", "reference"}}
    )
    objection_prompt: PydanticPrompt = ObjectionlPrompt()

    async def _ascore(self, row):
        pass

    async def _single_turn_ascore(self, sample, callbacks):
        prompt_input = ObjectionInput(
            user_input=sample.user_input, response=sample.response
        )
        prompt_response = await self.objection_prompt.generate(
            data=prompt_input, llm=self.llm
        )
        return int(prompt_response.satisfy)
    
async def generate_objection_scores(question_answer):
    from langchain_openai import ChatOpenAI
    from ragas.llms.base import LangchainLLMWrapper
    import pandas as pd
    # user_response= pd.read_csv(file_path)
    openai_model = LangchainLLMWrapper(ChatOpenAI(model_name="gpt-4o", api_key=OPENAI_API_KEY))
    scorer = SatisfyRate(llm=openai_model)
    
    sample = SingleTurnSample(user_input=question_answer['objection'], response=question_answer['answer'])
    
    #(user_response['objection'][num], user_response['response'][num])
    satisfy_0_1 = await scorer.single_turn_ascore(sample)
    
    print (question_answer['objection'], question_answer['answer'], satisfy_0_1)
    # Implement your logic to generate a response based on the user's input
    return satisfy_0_1 #f"Response to your objection: {user_response['objection'][num]}, {user_response['response'][num]}, {satisfy_0_1}" 

    
async def generate_response_to_objection(file_path, num):
    from langchain_openai import ChatOpenAI
    from ragas.llms.base import LangchainLLMWrapper
    import pandas as pd
    user_response= pd.read_csv(file_path)
    openai_model = LangchainLLMWrapper(ChatOpenAI(model_name="gpt-4o", api_key=OPENAI_API_KEY))
    scorer = SatisfyRate(llm=openai_model)
    
    sample = SingleTurnSample(user_input=user_response['objection'][num], response=user_response['response'][num])
    
    #(user_response['objection'][num], user_response['response'][num])
    satisfy_0_1 = await scorer.single_turn_ascore(sample)
    
    print (user_response['objection'][num], user_response['response'][num], satisfy_0_1)
    # Implement your logic to generate a response based on the user's input
    return satisfy_0_1 #f"Response to your objection: {user_response['objection'][num]}, {user_response['response'][num]}, {satisfy_0_1}" 

async def main(file_path):
    # Call the async function
    #examples_file = process_salesbud_file()
    response = await generate_response_to_objection(file_path, 0)

if __name__ == "__main__":
    # Check if the file path is provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python objection_eval.py <path_to_salesbud.csv>")
        sys.exit(1)

    # Get the file path from the command-line argument
    file_path = sys.argv[1]

    # Run the main async function
    asyncio.run(main(file_path))