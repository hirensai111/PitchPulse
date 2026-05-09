import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { PredictResponse } from "@/types/api";
import { Home, MapPin, Calendar, TrendingUp, Target, Crosshair } from "lucide-react";

interface MatchMetaHeaderProps {
  meta: PredictResponse["meta"];
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

const STAT_META: Record<string, { icon: typeof TrendingUp; subtitle: string }> = {
  t1_form_win_rate: { icon: TrendingUp, subtitle: "(last 10 matches)" },
  t2_form_win_rate: { icon: TrendingUp, subtitle: "(last 10 matches)" },
  t1_home_win_rate: { icon: Home, subtitle: "(last 10 home games)" },
  venue_avg_first_innings_score: { icon: Target, subtitle: "(historical)" },
  venue_avg_total_sixes: { icon: Crosshair, subtitle: "(per match, historical)" },
  h2h_t1_win_rate: { icon: TrendingUp, subtitle: "(last 5 head-to-head)" },
};

export function MatchMetaHeader({ meta }: MatchMetaHeaderProps) {
  const stats = [
    {
      key: "t1_form_win_rate",
      label: "T1 Form",
      value: `${(meta.key_features.t1_form_win_rate * 100).toFixed(0)}%`,
    },
    {
      key: "t2_form_win_rate",
      label: "T2 Form",
      value: `${(meta.key_features.t2_form_win_rate * 100).toFixed(0)}%`,
    },
    {
      key: "t1_home_win_rate",
      label: "T1 Home Win Rate",
      value: `${(meta.key_features.t1_home_win_rate * 100).toFixed(0)}%`,
    },
    {
      key: "venue_avg_first_innings_score",
      label: "Venue Avg 1st Inns",
      value: `${meta.key_features.venue_avg_first_innings_score.toFixed(0)}`,
    },
    {
      key: "venue_avg_total_sixes",
      label: "Venue Avg Sixes",
      value: `${meta.key_features.venue_avg_total_sixes.toFixed(1)}`,
    },
    {
      key: "h2h_t1_win_rate",
      label: "H2H T1 Win Rate",
      value: `${(meta.key_features.h2h_t1_win_rate * 100).toFixed(0)}%`,
    },
  ];

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <CardTitle className="text-2xl">
              {meta.team1}{" "}
              <span className="text-slate-400 font-normal">vs</span>{" "}
              {meta.team2}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {meta.is_home_game_t1 && (
              <Badge variant="blue">
                <Home className="h-3 w-3 mr-1" />
                {meta.team1} home
              </Badge>
            )}
            {meta.is_home_game_t2 && (
              <Badge variant="blue">
                <Home className="h-3 w-3 mr-1" />
                {meta.team2} home
              </Badge>
            )}
            {meta.is_neutral_venue && (
              <Badge variant="gray">Neutral</Badge>
            )}
            <Badge variant="outline">
              <Calendar className="h-3 w-3 mr-1" />
              {formatDate(meta.match_date)}
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-sm text-slate-500 mt-1">
          <MapPin className="h-3.5 w-3.5" />
          {meta.venue}
        </div>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
          {stats.map((stat) => {
            const metaInfo = STAT_META[stat.key];
            return (
              <div
                key={stat.key}
                className="flex flex-col items-center text-center p-3 rounded-lg bg-slate-50"
              >
                <metaInfo.icon className="h-4 w-4 text-slate-400 mb-1" />
                <span className="text-lg font-semibold text-slate-900">
                  {stat.value}
                </span>
                <span className="text-xs text-slate-500">{stat.label}</span>
                <span className="text-[10px] text-slate-400 mt-0.5">
                  {metaInfo.subtitle}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
