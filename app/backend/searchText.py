from typing import Any
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType, VectorQuery, VectorizedQuery


class SearchText:
    def __init__(self, search_client: SearchClient):
        self.search_client = search_client

    async def search(
        self,
        query: str,
        use_vector_search: bool = False,
        use_hybrid_search: bool = False,
        use_semantic_ranker: bool = False,
        use_semantic_captions: bool = False,
        select: str | None = None,
        k: int | None = None,
        filter: str | None = None,
        query_vector: list[float] | None = None,
        data_set: str = "investment-20240726"
    ):
        # Vectorize query
        query_vector = query_vector if use_vector_search else None
        vector_fields = "AnalysisAndRecommendationVector,DescriptionVector,ProjectOverviewVector,StrategicFitVector" if use_vector_search and "investment" in data_set else None
        k_vector = k if use_vector_search else None

        # Set text query for no-vector, semantic and 'Hybrid' searches
        query_text = (
            query
            if not use_vector_search or use_hybrid_search or use_semantic_ranker
            else None
        )

        # Semantic ranker options
        query_type = QueryType.SEMANTIC if use_semantic_ranker else None
        query_language = "en-us" if use_semantic_ranker else None
        semantic_configuration_name = (
            "default" if use_semantic_ranker else None
        )

        # Semantic caption options
        query_caption = QueryCaptionType.EXTRACTIVE if use_semantic_captions else None
        query_answer = QueryAnswerType.EXTRACTIVE if use_semantic_captions else None
        highlight_pre_tag = "<b>" if use_semantic_captions else None
        highlight_post_tag = "</b>" if use_semantic_captions else None

        vector_queries = [VectorizedQuery(vector=query_vector, k_nearest_neighbors=k_vector, fields=vector_fields)] if use_vector_search else None
        # AZS search query


        search_results = await self.search_client.search(
            query_text,
            vector_queries=vector_queries,
            top=10,
            include_total_count=True,
            select=select,
            filter=filter,
            query_type=query_type,
            query_language=query_language,
            semantic_configuration_name=semantic_configuration_name,
            query_caption=query_caption,
            query_answer=query_answer,
            highlight_pre_tag=highlight_pre_tag,
            highlight_post_tag=highlight_post_tag,
        )

        count = await search_results.get_count()
        
        results = []
        async for r in search_results:
            
            captions = (
                list(
                    map(
                        lambda c: {"text": c.text, "highlights": c.highlights},
                        r["@search.captions"],
                    )
                )
                if r["@search.captions"]
                else None
            )

            if "investment" in data_set:

                managingTeamsArr =  [r["ManagingTeamL1"], r["ManagingTeamL2"], r["ManagingTeamL3"], r["ManagingTeamL4"]]
                filteredArr = [i for i in managingTeamsArr if i is not None]
                managingTeam1 = '/'.join(filteredArr)
                results.append(
                    {
                        "@search.score": r["@search.score"],
                        "@search.reranker_score": r["@search.reranker_score"],
                        "@search.captions": captions,
                        "id": r["InvestmentId"], 
                        "name": r["Name"],
                        "descriptionContent": r["Description"],
                        "projectOverviewContent": r["ProjectOverview"],
                        "managingTeam": managingTeam1
                    }
                )

## CLM this to change
            elif "organization" in data_set:
                results.append(
                    {
                        "@search.score": r["@search.score"],
                        "@search.reranker_score": r["@search.reranker_score"],
                        "@search.captions": captions,
                        "vector_id": r["vector_id"],
                        "id": r["id"],
                        "title": r["title"],
                        "content": r["text"],
                        "url": r["url"],
                        "titleVector": r["titleVector"],
                        "contentVector": r["contentVector"],
                    }
                )

        return {
            "results": results,
            "count": count
        }
