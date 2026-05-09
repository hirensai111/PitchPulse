import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTeams, useVenues } from "@/api/queries";
// Venue type not needed directly
import { CalendarDays, MapPin, Shield, Swords } from "lucide-react";

interface MatchInputFormProps {
  onPredict: (team1: string, team2: string, venue: string, date: string) => void;
}

export function MatchInputForm({ onPredict }: MatchInputFormProps) {
  const { data: teams = [], isLoading: teamsLoading } = useTeams();
  const { data: venues = [], isLoading: venuesLoading } = useVenues();

  const [team1, setTeam1] = useState("");
  const [team2, setTeam2] = useState("");
  const [venue, setVenue] = useState("");
  const [matchDate, setMatchDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split("T")[0];
  });

  const selectedVenue = useMemo(
    () => venues.find((v) => v.venue === venue),
    [venues, venue]
  );

  const team2Options = useMemo(
    () => teams.filter((t) => t !== team1),
    [teams, team1]
  );

  const isValid =
    team1 && team2 && venue && matchDate && team1 !== team2;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isValid) {
      onPredict(team1, team2, venue, matchDate);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Team 1 */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
            <Shield className="h-3.5 w-3.5" />
            Team 1
          </label>
          <select
            value={team1}
            onChange={(e) => {
              setTeam1(e.target.value);
              if (team2 === e.target.value) setTeam2("");
            }}
            className="w-full h-10 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
            disabled={teamsLoading}
          >
            <option value="">Select team...</option>
            {teams.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        {/* Team 2 */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
            <Swords className="h-3.5 w-3.5" />
            Team 2
          </label>
          <select
            value={team2}
            onChange={(e) => setTeam2(e.target.value)}
            className="w-full h-10 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
            disabled={!team1 || teamsLoading}
          >
            <option value="">Select opponent...</option>
            {team2Options.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        {/* Venue */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5" />
            Venue
          </label>
          <select
            value={venue}
            onChange={(e) => setVenue(e.target.value)}
            className="w-full h-10 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
            disabled={venuesLoading}
          >
            <option value="">Select venue...</option>
            {venues.map((v) => (
              <option key={v.venue} value={v.venue}>
                {v.venue}
              </option>
            ))}
          </select>
        </div>

        {/* Date */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
            <CalendarDays className="h-3.5 w-3.5" />
            Match Date
          </label>
          <input
            type="date"
            value={matchDate}
            onChange={(e) => setMatchDate(e.target.value)}
            className="w-full h-10 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
      </div>

      {/* Venue info strip */}
      {selectedVenue && (
        <div className="flex items-center gap-2 text-sm text-slate-600 bg-slate-50 rounded-md px-3 py-2">
          <MapPin className="h-3.5 w-3.5 text-slate-400" />
          <span className="font-medium">{selectedVenue.venue}</span>
          {selectedVenue.home_teams.length > 0 ? (
            <>
              <span className="text-slate-400">|</span>
              <span>Home to:</span>
              {selectedVenue.home_teams.map((t) => (
                <Badge key={t} variant="blue" className="text-xs">
                  {t}
                </Badge>
              ))}
            </>
          ) : (
            <Badge variant="gray" className="text-xs">Neutral venue</Badge>
          )}
        </div>
      )}

      <div className="flex justify-end">
        <Button type="submit" disabled={!isValid} size="lg">
          Predict
        </Button>
      </div>
    </form>
  );
}
