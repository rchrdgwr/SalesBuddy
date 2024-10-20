class SessionState:
    session_stage = ""
    do_evaluation = False
    do_opportunity_analysis = False
    do_customer_research = False
    do_objections = False
    add_objections_to_analysis = True   
    ask_objections = True
    use_objection_cache = True
    do_ragas_evaluation = False
    customer_research_report_md = "HSBC Quarterly Report 2024-10-19.md"
    customer_research_report_pdf = "HSBC Quarterly Report 2024-10-19.pdf"
    bettetech_value_proposition_pdf = "BetterTech Lending Analytics Solution.pdf"
    do_voice = True
    status = "active"
    scenario = None
    qa_mode = "single"
    questions = []
    start_time = None
    end_time = None
    duration_minutes = None
    attitude = "Happy"
    mood_score = 5
    num_questions = 2
    current_question_index = 0
    previous_answer = None
    question = ""
    ground_truth = ""
    rep_answer = ""
    responses = []
    queries = []
    llm_responses = []
    command = ""
    scores = []
    llm_next_steps = ""
    opportunity_review_results = None
    opportunity_review_report = None
    def __init__(self):
        self.company = None
        self.customer = None
        self.opportunity = None
        self.scenario = None
        self.session_stage = "research"
        self.do_evaluation = False
        self.do_opportunity_analysis = False
        self.do_customer_research = False
        self.do_objections = False
        self.add_objections_to_analysis = True
        self.ask_objections = True
        self.use_objection_cache = True
        self.do_ragas_evaluation = False
        self.customer_research_report_md = "HSBC Quarterly Report 2024-10-19.md"
        self.customer_research_report_pdf = "HSBC Quarterly Report 2024-10-19.pdf"
        self.bettetech_value_proposition_pdf = "BetterTech Lending Analytics Solution.pdf"
        self.do_voice = True
        self.status = "active"
        self.scenario = None
        self.qa_mode = "single"
        self.questions = []
        self.start_time = None
        self.end_time = None
        self.duration_minutes = None
        self.attitude = "Happy"
        self.mood_score = 5
        self.num_questions = 2
        self.current_question_index = 0
        self.previous_answer = None
        self.question = ""
        self.ground_truth = ""
        self.rep_answer = ""
        self.responses = []
        self.queries = []
        self.llm_responses = []
        self.command = ""
        self.scores = []
        self.llm_next_steps = ""
        self.company = None
        self.customer = None
        self.opportunity = None
        self.scenario = None
        self.opportunity_review_results = None
        self.opportunity_review_report = None
    class Company:
        def __init__(self, name, description, product, product_summary, product_description):
            self.name = name
            self.description = description
            self.product = product
            self.product_summary = product_summary
            self.product_description = product_description

    class Customer:
        def __init__(self, name, contact_name, contact_role):
            self.name = name
            self.contact_name = contact_name
            self.contact_role = contact_role
            self.background = None


    class Opportunity:
        def __init__(self, id, name, stage, description, value, close_date, activity, next_steps):
            self.id = id
            self.name = name
            self.stage = stage
            self.description = description
            self.value = value
            self.close_date = close_date
            self.activity = activity
            self.next_steps = next_steps
            


    def add_company_info(self, name, description, product, product_summary, product_description):
        self.company = self.Company(name, description, product, product_summary, product_description)

    def add_customer_info(self, name, contact_name, contact_role):
        self.customer = self.Customer(name, contact_name, contact_role)

    def add_opportunity_info(self, id, name, stage, description, value, close_date, activity, next_steps):
        self.opportunity = self.Opportunity(id, name, stage, description, value, close_date, activity, next_steps) 

    def add_scenario_info(self, scenario_data):
        self.scenario = scenario_data
        self.add_opportunity_info(
            id=scenario_data['Opportunity ID'],
            name=scenario_data['Opportunity Name'],
            stage=scenario_data['Opportunity Stage'],
            description=scenario_data['Opportunity Description'],
            value=scenario_data['Opportunity Value'],
            close_date=scenario_data['Close Date'],
            activity=scenario_data['Activity'],
            next_steps=scenario_data['Next Steps']  
        )
        self.add_customer_info(
            name=scenario_data['Customer Name'],
            contact_name=scenario_data['Customer Contact'],
            contact_role=scenario_data['Customer Contact Role']
        )

    def get_opening(self):
        output_lines = [
            "**Simulation Scenario**",
            f"**Customer:** {self.customer.name if self.customer else 'Unknown'}",
            f"**Opportunity:** {self.opportunity.name if self.opportunity else 'Unknown'}",
            f"**Value:** {self.opportunity.value if self.opportunity and hasattr(self.opportunity, 'value') else 'Unknown'}",
            f"**Stage:** {self.opportunity.stage if self.opportunity else 'N/A'}",
            f"**Target Close Date:** {self.opportunity.close_date if self.opportunity and hasattr(self.opportunity, 'close_date') else 'Unknown'}",
            f"**Opportunity Description:** {self.opportunity.description if self.opportunity else 'Unknown'}",
            f"**Meeting with:** {self.customer.contact_name} ({self.customer.contact_role})",
            f"**Activity:** {self.opportunity.activity if self.opportunity and hasattr(self.opportunity, 'activity') else 'Unknown'}",
            f"**Current Meeting:** {self.opportunity.next_steps if self.opportunity and hasattr(self.opportunity, 'next_steps') else 'Unknown'}"
        ]
        output = "\n".join(output_lines)
        return output
    
    def __str__(self):
        company_info = f"{self.company.name} - " if self.company else ""
        customer_info = f"for {self.customer.name}" if self.customer else "No Customer"
        opportunity_info = f"{self.opportunity.name} ({self.opportunity.stage})" if self.opportunity else "No opportunity set"
        return f"{company_info}SessionState: {customer_info} {opportunity_info}".strip()
    
