import { useState } from "react";
import { useTrackRecord } from "@/api/queries";
import { MatchResultCard } from "@/components/MatchResultCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowUpDown } from "lucide-react";
// TrackRecordMatch type used implicitly via MatchResultCard props

type SortMode = "date-desc" | "notable-hits";

export function TrackRecordPage() {
  const { data, isLoading, error } = useTrackRecord();
  const [sortMode, setSortMode] = useState<SortMode>("date-desc");

  const sortedMatches = (() => {
    if (!data) return [];
    const matches = [...data.matches];
    if (sortMode === "date-desc") {
      return matches.sort((a, b) => b.date.localeCompare(a.date));
    }
    if (sortMode === "notable-hits") {
      return matches.sort((a, b) => (b.notable_hits ?? 0) - (a.notable_hits ?? 0));
    }
    return matches;
  })();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-32 w-full" />
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-rose-600">Failed to load track record data.</div>
      </div>
    );
  }

  const summary = data.summary;
  const hasResults = summary.likely_precision_at_5 !== null;

  const liveLikely = hasResults
    ? Math.round(summary.likely_precision_at_5! * 100)
    : 0;
  const liveNotable = hasResults
    ? Math.round(summary.notable_precision_at_5! * 100)
    : 0;
  const aggLikely = summary.aggregate_likely_p5
    ? Math.round(summary.aggregate_likely_p5 * 100)
    : 77;
  const aggNotable = summary.aggregate_notable_p5
    ? Math.round(summary.aggregate_notable_p5 * 100)
    : 70;

  const likelyBadge =
    liveLikely >= aggLikely
      ? "green"
      : liveLikely >= aggLikely - 10
      ? "secondary"
      : "destructive";
  const notableBadge =
    liveNotable >= aggNotable
      ? "green"
      : liveNotable >= aggNotable - 10
      ? "secondary"
      : "destructive";

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="text-center space-y-1">
          <h1 className="text-3xl font-bold text-slate-900">
            Live Forward Test Results
          </h1>
          <p className="text-sm text-slate-500">
            Predictions made before each match, graded against actual outcomes
          </p>
        </div>

        {/* Summary card */}
        <Card>
          <CardHeader>
            <CardTitle>Aggregate Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <div className="text-2xl font-bold text-slate-900">
                  {summary.total_matches}
                </div>
                <div className="text-xs text-slate-500">Matches tested</div>
              </div>
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <div className="text-2xl font-bold text-slate-900">
                  {liveLikely}%
                </div>
                <div className="text-xs text-slate-500">Likely P@5 (live)</div>
                <Badge variant={likelyBadge as any} className="mt-1 text-xs">
                  {liveLikely >= aggLikely ? "≥ aggregate" : "vs " + aggLikely + "%"}
                </Badge>
              </div>
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <div className="text-2xl font-bold text-slate-900">
                  {liveNotable}%
                </div>
                <div className="text-xs text-slate-500">Notable P@5 (live)</div>
                <Badge variant={notableBadge as any} className="mt-1 text-xs">
                  {liveNotable >= aggNotable - 10 && liveNotable < aggNotable
                    ? "within 10pp"
                    : liveNotable >= aggNotable
                    ? "≥ aggregate"
                    : "below"}
                </Badge>
              </div>
              <div className="text-center p-3 bg-slate-50 rounded-lg">
                <div className="text-2xl font-bold text-slate-900">
                  {aggLikely}% / {aggNotable}%
                </div>
                <div className="text-xs text-slate-500">Expected (165-match)</div>
              </div>
            </div>
            {hasResults && (
              <p className="mt-4 text-xs text-slate-500 text-center">
                Likely: {(summary.likely_precision_at_5! * 100).toFixed(0)}% ·
                Notable: {(summary.notable_precision_at_5! * 100).toFixed(0)}%
              </p>
            )}
            {!hasResults && (
              <p className="mt-4 text-xs text-amber-600 text-center bg-amber-50 rounded-md py-2">
                Live results pending. Matches are graded as they conclude.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Sort controls */}
        <div className="flex justify-end">
          <button
            onClick={() =>
              setSortMode((m) =>
                m === "date-desc" ? "notable-hits" : "date-desc"
              )
            }
            className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-md px-3 py-1.5 transition-colors"
          >
            <ArrowUpDown className="h-3.5 w-3.5" />
            {sortMode === "date-desc"
              ? "By date (newest first)"
              : "By notable hit rate"}
          </button>
        </div>

        {/* Match cards */}
        <div className="space-y-4">
          {sortedMatches.map((match) => (
            <MatchResultCard key={match.match_id} match={match} />
          ))}
        </div>
      </div>
    </div>
  );
}
