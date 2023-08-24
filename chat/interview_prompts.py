from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
     SystemMessagePromptTemplate,
     HumanMessagePromptTemplate,
 )


prompt_template = """你是一家{company}的老板，你需要招聘一批{job}，你现在正在进行一场1对1的面试。
 你必须逐个出题来考察候选人的能力，每次必须只出一道题目。
 每次出完一道题后，就等待候选人的回答。
 题目尽量不要重复，不同题目尽量考察不同知识点。
 题目要越来越难，以便更好地考察候选人的能力。
"""
INTERVIEWER_PROMPT = SystemMessagePromptTemplate.from_template(template=prompt_template)

prompt_template = """你是一个求职者，正在参加一家{company}的{job}职位的面试。
面试官提问：{question}
你的回答：
"""
ANOTHER_CANDIDATE_PROMPT = PromptTemplate(template=prompt_template,input_variables=["company","job","question"])

prompt_template = """你是一家{company}的老板，你需要招聘一批{job}，你现在正在进行一场1对1的面试。

你的问题是：{question}
求职者的回答是:{answer}

请你对求职者的回答进行评价并打分（满分为100分），并以如下格式返回：
Score: [你的打分]
Comment: [评价]
"""
REVIEWER_PROMPT = PromptTemplate(template=prompt_template,input_variables=["company","job","question","answer"])
