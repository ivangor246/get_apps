export interface AppliedFilters {
  min_downloads: number | null;
  max_downloads: number | null;
  min_rating: number | null;
  categories_any: string[];
  above_median_downloads: boolean;
}

export interface SourceApp {
  app_id: string;
  name: string | null;
  url: string;
  rating: number | null;
  downloads: number | null;
  categories: string[];
  distance: number;
}

export interface RAGResponse {
  answer: string;
  filters: AppliedFilters;
  sources: SourceApp[];
  intent: string;
  language: string;
  iterations: number;
}

export interface RAGQueryPayload {
  db_name: string;
  query: string;
}
