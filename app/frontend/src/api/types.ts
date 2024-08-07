export type ApproachKey = "text" | "vec" | "hs" | "hssr";

export interface Approach {
    key: ApproachKey;
    title: string;
}

export interface TextSearchRequest {
    query: string;
    vectorSearch?: boolean;
    hybridSearch?: boolean;
    top?: number;
    k?: number;
    filter?: string;
    useSemanticRanker?: boolean;
    useSemanticCaptions?: boolean;
    queryVector?: number[];
    dataSet?: string;
}

export interface ImageSearchRequest {
    query: string;
    dataType: string;
}

export interface SearchResponse<T extends SearchResult> {
    results: T[];
    count: number;
}

interface SearchResult {
    "@search.score": number;
    "@search.reranker_score"?: number;
    "@search.captions"?: SearchCaptions[];
}

interface SearchCaptions {
    text: string;
    highlights: string;
}

export interface TextSearchResult1 extends SearchResult {
    id: string;
    title: string;
    titleVector: number[];
    content: string;
    contentVector: number[];
    category?: string;
    url?: string;
}

export interface TextSearchResult extends SearchResult {
    id: string;
    name: string;
    descriptionContent: string;
    projectOverviewContent: string;
    managingTeam: string;
}

export interface ImageSearchResult extends SearchResult {
    id: string;
    title: string;
    imageUrl: string;
}

export interface ResultCard {
    approachKey: string;
    searchResults: TextSearchResult[];
    resultCount: number;
}

export interface AxiosErrorResponseData {
    error: {
        code: string;
        message: string;
    };
}
