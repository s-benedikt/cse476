# Final Project CSE 476

This project implements an inference-time agent that solves reasoning heavy problems.

It implements the following inference time techniques:  
\- Self Consistency  
\- Critic to evaluate an answer  
\- Plan and solve 

**To run:**

- Create a .venv  
- Install the requirements.txt  
- Run generate\_answer\_template.py 

\`\`\`  
python \-m venv .venv  
source .venv/bin/activate  \# macOS/Linux  
pip install \-r requirements.txt  
python3 generate\_answer\_template.py  
\`\`\`  
**Resources**:  
Find the Github repository [here](https://github.com/s-benedikt/cse476.git).  
Find the output file [here](https://drive.google.com/file/d/15HYe2buiZA1zq9hJqyIWzQDq98WQHF_7/view?usp=sharing).  
This report can be found [here](https://docs.google.com/document/d/13LHQmY7XkVWbH39y-PG6GdeZIk35gSMVZW2GYyD1_9w/edit?usp=sharing).

**How the software works**:  
main.py:  
When generate\_answer\_template.py is started, it launches main.py  (you could also run main.py directly if you don’t want the format validation). The main script then instanciates an Agent and runs every query by giving it to the agent.  
agent.py:  
The agent implements three inference-time algorithms:

- Self-Consistency (SC) \- short, no reasoning  
- Chain-of-Thought (CoT) \- longer, with reasoning  
- Critic \- Selects better answer

SC and CoT are running in parallel for performance reasons.  
If SC and CoT disagree, the agent invokes a third LLM call: the critic.  
The critic will then output the answer it thinks is the correct answer.  
Both answers are run through a getAnswer function which tries to retrieve the answer.   
First, it searches for lines beginning with “Final”, “Answer”, or “Result” and strips punctuation and dollar signs. If the hard coded match fails, it asks a LLM to retrieve the answer.  
For evaluation, the agents calls the LLM with the prediction and the solution and asks it if they match. This returns a Yes or a No response.  
api.py:  
Implements the API as seen in the Jupyter Notebook.  
Package:  
The input is hardcoded to /final/cse\_476\_final\_project\_test\_data.json.  
The output is hardcoded to /output/output.json  
If you want to change this, go to main.py, scroll to the bottom and alter the default path in the command line parser.

