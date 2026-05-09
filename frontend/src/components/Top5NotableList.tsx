import { useState } from "react";
import { PredictionCard } from "./PredictionCard";
import type { Prediction } from "@/types/api";
import { Sparkles } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Top5NotableListProps {
  predictions: Prediction[];
}

export function Top5NotableList({ predictions }: Top5NotableListProps) {
  const [aboutOpen, setAboutOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-violet-600" />
        <h2 className="text-lg font-semibold text-slate-900">Most Notable</h2>
        <span className="text-sm text-slate-500">interesting picks ranked by lift</span>
      </div>
      <div className="space-y-3">
        {predictions.map((p, i) => (
          <PredictionCard key={p.event_id} prediction={p} index={i} variant="notable" />
        ))}
      </div>
      <button
        onClick={() => setAboutOpen(true)}
        className="text-sm text-slate-500 hover:text-slate-800 underline underline-offset-2"
      >
        About this prediction
      </button>

      <Dialog open={aboutOpen} onOpenChange={setAboutOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>About Most Notable</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-slate-600">
            This list picks events whose predicted probability is unusually high
            relative to their historical base rate. More context-sensitive, less
            aggregate accuracy.
          </p>
        </DialogContent>
      </Dialog>
    </div>
  );
}
