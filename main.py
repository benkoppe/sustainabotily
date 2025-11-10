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
from llama_index.llms.openai import OpenAI

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
    index = await build_index()
    print(index)


if __name__ == "__main__":
    asyncio.run(main())
