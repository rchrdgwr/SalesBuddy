import pandas as pd
import os

def get_questions(stage=None, num_questions=0):
    q_and_a_filename = "AIE4_SalesBuddy_QandA.csv" 
    data = read_csv_from_data_folder(q_and_a_filename)
    if data is None:
        print(f"Error: Failed to read {q_and_a_filename}")
        return []
    questions = []
    for index, row in data.iterrows():
        if stage is not None and row['Stage'] != stage:
            continue    
        question = {
            'stage': row['Stage'],
            'question': row['Customer Question (Provided by Claude)'],
            'ground_truth': row['Ground Truth (Provided by Nitin). Marked as Salesperson 2 by Claude'],
        }
        if num_questions == 0 or num_questions > len(questions):
            print(f"Adding question: {question['question']}")
            questions.append(question)
    print(f"Returned {len(questions)} questions for stage {stage}")
    return questions

def get_customer_background(scenario, customer_name="HSBC" ):
    background_filename = f"{customer_name}_background.txt"
    data = read_txt_from_data_folder(background_filename)
    scenario.customer.background = data
    print(f"Read background for {customer_name} - {background_filename}")

def get_company_data(scenario):
    company = {
        "name": "BetterTech",
        "description": """
            Founded by industry experts, BetterTech understands the data analytics challenges faced by financial 
            institutions across lending desks, risk, and compliance. 
            BetterTech pioneered the use of high-performance analytics in finance, helping the banks and lenders 
            make better decisions, explain results with confidence, and simulate the impact of their decisions. 
            BetterTech’s mission is to deliver train-of-thought analysis on terabytes of data in the most 
            cost-effective way so clients can explain their results with confidence and model the scenarios 
            that will optimize their business. BetterTech specializes in risk data analytics for one of the 
            fastest moving and most regulated industries with a presence in the world’s leading 
            financial marketplaces - London, New York, Singapore, Sydney, Hong Kong, Paris and Frankfurt. 
        """,
        "product": "BetterTech Lending Analytics Solution", 
        "product_summary": """
            A comprehensive solution for real-time analysis in lending, surpassing basic regulatory compliance 
            by enabling reporting, explaining, and optimizing. Deployed as SaaS, on-premise, or in the cloud, it 
            empowers organizations to improve performance, enhance decision-making, and stay competitive by 
            simulating various scenarios efficiently and accurately.
        """,
        "product_description": """
            Real-time analysis with BetterTech Lending Analytics 
            While most technologies on the market are able to fulfill regulatory risk management requirements, 
            they often fall short of meeting the team’s actual needs. What works when Lending Analytics calculations 
            are run weekly or monthly is simply not enough on a day-to-day basis. Maintaining regulations is no 
            longer enough 

            There are three functions that an efficient Lending Analytics solution must be able to fulfill: 
            report, explain and optimize. 

            Reporting is what every solution made for Lending Analytics can do: calculating risk figures and 
            generating reports at the right level of aggregation that are ready to be sent to internal and 
            external auditors. With the data volumes involved with Lending Analytics, however, reporting alone 
            is simply not enough. Explaining is the most critical need for business users. Regulators ask for 
            detailed explanations of what is included in the report, request that banks test alternative stress 
            scenarios, and demonstrate the accuracy of their models — particularly with the Internal Models Approach. 
            With a solution that only reports, business teams end up scrambling to answer those requests as best 
            as they can, falling back on other tools such as Excel or PowerBI, which are simply not designed to 
            analyze data at this scale. Optimizing is where growth and profitability reside. 
            Lending Analytics framework creates many decision points that are crucial to improving performance: 
            • How best to organize or reorganize loan portfolios? 
            • What would be the impact of changing positions or making certain loans? 
            • How can we improve our models? 

            BetterTech Lending Analytics handles this level of analysis deftly and can quickly answer these questions. 
            By relying on inadequate tools to perform analysis, organizations often see reduced productivity and 
            accuracy. Inaccurate reporting negatively impacts relationships with regulators, potentially leading 
            to fines, leading to fines. Furthermore, companies that do not have the analytical capabilities to 
            optimize their risk management and, by extension their capital charge, risk falling behind other, 
            better equipped organizations. How can you get ahead if you cannot efficiently simulate different 
            scenarios to choose the best outcome, while your competitors do it dozens of times a day? 

            A robust analytics solutions that is affordable and easy to implement 

            BetterTech Lending Analytics is in production today at many banks of all sizes around the world, 
            including HSBC, Erste Bank, CIBC and Mizuho. It has successfully passed the ISDA Lending Analytics 
            SA Regulatory Benchmarking Unit Test. It has even been selected by one of the most important global 
            regulators to serve as the benchmark against which to test other banks’ architectures. 

            Available as SaaS or on-premise, BetterTech Lending Analytics can run on any Cloud platform or 
            in-house hardware and be fully deployed within 4 to 6 weeks. 

            Runs anywhere BetterTech Lending Analytics can be deployed under several configurations that all 
            bring the same benefits. Reach out to our team of experts to find the setup that will work best for 
            your organization. 

            On-premise: BetterTech Lending Analytics can be deployed on a large variety of hardware that are 
            able to provide the requisite capabilities. We have partnerships in place with most global providers 
            to ensure compatibility. In the Cloud: We have extensively tested BetterTech Lending Analytics on 
            all the main cloud platforms (Azure, AWS, Google Cloud...). In fact, it has been deployed in production 
            on those platforms. 

            As SaaS: We can provide BetterTech Lending Analytics under a managed services contract. This 
            configuration offers the fastest time-to-production while giving you complete control over your 
            investment. The future of market risk analytics Organizations who want to outsmart the competition 
        """,
    }
    scenario.add_company_info(
        name=company['name'],
        description=company['description'],
        product=company['product'],
        product_summary=company['product_summary'],
        product_description=company['product_description']
    )

def get_q_and_a():
    q_and_a_filename = "AIE4_SalesBuddy_QandA.csv" 
    data = read_csv_from_data_folder(q_and_a_filename)
    return data

def get_opportunities():
    opportunities_filename = "Opportunity_Information.csv" 
    data = read_csv_from_data_folder(opportunities_filename)
    return data

def read_csv_from_data_folder(filename, handle_nan='drop'):
    data_folder = "./data/"
    file_path = os.path.join(data_folder, filename)

    try:
        df = pd.read_csv(file_path)
        print(f"Successfully read {filename}")
        # Handle NaN values
        if handle_nan == 'drop':
            df = df.dropna()
        elif handle_nan == 'fill_na':
            df = df.fillna('N/A')
        elif handle_nan == 'fill_empty':
            df = df.fillna('')
        else:
            print(f"Warning: Unknown NaN handling method '{handle_nan}'. NaN values were not processed.")
        
        # Reset index if rows were dropped
        df = df.reset_index(drop=True)
        return df
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found in the data folder.")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: File '{filename}' is empty.")
        return None
    except Exception as e:
        print(f"An error occurred while reading '{filename}': {str(e)}")
        return None
    
def read_txt_from_data_folder(filename):
    data_folder = "./data/"
    file_path = os.path.join(data_folder, filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = file.read()
        print(f"Successfully read {filename}")
        return data
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found in the data folder.")
        return None
    except Exception as e:
        print(f"An error occurred while reading '{filename}': {str(e)}")
        return None

    