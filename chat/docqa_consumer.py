import json
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import chat.maprerank as maprerank
from langchain.chains.llm import LLMChain
from langchain.prompts.prompt import PromptTemplate
import chat.prompts as prompts
from langchain.output_parsers.regex import RegexParser
from channels.consumer import SyncConsumer
import os,time


os.environ["OPENAI_API_KEY"] = "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"

class DocQAConsumer(SyncConsumer):

    def __init__(self):
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        self.classifier_llm_chain = LLMChain(llm=llm,prompt=prompts.CLASSIFIER_PROMPT)
        self.direct_llm_chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(input_variables=["question"],template="请用心理学知识回答该问题：{question}"))
        llm_chain = LLMChain(llm,prompt=prompts.PROMPT)
        embeddings_model = STEmbedding()
        vectorstore = FAISS.load_local("/home/work/psycho.vecstore",embeddings_model)
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

    def doc_question(self,message):
        question = message['question']
        username = message['username']
        print("doc_question:",question,username)
        #TODO: memory for conversation

        res = self.classifier_llm_chain(question)
        if res['text'].startswith('NO'):
            text = "我是一个心理学专业的助教，我会拒绝回答不相关问题。请重新提问！"
        else:
            text = res['text'][3:]
        self.channel_layer.group_send(username,{
                "type" : "sendMessage",
                "message":text,
                "username":username,
            })

        t0 = time.time()
        result = qa_chain({"query": question})
        self.channel_layer.group_send(username,{
                "type" : "sendMessage",
                "message":result["result"]["answer"],
                "username":username,
            })
        self.channel_layer.group_send(username,{
                "type" : "sendMessage",
                "message":result["result"]["_doc_"],
                "username":username,
            })
        self.channel_layer.group_send(username,{
                "type" : "sendMessage",
                "message":result["result"]["_doc_metadata_"],
                "username":username,
            })
        self.channel_layer.group_send(username,{
                "type" : "sendMessage",
                "message":"答案评分：" + result["result"]["score"],
                "username":username,
            })

    def bare_question(self, message):
        question = message['question']
        username = message['username']
        res = self.direct_llm_chain(question)
        self.channel_layer.group_send(username,{
                "type" : "sendMessage",
                "message":res['text'],
                "username":username,
            })

class PrintConsumer(SyncConsumer):
    def test_print(self, message):
        print("Test: " + message["text"])
