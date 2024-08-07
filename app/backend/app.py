import os
import time
import logging
import gzip
import openai
from io import BytesIO
from quart import Quart, request, jsonify, Blueprint, current_app
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient

from searchText import SearchText

CONFIG_OPENAI_TOKEN = "openai_token"
CONFIG_CREDENTIAL = "azure_credential"
CONFIG_EMBEDDING_DEPLOYMENT = "embedding_deployment"
CONFIG_SEARCH_INVESTMENT_INDEX_V_PREV = "search_investment"
CONFIG_SEARCH_INVESTMENT_INDEX_V_CURR = "search_investment"
CONFIG_SEARCH_ORGANIZATION_INDEX_V_PREV = "search_organization"
CONFIG_SEARCH_ORGANIZATION_INDEX_V_CURR = "search_organization"

dataSetConfigDict = {
     "investment-20240611-2": CONFIG_SEARCH_INVESTMENT_INDEX_V_PREV,
     "investment-20240726": CONFIG_SEARCH_INVESTMENT_INDEX_V_CURR,
     "organization-20240611": CONFIG_SEARCH_ORGANIZATION_INDEX_V_PREV,
     "organization-20240726": CONFIG_SEARCH_ORGANIZATION_INDEX_V_CURR,
}

bp = Blueprint("routes", __name__, static_folder="static")


@bp.route("/", defaults={"path": "index.html"})
@bp.route("/<path:path>")
async def static_file(path):
    return await bp.send_static_file(path)


@bp.route("/embedQuery", methods=["POST"])
async def embed_query():
    try:
        request_json = await request.get_json()
        query = request_json["query"]
        response = await openai.Embedding.acreate(
            input=query, engine=current_app.config[CONFIG_EMBEDDING_DEPLOYMENT]
        )
        return response["data"][0]["embedding"], 200
    except Exception as e:
        logging.exception("Exception in /embedQuery")
        return jsonify({"error": str(e)}), 500


@bp.route("/searchText", methods=["POST"])
async def search_text():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 400
    try:
        request_json = await request.get_json()
        vector_search = (
            request_json["vectorSearch"] if request_json.get("vectorSearch") else False
        )

        hybrid_search = (
            request_json["hybridSearch"] if request_json.get("hybridSearch") else False
        )

        select = request_json["select"] if request_json.get("select") else None
        
        k = request_json["k"] if request_json.get("k") else 10
        
        filter = request_json["filter"] if request_json.get("filter") else None
        
        use_semantic_ranker = (
            request_json["useSemanticRanker"]
            if request_json.get("useSemanticRanker")
            else False
        )
        
        use_semantic_captions = (
            request_json["useSemanticCaptions"]
            if request_json.get("useSemanticCaptions")
            else False
        )
        
        query_vector = (
            request_json["queryVector"] if request_json.get("queryVector") else None
        )

        data_set = request_json["dataSet"] if request_json.get("dataSet") else "investment-20240726"
        indexConfig = dataSetConfigDict[data_set]

        r = await current_app.config[indexConfig].search(
            query=request_json["query"],
            use_vector_search=vector_search,
            use_hybrid_search=hybrid_search,
            use_semantic_ranker=use_semantic_ranker,
            use_semantic_captions=use_semantic_captions,
            select=select,
            k=k,
            filter=filter,
            query_vector=query_vector,
            data_set=data_set,
        )
        return jsonify(r), 200
    except Exception as e:
        logging.exception("Exception in /searchText")
        return jsonify({"error": str(e)}), 500

@bp.before_request
async def ensure_openai_token():
    openai_token = current_app.config[CONFIG_OPENAI_TOKEN]
    if openai_token.expires_on < time.time() + 60:
        openai_token = await current_app.config[CONFIG_CREDENTIAL].get_token(
            "https://cognitiveservices.azure.com/.default"
        )
        current_app.config[CONFIG_OPENAI_TOKEN] = openai_token
        openai.api_key = openai_token.token


@bp.after_request
async def gzip_response(response):
    accept_encoding = request.headers.get("Accept-Encoding", "")
    if (
        response.status_code < 200
        or response.status_code >= 300
        or len(await response.get_data()) < 500
        or "gzip" not in accept_encoding.lower()
    ):
        return response

    gzip_buffer = BytesIO()
    gzip_file = gzip.GzipFile(mode="wb", compresslevel=6, fileobj=gzip_buffer)
    gzip_file.write(await response.get_data())
    gzip_file.close()
    response.set_data(gzip_buffer.getvalue())
    response.headers["Content-Encoding"] = "gzip"
    response.headers["Content-Length"] = len(await response.get_data())

    return response


@bp.before_app_serving
async def setup_clients():
    # Replace these with your own values, either in environment variables or directly here
    AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
    AZURE_OPENAI_DEPLOYMENT_NAME = (
        os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "embedding"
    )
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    AZURE_SEARCH_SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
    AZURE_SEARCH_INVESTMENT_INDEX_NAME_PREV = os.getenv("AZURE_SEARCH_INVESTMENT_INDEX_NAME_PREV")
    AZURE_SEARCH_INVESTMENT_INDEX_NAME_CURR = os.getenv("AZURE_SEARCH_INVESTMENT_INDEX_NAME_CURR")
    AZURE_SEARCH_ORGANIZATION_INDEX_NAME_PREV = os.getenv("AZURE_SEARCH_ORGANIZATION_INDEX_NAME_PREV")
    AZURE_SEARCH_ORGANIZATION_INDEX_NAME_CURR = os.getenv("AZURE_SEARCH_ORGANIZATION_INDEX_NAME_CURR")
    
    azure_credential = DefaultAzureCredential(
        exclude_shared_token_cache_credential=True
    )

    # Used by the OpenAI SDK
    openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
    openai.api_version = AZURE_OPENAI_API_VERSION
    openai.api_type = "azure_ad"
    openai_token = await azure_credential.get_token(
        "https://cognitiveservices.azure.com/.default"
    )
    openai.api_key = openai_token.token

    # Set up clients for Cognitive Search
    search_client_investment_prev = SearchClient(
        endpoint=AZURE_SEARCH_SERVICE_ENDPOINT,
        index_name=AZURE_SEARCH_INVESTMENT_INDEX_NAME_PREV,
        credential=azure_credential,
    )
    search_client_investment_curr = SearchClient(
        endpoint=AZURE_SEARCH_SERVICE_ENDPOINT,
        index_name=AZURE_SEARCH_INVESTMENT_INDEX_NAME_CURR,
        credential=azure_credential,
    )
    search_client_organization_prev = SearchClient(
        endpoint=AZURE_SEARCH_SERVICE_ENDPOINT,
        index_name=AZURE_SEARCH_ORGANIZATION_INDEX_NAME_PREV,
        credential=azure_credential,
    )
    search_client_organization_curr = SearchClient(
        endpoint=AZURE_SEARCH_SERVICE_ENDPOINT,
        index_name=AZURE_SEARCH_ORGANIZATION_INDEX_NAME_CURR,
        credential=azure_credential,
    )

    # Store on app.config for later use inside requests
    current_app.config[CONFIG_OPENAI_TOKEN] = openai_token
    current_app.config[CONFIG_CREDENTIAL] = azure_credential
    current_app.config[CONFIG_EMBEDDING_DEPLOYMENT] = AZURE_OPENAI_DEPLOYMENT_NAME
    current_app.config[CONFIG_SEARCH_INVESTMENT_INDEX_V_PREV] = SearchText(search_client_investment_prev)
    current_app.config[CONFIG_SEARCH_INVESTMENT_INDEX_V_CURR] = SearchText(search_client_investment_curr)
    current_app.config[CONFIG_SEARCH_ORGANIZATION_INDEX_V_PREV] = SearchText(search_client_organization_prev)
    current_app.config[CONFIG_SEARCH_ORGANIZATION_INDEX_V_CURR] = SearchText(search_client_organization_curr)
    
def create_app():
    app = Quart(__name__)
    app.register_blueprint(bp)
    return app
