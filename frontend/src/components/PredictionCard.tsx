import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExplainPopover } from "./ExplainPopover";
import type { Prediction } from "@/types/api";

interface PredictionCardProps {
  prediction: Prediction;
  index: number;
  variant: "likely" | "notable";
}

export function PredictionCard({ prediction, index, variant }: PredictionCardProps) {
  const probPercent = (prediction.probability * 100).toFixed(1);
  const basePercent = (prediction.base_rate * 100).toFixed(0);
  const lift = prediction.lift.toFixed(2);

  const barColor = variant === "likely" ? "bg-blue-500" : "bg-violet-500";
  const barBg = variant === "likely" ? "bg-blue-100" : "bg-violet-100";
  const numColor = variant === "likely" ? "text-blue-600" : "text-violet-600";

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Rank number */}
          <div
            className={`flex-shrink-0 w-7 h-7 rounded-full ${barBg} flex items-center justify-center text-sm font-bold ${numColor}`}
          >
            {index + 1}
          </div>

          <div className="flex-1 min-w-0">
            {/* Title row */}
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-sm font-medium text-slate-900 leading-tight">
                {prediction.display_name}
              </h4>
              <ExplainPopover prediction={prediction} />
            </div>
            {prediction.scope === "team" && prediction.team && (
              <Badge variant={variant === "likely" ? "blue" : "purple"} className="text-xs mt-1">
                for {prediction.team}
              </Badge>
            )}

            {/* Probability bar */}
            <div className="mt-3">
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xl font-bold ${numColor}`}>
                  {probPercent}%
                </span>
                <span className="text-xs text-slate-500">
                  base: {basePercent}% | lift: {lift}x
                </span>
              </div>
              <div className={`h-2 w-full rounded-full ${barBg}`}>
                <div
                  className={`h-full rounded-full ${barColor} transition-all duration-500`}
                  style={{ width: `${Math.min(prediction.probability * 100, 100)}%` }}
                />
              </div>
            </div>

            {/* Notable list: lift badge instead of raw score */}
            {variant === "notable" && (
              <div className="mt-2 flex justify-end gap-2">
                {prediction.lift > 2.0 && (
                  <Badge variant="purple" className="text-xs">
                    very unusual
                  </Badge>
                )}
                {prediction.lift > 1.5 && prediction.lift <= 2.0 && (
                  <Badge variant="purple" className="text-xs">
                    unusual
                  </Badge>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
