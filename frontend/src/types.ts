export interface ReasoningTrace {
    title: string;
    reasoning: string;
}

export interface CitySummary {
    id?: string;
    lat: number;
    lon: number;
    location: string;
    weight: number;
    title?: string;
    summary: string;
    sentiment: 'positive' | 'neutral' | 'negative' | 'mixed';
    key_events: string[];
    key_events_html?: string;
    reasoning?: ReasoningTrace[];
    items_count?: number;
}
