
let API_BASE = '';

/**
 * Call this in your app's entry point (main.tsx) to configure the API base URL.
 * Example: configureApi(import.meta.env.VITE_API_BASE);
 */
export function configureApi(baseUrl: string) {
    API_BASE = baseUrl;
}

export interface SearchResult {
    ids: string[][];
    distances: number[][];
    metadatas: any[][];
    documents: string[][];
}

export interface ReportResult {
    ids: string[];
    embeddings: number[][];
    metadatas: any[];
    documents: string[];
}

export const api = {
    async search(query: string, nResults = 10): Promise<SearchResult> {
        const res = await fetch(`${API_BASE}/chroma/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, nResults }),
        });
        if (!res.ok) throw new Error('Search failed');
        return res.json() as SearchResult;
    },

    async getReport(id: string): Promise<ReportResult> {
        const res = await fetch(`${API_BASE}/report/${id}`);
        if (!res.ok) throw new Error('Get report failed');
        return res.json() as ReportResult;
    },

    getPdfUrl(id: string): string {
        return `${API_BASE}/pdf/${id}`;
    }
};
