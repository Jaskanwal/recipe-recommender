"""Index the recipies and save them in the vector database."""
import glob
import json
import os

import click
import numpy as np
import torch
from dotenv import load_dotenv
from langchain import text_splitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from sentence_transformers import SentenceTransformer

from src.common.logger import get_logger
from src.common.utils import load_yaml

# load all the environment variables
load_dotenv()
# Load all the modeling parameters
params = load_yaml("params.yaml")

# Relevant keys from the recipe.json file to build document content
CONTENT_KEYS = ["name", "description", "ingredients", "cusine", "diet", "difficulty", "total_time"]
# Indicator to normalize the document vector embeddings
NORMALIZE_EMBEDDINGS = True
# Url for the Qdrant db
DB_URL = "http://localhost:6333"
# Initialize logger
LOGGER = get_logger(__file__)
# Number of documents read and processed together
DOC_CHUNK_SIZE = 200


def get_document_from_json(json_file_path: str, dataset_name: str) -> Document:
    """Read recipe as a json file and output langchain document with relevant content and meta-data.

    Args:
        json_file_path (str): path to the json file with recipe details
        dataset_name (str): Name of the dataset

    Returns:
        Document: langchain document with relevant content and meta-data
    """
    with open(json_file_path, "r") as file:
        data = json.load(file)
    content = "; \n".join([f"{key}: {value}" for key, value in data.items() if key in CONTENT_KEYS and len(value) > 0])
    content = Document(page_content=content, metadata={"recipe_id": data["recipe_id"], "dataset_name": dataset_name})
    return content


def load_documents_to_db(
    embeddings_model: HuggingFaceEmbeddings, contents: list[Document], retriver_db_name: str, splitter: text_splitter
) -> None:
    """Load document embeddings into a retrieval database using a given HuggingFace embeddings model.

    Args:
        embeddings_model (HuggingFaceEmbeddings): The Hugging Face embeddings model used for encoding document contents.
        contents (list[Document]): List of Document objects containing textual content to be indexed.
        retriver_db_name (str): Name of the retrieval database where the document embeddings will be stored.
        splitter (text_splitter): An instance of a text splitter used to divide the documents into chunks.
    """
    # Split the documents into chunks for deriving the chunk embeddings
    documents = splitter.split_documents(contents)
    # Load the chunks into the vector db
    _ = Qdrant.from_documents(
        documents, embeddings_model, url=DB_URL, prefer_grpc=False, collection_name=retriver_db_name
    )


def get_embedding_model(embedding_model_name: str) -> HuggingFaceEmbeddings:
    """Instantiate and return a HuggingFaceEmbeddings model for a given embedding model name.

    Args:
        embedding_model_name (str): The name or identifier of the Hugging Face embedding model.

    Returns:
        HuggingFaceEmbeddings: An instance of the HuggingFaceEmbeddings class configured with the specified model.
    """
    # Download model from huggingface and save model parameters locally
    model_path = os.path.join(os.getenv("DATA_ROOT"), "embedding_models", embedding_model_name)
    if not os.path.exists(model_path):
        os.makedirs(model_path)
        model = SentenceTransformer(embedding_model_name)
        model.save(model_path)

    embeddings_model = HuggingFaceEmbeddings(
        model_name=model_path,
        model_kwargs={"device": torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")},
        encode_kwargs={"normalize_embeddings": NORMALIZE_EMBEDDINGS},
    )
    return embeddings_model


def get_documents_chunk(dataset_files: list[str], dataset_name: str) -> tuple[int, list[Document]]:
    """Generate chunks of documents from a list of dataset files.

    Args:
        dataset_files (list[str]): List of file paths containing dataset documents in JSON format.
        dataset_name (str): Name or identifier for the dataset to add in the document meta data.

    Yields:
        tuple[int, list[Document]]: Chunk index and a list of Document objects extracted from each chunk of dataset
            files.
    """
    dataset_files_chunks = np.split(dataset_files, range(DOC_CHUNK_SIZE, len(dataset_files), DOC_CHUNK_SIZE))
    for idx, chunk in enumerate(dataset_files_chunks):
        chunk_content = [get_document_from_json(json_file_path=file, dataset_name=dataset_name) for file in chunk]
        yield idx, chunk_content


def load_dataset(
    dataset_name: str, embedding_model: HuggingFaceEmbeddings, splitter: text_splitter, retriver_db_name: str
) -> None:
    """Load a dataset into a retrieval database using the specified HuggingFace embeddings model.

    Args:
        dataset_name (str): Name or identifier for the dataset.
        embedding_model (HuggingFaceEmbeddings): The Hugging Face embeddings model used for encoding document contents.
        splitter (text_splitter): An instance of a text splitter used to divide the documents into chunks.
        retriver_db_name (str): Name of the retrieval database where the document embeddings will be stored.
    """
    LOGGER.info("Starting to load a dataset", dataset_name=dataset_name)
    dataset_files = glob.glob(os.path.join(os.getenv("SCRAPED_DATA_ROOT"), dataset_name, "recipes", "*.json"))
    for idx, chunk_content in get_documents_chunk(dataset_files=dataset_files, dataset_name=dataset_name):
        load_documents_to_db(
            embeddings_model=embedding_model,
            contents=chunk_content,
            retriver_db_name=retriver_db_name,
            splitter=splitter,
        )
        LOGGER.info("Completed loading a chunk", dataset_name=dataset_name, chunk=idx)


@click.command()
@click.option(
    "--scraped_datasets",
    default=params["scraped_datasets"],
    show_default=True,
    multiple=True,
    type=str,
    help="Names of the scraped datasets used to index in the retriver",
)
@click.option(
    "--embedding_model_name",
    default=params["embedding_model"]["model_name"],
    show_default=True,
    type=str,
    help="Model tag of hugging face model to get sentence embeddings",
)
@click.option(
    "--retriver_db_name",
    default=params["embedding_model"]["retriver_db_name"],
    show_default=True,
    type=str,
    help="Collections name for the embeddings db",
)
@click.option(
    "--chunk_size",
    default=params["embedding_model"]["chunk_size"],
    show_default=True,
    type=int,
    help="Number of characters in a single document chunk. Pick a suitable now so that each chunk is less than "
    "max_seq_length of the chosen model",
)
@click.option(
    "--chunk_overlap",
    default=params["embedding_model"]["chunk_overlap"],
    show_default=True,
    type=int,
    help="Number of characters overlap between consecutive chunks",
)
def retriver_entrypoint(
    scraped_datasets: list[str],
    embedding_model_name: str,
    retriver_db_name: str,
    chunk_size: int,
    chunk_overlap: int,
):
    """Entrypoint to initialize the retriver.

    Args:
        scraped_datasets (list[str]): Names of the scraped datasets used to index in the retriver
        embedding_model_name (str): Model tag of hugging face model to get sentence embeddings
        retriver_db_name (str): Collections name for the embeddings db
        chunk_size (int): Number of characters in a single document chunk
        chunk_overlap (int): Number of characters overlap between consecutive chunks
    """
    embedding_model = get_embedding_model(embedding_model_name)
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # Make sure the chunk size is not super large in comparison to max sequence length for the model
    try:
        max_seq_length = embedding_model.client.max_seq_length
        if chunk_size > 3 * max_seq_length:
            LOGGER.warning(
                f"Number of characters in chunk_size={chunk_size} is significantly higher than "
                f"max_seq_length={max_seq_length} supported by {embedding_model_name}. Please verify."
            )

    except Exception:
        LOGGER.info("Comparison between chunk size and max seq length supported by the model could not performed")

    for dataset_name in scraped_datasets:
        load_dataset(
            dataset_name=dataset_name,
            embedding_model=embedding_model,
            splitter=splitter,
            retriver_db_name=retriver_db_name,
        )


if __name__ == "__main__":
    # Call the Click command to execute the script
    retriver_entrypoint()
