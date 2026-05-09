import { useState } from "react";
import { Info } from "lucide-react";
import { useEventImportance } from "@/api/queries";
import { FeatureImportanceChart } from "./FeatureImportanceChart";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import type { Prediction } from "@/types/api";

interface ExplainPopoverProps {
  prediction: Prediction;
}

function getExplanation(lift: number): string {
  if (lift > 1.5) {
    return "The model thinks this event is notably more likely than average in this match.";
  }
  if (lift < 0.7) {
    return "The model thinks this event is less likely than average in this match.";
  }
  return "The model's prediction is close to the historical average for this event.";
}

export function ExplainPopover({ prediction }: ExplainPopoverProps) {
  const [open, setOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data: importanceData } = useEventImportance(prediction.event_id);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        aria-label="Explain prediction"
      >
        <Info className="h-4 w-4" />
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 top-8 z-50 w-80 bg-white rounded-lg border border-slate-200 shadow-lg p-4 space-y-3">
            <h4 className="font-semibold text-sm text-slate-900">
              {prediction.display_name}
            </h4>
            <p className="text-sm text-slate-600">
              This match:{" "}
              <span className="font-medium">
                {(prediction.probability * 100).toFixed(1)}%
              </span>{" "}
              (base rate: {(prediction.base_rate * 100).toFixed(1)}%, lift:{" "}
              {prediction.lift.toFixed(2)}×)
            </p>
            <p className="text-sm text-slate-700 bg-slate-50 rounded-md p-2">
              {getExplanation(prediction.lift)}
            </p>

            {importanceData && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                  Top driving features
                </p>
                <div className="space-y-1">
                  {importanceData.features.slice(0, 3).map((f) => (
                    <div
                      key={f.feature}
                      className="flex justify-between text-sm"
                    >
                      <span className="text-slate-700">{f.feature}</span>
                      <span className="text-slate-500 font-mono">
                        {f.importance.toFixed(4)}
                      </span>
                    </div>
                  ))}
                </div>
                <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                  <DialogTrigger>
                    <span className="text-sm text-blue-600 hover:text-blue-800 font-medium cursor-pointer">
                      See all feature importances →
                    </span>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>
                        Feature Importances: {importanceData.display_name}
                      </DialogTitle>
                    </DialogHeader>
                    <FeatureImportanceChart features={importanceData.features} />
                  </DialogContent>
                </Dialog>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
