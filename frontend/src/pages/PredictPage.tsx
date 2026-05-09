import { useState } from "react";
import { usePredict } from "@/api/queries";
import { MatchInputForm } from "@/components/MatchInputForm";
import { MatchMetaHeader } from "@/components/MatchMetaHeader";
import { Top5LikelyList } from "@/components/Top5LikelyList";
import { Top5NotableList } from "@/components/Top5NotableList";
import { Loading } from "@/components/Loading";

export function PredictPage() {
  const [inputs, setInputs] = useState<{
    team1: string;
    team2: string;
    venue: string;
    matchDate: string;
  } | null>(null);

  const { data, isLoading, error, isError } = usePredict(
    inputs?.team1 ?? "",
    inputs?.team2 ?? "",
    inputs?.venue ?? "",
    inputs?.matchDate ?? ""
  );

  const handlePredict = (team1: string, team2: string, venue: string, matchDate: string) => {
    setInputs({ team1, team2, venue, matchDate });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="text-center space-y-1">
          <h1 className="text-3xl font-bold text-slate-900">IPL Predictor</h1>
          <p className="text-sm text-slate-500">
            AI-powered match event predictions using calibrated XGBoost models
          </p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
          <MatchInputForm onPredict={handlePredict} />
        </div>

        {/* Error */}
        {isError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800 text-sm">
            <p className="font-medium">Prediction failed</p>
            <p>{error instanceof Error ? error.message : "Unknown error"}</p>
          </div>
        )}

        {/* Loading */}
        {isLoading && <Loading />}

        {/* Results */}
        {data && (
          <div className="space-y-6">
            <MatchMetaHeader meta={data.meta} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Top5LikelyList predictions={data.top_5_likely} />
              <Top5NotableList predictions={data.top_5_notable} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
