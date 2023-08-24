from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer


class STEmbedding(Embeddings):
    def __init__(self):
        super(Embeddings,self).__init__()
        self.model = SentenceTransformer('intfloat/multilingual-e5-large')

    def _get_emb(self,texts):
        return self.model.encode(texts,normalize_embeddings=False)


    async def aembed_documents(self,texts):
        return await self._get_emb(['passage:'+ c for c in texts])


    async def aembed_query(self,text):
        return await self._get_emb(['query:'+text])[0]


    def embed_documents(self,texts):
        return self._get_emb(['passage:'+ c for c in texts])


    def embed_query(self,text):
        return self._get_emb(['query:'+text])[0]


