import { useState } from "react";
import { PredictionCard } from "./PredictionCard";
import type { Prediction } from "@/types/api";
import { BadgeCheck } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Top5LikelyListProps {
  predictions: Prediction[];
}

export function Top5LikelyList({ predictions }: Top5LikelyListProps) {
  const [aboutOpen, setAboutOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <BadgeCheck className="h-5 w-5 text-blue-600" />
        <h2 className="text-lg font-semibold text-slate-900">Most Likely</h2>
        <span className="text-sm text-slate-500">safe bets ranked by probability</span>
      </div>
      <div className="space-y-3">
        {predictions.map((p, i) => (
          <PredictionCard key={p.event_id} prediction={p} index={i} variant="likely" />
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
            <DialogTitle>About Most Likely</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-slate-600">
            This list picks events the model is most confident will happen.
            Base rates dominate — obvious events rank high.
          </p>
        </DialogContent>
      </Dialog>
    </div>
  );
}
