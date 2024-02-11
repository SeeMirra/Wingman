#Portions copyright langchain, ray project, and their respective holders. All other portions copyright 2024 Christian Mirra
import os
import sys
if len(sys.argv) > 1:
    print(f"Cloning {sys.argv[1]}!")
else:
    print("No Argument Detected! Usage: generate_embedding_github.py https://github.com/princeton-nlp/tree-of-thought-llm")
    exit()
import time
from typing import List
import git
import langchain
import numpy as np
import ray
import warnings

warnings.filterwarnings("ignore")
from pprint import pprint

#from langchain.text_splitter import Language
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain.document_loaders import ReadTheDocsLoader
from langchain.embeddings.base import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from sentence_transformers import SentenceTransformer

from local_embeddings import LocalHuggingFaceEmbeddings

# wget -e robots=off --recursive --no-clobber --page-requisites --html-extension \
# --convert-links --restrict-file-names=windows \
# --domains https://github.com --no-parent https://github.com/princeton-nlp/tree-of-thought-llm

git.Repo.clone_from(sys.argv[1], "./cloned")

FAISS_INDEX_PATH = "faiss_index_fast"
db_shards = 8
ray.init()



loader = GenericLoader.from_filesystem(
    "./cloned",
    glob="*",
    suffixes=[".py", ".js"],
    parser=LanguageParser(),
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=100,
    length_function=len,
)


@ray.remote(num_gpus=1)
def process_shard(shard):
    print(f"Starting process_shard of {len(shard)} chunks.")
    st = time.time()
    embeddings = LocalHuggingFaceEmbeddings("multi-qa-mpnet-base-dot-v1")
    et = time.time() - st
    print(f"Loading embeddings took {et} seconds.")
    st = time.time()
    result = FAISS.from_documents(shard, embeddings)
    et = time.time() - st
    print(f"Shard completed in {et} seconds.")
    return result


st = time.time()
print("Loading documents ...")
docs = loader.load()
chunks = text_splitter.create_documents(
    [doc.page_content for doc in docs], metadatas=[doc.metadata for doc in docs]
)
et = time.time() - st
print(f"Time taken: {et} seconds. {len(chunks)} chunks generated")

print(f"Loading chunks into vector store ... using {db_shards} shards")
st = time.time()
shards = np.array_split(chunks, db_shards)
futures = [process_shard.remote(shards[i]) for i in range(db_shards)]
results = ray.get(futures)
et = time.time() - st
print(f"Shard processing complete. Time taken: {et} seconds.")

st = time.time()
print("Merging shards ...")
db = results[0]
for i in range(1, db_shards):
    db.merge_from(results[i])
et = time.time() - st
print(f"Merged in {et} seconds.")

st = time.time()
print("Saving faiss index")
db.save_local(FAISS_INDEX_PATH)
et = time.time() - st
print(f"Saved in: {et} seconds.")
