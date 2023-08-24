import json
import langchain
langchain.verbose = True
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import chat.maprerank as maprerank
from langchain.chains.llm import LLMChain
from langchain.prompts.prompt import PromptTemplate
import chat.prompts as prompts
from langchain.output_parsers.regex import RegexParser
from chat.st_embedding import STEmbedding
import os,time
import asyncio

os.environ["OPENAI_API_KEY"] = "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"
embeddings_model = STEmbedding()
vectorstore = FAISS.load_local("/home/work/psycho.vecstore",embeddings_model)
print("new vectorstore")

class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        if self.groups is None:
            self.groups = []
        self.memory = ["","","","","",""]
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
        parser1 = RegexParser(
            regex=r"Score:(.*?)\n+Reason:(.*)",
            output_keys=['score','reason'],
        )
        self.classifier_llm_chain = LLMChain(llm=llm,prompt=prompts.CLASSIFIER_PROMPT,output_parser=parser1)
        self.direct_llm_chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(input_variables=["question"],template="请用心理学知识回答该问题：{question}"))
        parser1 = RegexParser(
            regex=r"Final Question: (.*?)\n+Reason:(.*)",
            output_keys=['final_q','reason'],
        )
        self.complete_llm_chain = LLMChain(
            llm=llm,
            prompt=prompts.COMPLETE_PROMPT,
            output_parser=parser1
        )

        self.qa_chain = None
        self.last_question = None
        print("new consumer:",hash(self))

    async def connect(self):
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
    
    def add_memory(self,question,answer):
        for i in range(4):
            self.memory[i] = self.memory[i+2]
        self.memory[-2] = "问:"+question
        self.memory[-1] = "答:"+answer

    async def classify(self,message):
        question = message["question"]
        username = message["username"]
        if not self.qa_chain:
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
            llm_chain = LLMChain(llm=llm,prompt=prompts.PROMPT)
            combine_documents_chain = maprerank.MyMapRerankDocumentsChain(
                llm_chain=llm_chain,
                rank_key="score",
                answer_key="answer",
                document_variable_name="context",
            )   
            self.qa_chain = RetrievalQA(
                retriever=vectorstore.as_retriever(search_type="mmr",search_kwargs={'k': 3}),
                return_source_documents=True,
                combine_documents_chain=combine_documents_chain)
        #TODO: memory for conversation

        res = self.classifier_llm_chain(question)
        score = int(res["text"]["score"].strip())
        if score < 50:
            text = "我是一个心理学专业的助教，我会拒绝回答不相关问题。请重新提问！"
        else:
            text = res['text']["score"]
        print("classify:",res,self.room_name,username)
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":text,
                "category": "ai",
                "username":"评估结果",
            })  

        if score < 50:
            return
        
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "sendMessage" ,
                "message" : "正在搜寻相关资料并准备答案...",
                "category": "system",
                "username" : "助教",
            })
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "doc.question" ,
                "question" : question,
                "username" : username ,
            })
    
    async def complete_question(self,message):
        question = message["question"]
        username = message["username"]
        if len("".join(self.memory).strip()) > 0:
            res = self.complete_llm_chain({'context':'\n'.join(self.memory),'question':question})
            question = res['text']['final_q']
            await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":question,
                "category": "ai",
                "username":"最终问题",
            })  
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "sendMessage" ,
                "message" : "正在评估是否心理学相关问题...",
                "category": "system",
                "username" : "助教",
            })
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "classify" ,
                "question" : question,
                "username" : username ,
            })


    async def doc_question(self,message):
        question = message["question"]
        username = message["username"]
        t0 = time.time()
        result = self.qa_chain({"query": question})
        print("answer:",result["result"]["answer"])
        print("doc:",result["result"]["_doc_"])
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":result["result"]["answer"].replace("\n","<br/>"),
                "username":"回答",
                "category": "ai",
            })
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":result["result"]["_doc_"].replace("\n","<br/>"),
                "username":"相关材料",
                "category": "ai",
            })
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":str(result["result"]["_doc_metadata_"]["source"]).split('/')[-1],
                "username":"材料出处",
                "category": "ai",
            })
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message": result["result"]["score"],
                "username":"答案评分",
                "category": "ai",
            })
        print("score:",int(result["result"]["score"]))
        self.add_memory(question,result["result"]['answer'])
        if int(result["result"]["score"]) < 100:
            text = "由于提供的文档不够充分，该回答可能不够完善。是否不基于文档作答？（y/n）"
        else:
            text = "回答完成，期待新的问题..."
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "sendMessage" ,
                "message" : text,
                "category": "system-done",
                "username" : "助教",
            })

    async def bare_question(self,message):
        question = message["question"]
        username = message["username"]
        res = self.direct_llm_chain(question)
        print("bare answer:",res)
        await self.channel_layer.group_send(self.room_name,{
                "type" : "sendMessage",
                "message":res['text'].replace("\n","<br/>"),
                "category": "ai",
                "username":username,
            })
        self.add_memory(question,res["text"])
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "sendMessage" ,
                "message" : "回答完成，期待新的问题...",
                "category": "system-done",
                "username" : "助教",
            })
    
    async def receive(self, text_data):
        print("receive:",text_data)
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = text_data_json["username"]
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "sendMessage" ,
                "message" : message ,
                "category":"user",
                "username" : username ,
            })
        if message.strip() == 'y' and self.last_question:
            await self.channel_layer.group_send(
                self.room_name,{
                "type" : "sendMessage" ,
                "message" : "尝试不基于参考文档作答...",
                "category": "system",
                "username" : "助教",
            })
            await self.channel_layer.group_send(
                self.room_name,{
                "type" : "bare.question" ,
                "question" : self.last_question,
                "username" : username ,
            })
            return
        if len("".join(self.memory).strip()) > 0:
            await self.channel_layer.group_send(
                self.room_name,{
                "type" : "sendMessage" ,
                "message" : "正在基于上下文补全问题...",
                "category": "system",
                "username" : "助教",
            })
        await self.channel_layer.group_send(
            self.room_name,{
                "type" : "complete.question" ,
                "question" : message ,
                "username" : username ,
            })
        self.last_question = message

    async def sendMessage(self , event) :
        message = event["message"]
        username = event["username"]
        await self.send(text_data = json.dumps({"message":message ,"username":username,"category":event["category"]}))

