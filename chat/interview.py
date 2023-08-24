import json
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain.chat_models import ChatOpenAI
from langchain.chains.llm import LLMChain
import tiktoken
from langchain.prompts.prompt import PromptTemplate
import chat.interview_prompts as interview_prompts
from langchain.output_parsers.regex import RegexParser
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)
import os,time
import asyncio

os.environ["OPENAI_API_KEY"] = "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"
os.environ["TOKENIZERS_PARALLELISM"]="false"
enc = tiktoken.get_encoding("cl100k_base")

MAX_TOKEN = 4000
class InterViewer:
    def __init__(self,sys_tmpl,company,job):
        assistant_sys_msg = sys_tmpl.format_messages(
            company=company,
            job=job,
        )[0]
        self.system_message = assistant_sys_msg
        self.model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
        self.init_messages()

    def reset(self):
        self.init_messages()
        return self.stored_messages

    def init_messages(self):
        self.stored_messages = [self.system_message]

    def filter_old_msg(self):
        token_cnt = [len(enc.encode(s.content)) for s in self.stored_messages]
        total_token = token_cnt[0]
        msg_len = 0 
        for l in token_cnt[1:][::-1]:
            if total_token + l > MAX_TOKEN:
                break
            total_token += l
            msg_len += 1
        self.stored_messages = [self.stored_messages[0]] + self.stored_messages[-msg_len:]

    def update_messages(self, message):
        self.stored_messages.append(message)
        len_msg = [len(enc.encode(s.content)) for s in self.stored_messages]
        self.filter_old_msg()
        return self.stored_messages

    def step(self):
        output_message = self.model(self.stored_messages)
        self.update_messages(output_message) 
        print('-'*20,'\n\n','\n\n'.join([s.content for s in self.stored_messages]),'\n\n','-'*20)
        return output_message

class ReViewer:
    def __init__(self,prompt,company,job):
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
        parser = RegexParser(
            regex=r"Score: (.*?)\n.*?Comment:(.*)",
            output_keys=["score", "comments"],
        )
        self.model = LLMChain(llm=llm,prompt=prompt,output_parser=parser)
        self.company = company
        self.job = job
        self.init_score()

    def init_score(self):
        self.stored_messages = []

    def review(self, question, answer):
        res = self.model({"company":self.company,"job":self.job,"question":question,"answer":answer})
        score = res['text']['score']
        comments = res['text']['comments']
        self.stored_messages.append((question,answer,comments,score))
        return comments,score

    def summary(self):
        total_score = 0
        text = ''
        for q,a,c,s in self.stored_messages:
            total_score += int(s)
        text += "综合得分：%.2f%%"%(total_score*1.0/len(self.stored_messages))
        return text



class InterviewConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        if self.groups is None:
            self.groups = []
        self.company = None
        self.job = None

    async def connect(self):
        print(self.scope["query_string"])
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        print("zoom name:",self.room_name,self.channel_name)
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()
        print("connect")

    async def disconnect(self , close_code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )
        print("disconnect")

    async def give_question(self,message):
        question = self.interviewer.step().content
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":question.replace('\n','<br/>'),
                "category": "ai",
                "username":"面试官",
            })  
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":"****TIPS:****\n输入pass可以跳过该问题。输入support可以让系统帮你回答。输入over查看成绩并结束面试。\n",
                "category": "system-done",
                "username":"面试官",
            })  
        self.question = question
    
    async def support(self,message):
        res = self.another_candidate({"company":self.company,"job":self.job,"question":self.question})
        reply = res["text"]
        self.interviewer.update_messages(HumanMessage(content=(reply)))
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":reply.replace('\n',"<br/>"),
                "category": "ai",
                "username":"系统回答",
            })  
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "review" ,
                "reply": message
            })
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "sendMessage" ,
                "message" : "正在评估你的答案...",
                "category": "system",
                "username" : "",
            })



    async def review(self,message):
        reply = message['reply']
        comments,score = self.reviewer.review(self.question,reply)
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":"%s/100"%(score,),
                "category": "ai",
                "username":"面试得分",
            })  
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":comments,
                "category": "ai",
                "username":"面试点评",
            })  
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "give.question" ,
            })

    async def receive(self, text_data):
        print("receive:",text_data)
        text_data_json = json.loads(text_data)
        if "category" in text_data_json and text_data_json["category"] == "init":
            self.company = text_data_json["company"]
            self.job = text_data_json["job"]
            self.interviewer = InterViewer(interview_prompts.INTERVIEWER_PROMPT,self.company,self.job)
            self.reviewer = ReViewer(interview_prompts.REVIEWER_PROMPT,self.company,self.job)
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
            self.another_candidate = LLMChain(llm=llm,prompt=interview_prompts.ANOTHER_CANDIDATE_PROMPT)
            await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":'你好，感谢你前来应聘"%s"岗位，我是这家%s的面试官，你准备好了吗?\n'%(self.job,self.company),
                "category": "ai",
                "username":"面试官",
            })  
            user_hi = '我已经准备好了，请开始提问吧！'
            await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":user_hi,
                "category": "user",
                "username":self.room_name,
            })  
            self.interviewer.update_messages(HumanMessage(content=(user_hi)))
            await self.channel_layer.group_send(self.room_name,{
                "type" : "give.question",
            })  
            return
        elif not self.company or not self.job:
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "sendMessage" ,
                    "message" : "请先选择企业性质和岗位性质",
                    "category": "system",
                    "username" : "",
                })
            return
        message = text_data_json["message"]
        username = text_data_json["username"]
        message = message.strip()
        if message == 'pass':
            message = "这个问题我不会，换下一个问题。"
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "sendMessage" ,
                    "message" : message,
                    "category":"user",
                    "username" : username ,
                })
            self.interviewer.update_messages(HumanMessage(content=(message)))
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "give.question" ,
                })
        elif message == 'support':
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "sendMessage" ,
                    "message" : message,
                    "category":"user",
                    "username" : username ,
                })
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "sendMessage" ,
                    "message" : "你选择了系统代答，系统正在生成答案...",
                    "category": "system",
                    "username" : "",
                })
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "support" ,
                })
        elif message == 'over':
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "sendMessage" ,
                    "message" : message,
                    "category":"user",
                    "username" : username ,
                })
            await self.channel_layer.group_send(
                self.room_name,{
                "type" : "sendMessage" ,
                "message" : self.reviewer.summary(),
                "category": "ai",
                "username" : "面试官",
            })
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "sendMessage" ,
                    "message" : "面试已经结束，请在上面选择’公司性质‘和’岗位性质‘重新开始...",
                    "category": "system-done",
                    "username" : "",
                })
        else:
            self.interviewer.update_messages(HumanMessage(content=(message)))
            await self.channel_layer.group_send(
                 self.room_name,{
                "type" : "sendMessage" ,
                "message" :message,
                "category":"user",
                "username" : username ,
            })
            await self.channel_layer.group_send(
                self.room_name,{
                    "type" : "review" ,
                    "reply": message
                })
            await self.channel_layer.group_send(
                self.room_name,{
                "type" : "sendMessage" ,
                "message" : "正在评估你的答案...",
                "category": "system",
                "username" : "",
            })

    async def sendMessage(self , event) :
        message = event["message"]
        username = event["username"]
        await self.send(text_data = json.dumps({"message":message ,"username":username,"category":event["category"]}))

