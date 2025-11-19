import os
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from llama_index.core.chat_engine.types import BaseChatEngine
from llama_index.readers.file import MarkdownReader
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    load_index_from_storage,
    PromptTemplate,
)
from llama_index.llms.groq import Groq
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# Load environment variables
load_dotenv()

DATA_DIR = Path("./crawl_output/")
STORAGE_DIR = Path("./storage/")

Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")


def build_index(force_rebuild: bool = False):
    if STORAGE_DIR.exists() and not force_rebuild:
        print("Loading existing index from storage...")
        storage_context = StorageContext.from_defaults(persist_dir=str(STORAGE_DIR))
        return load_index_from_storage(storage_context)

    print("Building new index...")
    loader = MarkdownReader()
    md_files = list(DATA_DIR.glob("*.md"))

    if not md_files:
        raise FileNotFoundError(f"No markdown files found in {DATA_DIR.resolve()}")

    all_docs = []
    for f in md_files:
        docs = loader.load_data(file=str(f))
        all_docs.extend(docs)

    Settings.chunk_size = 512
    storage_context = StorageContext.from_defaults()
    index = VectorStoreIndex.from_documents(all_docs, storage_context=storage_context)
    storage_context.persist(persist_dir=str(STORAGE_DIR))
    print(f"Index built and saved to {STORAGE_DIR}")
    return index


def build_chat_engine(
    index, model="llama-3.1-8b-instant", token_limit=1500
) -> BaseChatEngine:
    memory = ChatMemoryBuffer.from_defaults(token_limit=token_limit)

    chat_engine = index.as_chat_engine(
        llm=Groq(model=model, api_key=os.getenv("GROQ_API_KEY")),
        similarity_top_k=5,
        memory=memory,
        chat_mode="context",
        system_prompt="""
            You are an expert on the Cornell Sustainability Office (CSO).

            Strictly using your given context regarding the CSO, answer the question clearly.
            NEVER guess or infer information, i.e. be upfront if you cannot answer a question. 
            All information must come from the provided context.

            If the user greets you, simply greet them back and briefly introduce yourself.

            AVOID saying the word 'context' in your responses. Make it appear as if 
            the information from the provided context is inherently part of your knowledge base. 
        """,
    )

    return chat_engine


def do_chat_repl(chat_engine: BaseChatEngine):
    print(
        """=====  BEFORE YOU BEGIN CHATTING... =====
Regarding AI energy usage, there is often a focus on the energy used in model 
training. Today, however, inference - not training - represents an increasing 
majority of AI energy demands, with estimates suggesting 80 to 90 percent of 
computing power for AI is used for inference. 

With every query, an AI chatbot consumes a certain amount of electricity, water, 
and carbon. Model size plays a massive role with respect to this energy consumption! 
Thus, our chatbot intentionally uses a smaller, energy-efficient model (LLaMA 3.1 8B), 
where each query is approximately equivalent to running a microwave for a tenth 
of a second.

While using a lightweight model can reduce the environmental footprint of our 
chatbot, and the impact of a single query appears low, it is still important 
to see the bigger picture on the environmental cost that AI carries. 
          
For more information, visit the following link: <insert link>
========================================="""
    )
    print("(Type 'exit' or 'quit' to close chat.)\n")
    count = 0
    energy_use = 0
    while True:
        query = input("User: ").strip()
        if query.lower() in {"exit", "quit"}:
            break

        try:
            print("Processing...")
            response = query_engine.chat(query)
            print(f"Agent: {response}\n")

            count = count + 1
            energy_use = energy_use + 0.1
            if count == 1:
                print(
                    f"Note: You have made {count} query, equivalent to microwaving food for {energy_use} seconds.\n"
                )
            else:
                print(
                    f"Note: You have made {count} queries, equivalent to microwaving food for {energy_use} seconds.\n"
                )
        except Exception as e:
            print(f"Error: {e}\n")


async def main():
    print("Loading index...")
    index = build_index()

    chat_engine = build_chat_engine(index)

    do_chat_repl(chat_engine)


if __name__ == "__main__":
    asyncio.run(main())
