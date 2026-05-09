export interface Venue {
  venue: string;
  home_teams: string[];
  is_neutral: boolean;
  matches_in_dataset: number;
}

export interface Prediction {
  event_id: string;
  display_name: string;
  category: string;
  scope: "match" | "team";
  team: string | null;
  probability: number;
  base_rate: number;
  lift: number;
  notability_score: number;
}

export interface PredictResponse {
  meta: {
    team1: string;
    team2: string;
    venue: string;
    match_date: string;
    is_home_game_t1: boolean;
    is_home_game_t2: boolean;
    is_neutral_venue: boolean;
    key_features: {
      t1_form_win_rate: number;
      t2_form_win_rate: number;
      t1_home_win_rate: number;
      venue_avg_first_innings_score: number;
      venue_avg_total_sixes: number;
      h2h_t1_win_rate: number;
    };
  };
  all_predictions: Prediction[];
  top_5_likely: Prediction[];
  top_5_notable: Prediction[];
}

export interface TrackRecordMatch {
  match_id: string;
  date: string;
  team1: string;
  team2: string;
  venue: string;
  result: string;
  notes?: string;
  top_5_likely: {
    event_id: string;
    display_name: string;
    team?: string;
    probability: number;
    actual: boolean | null;
  }[];
  top_5_notable: {
    event_id: string;
    display_name: string;
    team?: string;
    probability: number;
    actual: boolean | null;
  }[];
  likely_hits: number | null;
  notable_hits: number | null;
}

export interface TrackRecordResponse {
  matches: TrackRecordMatch[];
  summary: {
    total_matches: number;
    avg_likely_hits: number | null;
    avg_notable_hits: number | null;
    likely_precision_at_5: number | null;
    notable_precision_at_5: number | null;
    aggregate_likely_p5: number | null;
    aggregate_notable_p5: number | null;
    note: string;
  };
}

export interface EventImportanceResponse {
  event_id: string;
  display_name: string;
  features: {
    feature: string;
    importance: number;
  }[];
}

export interface ModelCardResponse {
  content: string;
}
