import os
from pathlib import Path
import asyncio
from llama_index.readers.file import MarkdownReader
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    load_index_from_storage,
)
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openrouter import OpenRouter

DATA_DIR = Path("./crawl_output/")
STORAGE_DIR = Path("./storage/")


async def build_index(force_rebuild: bool = False):
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
    print(f"Index build and saved to {STORAGE_DIR}")
    return index


async def main():
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") or input(
        "Enter your OpenAI API Key: "
    )
    os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY") or input(
        "Enter your OpenRouter API Key: "
    )

    index = await build_index()

    query_engine_tool = QueryEngineTool(
        query_engine=index.as_query_engine(),
        metadata=ToolMetadata(
            name="sustainability_markdown_query_engine",
            description="Answer questions about Cornell Sustainability using this comprehensive markdown files directory",
        ),
    )

    agent = FunctionAgent(
        tools=[query_engine_tool], llm=OpenRouter(model="minimax/minimax-m2:free")
    )

    print("\nChatbot ready. Type 'exit' to quit.\n")
    while True:
        query = input("User: ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        response = await agent.run(query)
        print("Agent:", response, "\n")


if __name__ == "__main__":
    asyncio.run(main())
