import { Check, X, Clock } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { TrackRecordMatch } from "@/types/api";

interface MatchResultCardProps {
  match: TrackRecordMatch;
}

function PredictionRow({
  item,
  index,
}: {
  item: TrackRecordMatch["top_5_likely"][0];
  index: number;
}) {
  const statusIcon =
    item.actual === true ? (
      <Check className="h-4 w-4 text-emerald-600" />
    ) : item.actual === false ? (
      <X className="h-4 w-4 text-rose-500" />
    ) : (
      <Clock className="h-4 w-4 text-slate-400" />
    );

  return (
    <div className="flex items-center gap-2 py-1.5">
      <span className="text-xs font-bold text-slate-400 w-4">{index + 1}</span>
      <span className="text-sm text-slate-700 flex-1 truncate">
        {item.display_name}
      </span>
      {item.team && (
        <Badge variant="outline" className="text-xs flex-shrink-0">
          for {item.team}
        </Badge>
      )}
      <span className="text-sm font-medium text-slate-900 w-12 text-right">
        {(item.probability * 100).toFixed(0)}%
      </span>
      <span className="w-5 flex justify-center">{statusIcon}</span>
    </div>
  );
}

export function MatchResultCard({ match }: MatchResultCardProps) {
  const likelyHits = match.likely_hits ?? 0;
  const notableHits = match.notable_hits ?? 0;
  const isPending = match.result === "TBD";

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              {match.team1}{" "}
              <span className="text-slate-400 font-normal">vs</span>{" "}
              {match.team2}
            </h3>
            <p className="text-sm text-slate-500">
              {match.venue} — {match.date}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isPending ? (
              <Badge variant="gray">Result pending</Badge>
            ) : (
              <Badge variant="outline">{match.result}</Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Likely column */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <h4 className="font-semibold text-slate-900">Most Likely</h4>
              <span className="text-xs text-slate-500">
                ({likelyHits}/5 hits)
              </span>
            </div>
            <div className="space-y-0.5">
              {match.top_5_likely.map((item, i) => (
                <PredictionRow key={item.event_id + (item.team ?? "")} item={item} index={i} />
              ))}
            </div>
          </div>

          {/* Notable column */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <h4 className="font-semibold text-slate-900">Most Notable</h4>
              <span className="text-xs text-slate-500">
                ({notableHits}/5 hits)
              </span>
            </div>
            <div className="space-y-0.5">
              {match.top_5_notable.map((item, i) => (
                <PredictionRow key={item.event_id + (item.team ?? "")} item={item} index={i} />
              ))}
            </div>
          </div>
        </div>

        {match.notes && (
          <div className="mt-3 text-xs text-amber-700 bg-amber-50 rounded-md px-3 py-2">
            {match.notes}
          </div>
        )}
        <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500">
          Likely hit rate: {match.likely_hits !== null ? `${(likelyHits / 5 * 100).toFixed(0)}%` : "Pending"}
          {" · "}
          Notable hit rate: {match.notable_hits !== null ? `${(notableHits / 5 * 100).toFixed(0)}%` : "Pending"}
        </div>
      </CardContent>
    </Card>
  );
}
