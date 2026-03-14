

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
from dotenv import load_dotenv
from src.finance_agent import FinanceAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.prompts import PromptTemplate



load_dotenv()

def main():
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        
        finance_logic = FinanceAgent()
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
        
        tools = [
            finance_logic.analyze_financial_data,
            finance_logic.predict_future_spending
        ]

    
        template = """Respond to the human as helpfully and accurately as possible. 
        You have access to the following tools:


                {tools}

        Use a json blob to specify a tool by providing an action key (tool name) 
        and an action_input key (tool input).

        Valid "action" values: "Final Answer" or {tool_names}

        Provide only ONE action per $JSON_BLOB, as shown:

        ```
        {{
          "action": "tool name",
          "action_input": "tool input"
        }}
        ```

        Begin!

        Question: {input}
        Thought: {agent_scratchpad}
        """

        prompt = PromptTemplate.from_template(template)
        
        # Create the Agent
        agent = create_structured_chat_agent(llm, tools, prompt)
        
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, 
            handle_parsing_errors=True
        )

        print("\n--- Agent Online (System Variables Fixed) ---")
        
        query = "Analyze 'data/financial_data.csv' and tell me if there are anomalies."
        agent_executor.invoke({"input": query})

    except Exception as e:
        print(f"Main Loop Error: {e}")

if __name__ == "__main__":
    main()