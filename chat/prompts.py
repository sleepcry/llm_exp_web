from langchain.output_parsers.regex import RegexParser
from langchain.prompts import PromptTemplate


parser2 = RegexParser(
    regex=r"Score: (.*?)\n.*?Answer:(.*)",
    output_keys=["score", "answer"],
)
#''切记：Score为必填字段，无论任何情况都需要返回Score。
prompt_template = """阅读"Context"中的信息然后用中文回答"Question"描述的问题，你的答案必须源自于Context中的内容。
除了问题的答案，你必须评估一个分数"Score"来表示你多大程度上回答了用户的问题。如果你无法获取答案，回答你不知道并评估分数，不要试图编造答案。
按照如下格式进行回答：

--------
Score: [你评估的分数，分数为区间[0,100]的整数值，最小为0，最大为100]
Helpful Answer: [你的答案]
--------

如何评分：
- 分数Score越高代表回答越完整。
- Score=100,代表你认为答案准确地回答了"Question"中的问题，并且包含了充分的层次和细节。
- Score=0,表示你认为文档中的内容中完全找不到"Question"中问题的答案。
- 认真评估问题和答案的相关性，不要轻易给满分。

Example #1

Context:
---------
苹果是红色的。
---------
Question: 苹果是什么颜色的？
Score: 100
Helpful Answer: 红色 

Example #2

Context:
---------
当时是夜晚并且证人忘掉戴眼睛，因此他不是很确定那是一辆运动型轿车还是一辆SUV。
---------
Question: 那是一辆什么类型的车？
Score: 60
Helpful Answer: 运动型轿车或者SUV

Example #3

Context:
---------
梨子是要么是红色要么是橘色的
---------
Question: 苹果是什么颜色的？
Score: 0
Helpful Answer: 这篇文档没有对应答案。

现在开始吧！

Context:
---------
{context}
---------
Question: {question}
"""
PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"],
    output_parser=parser2
)

prompt_template = """ 评估问题是否心理学相关问题，回答必须以“YES”或者“NO”开头，并说明原因。
如果该问题是心理学相关问题，回答必须以“YES”开头，否则，以“NO”开头。用中文作答！
比如：
Example #1

Question: 世界上最大的湖泊是什么？
Answer: NO，该问题是地理问题，并非心理学相关问题。

Example #2
Question: 什么是人脑发育的关键期和可塑性？
Answer: YES，该问题是心理学相关问题。
下面为正式问题：
Question: {question}
Answer:
"""
prompt_template = """评估一个分数"Score"来代表"Question"与心理学的的相关度。
--------
如何评分：
- Score值越大表示"Question"与心理学的的相关度越高。
- 0表示"Question"与心理学完全不相关。
- 100表示"Question"与心理学高度相关。
- 认真评分，这很重要。
--------

用中文作答并简要说明评分理由！
用下面格式回答：

Score: [分数]
Reason: [评分理由]
--------
Question: {question}
Answer:
"""
CLASSIFIER_PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["question"]
)

prompt_template = """基于<<<Context>>>中问答上下文，补全<<<Question>>>为一个完整的句子。
具体要求：
1. 永远不要试图回答<<<Question>>>。 即便它是一个疑问句。你的目标是确保<<<Question>>>的完整性。
2. 句子必须有明确的主谓宾。
3. 句子中的代词必须用合适的名词替换。
4. 不能改变句子原本的意思! 
5. 不能扩充句子的意思！


请按照下面格式回答：
Final Question: [最终的句子]
Reason: [判断的理由]

<<<Context>>>:
--------
{context}
--------
<<<Question>>>:{question}
"""

"""prompt_template = 评估<<<Question>>>是否为一个完整句子。如果是，不做任何改动，返回原始句子并说明理由。否则，结合<<<Context>>>描述的问答语境补全句子，返回补全后的句子并说明理由。

不能改变句子原本的意思! 
不能扩充句子的意思！
非常重要：务必将句子中的代词用合适的名词替换！

请按照下面格式回答：
Final Question: [最终的句子]
Reason: [判断的理由]

<<<Context>>>:
--------
{context}
--------
<<<Question>>>:{question}
"""

COMPLETE_PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context","question"],
)

