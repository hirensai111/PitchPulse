import sys
sys.path.insert(0, 'src')

import pandas as pd
from pathlib import Path
from venue_mapping import VENUE_TO_HOME_TEAM, get_home_team

matches = pd.read_parquet('data/processed/matches.parquet')
venue_counts = matches['venue'].value_counts().to_dict()
unique_venues = sorted(venue_counts.keys())

total_matches = len(matches)
mapped_matches = 0
unmapped_venues = []
unmapped_matches = 0

lines = []
lines.append("=" * 80)
lines.append("VENUE AUDIT")
lines.append("=" * 80)
lines.append("")

for venue in unique_venues:
    count = venue_counts[venue]
    home_teams = get_home_team(venue)
    is_mapped = venue in VENUE_TO_HOME_TEAM
    if is_mapped:
        mapped_matches += count
        status = f"mapped -> {home_teams if home_teams else 'NEUTRAL'}"
    else:
        unmapped_venues.append(venue)
        unmapped_matches += count
        status = "UNMAPPED"
    lines.append(f"{venue!r:<65s} | count={count:>4d} | {status}")

lines.append("")
lines.append("=" * 80)
lines.append("SUMMARY")
lines.append("=" * 80)
lines.append(f"Total unique venues: {len(unique_venues)}")
lines.append(f"Mapped venues: {len(VENUE_TO_HOME_TEAM)}")
lines.append(f"Unmapped venues: {len(unmapped_venues)}")
lines.append(f"Total matches: {total_matches}")
lines.append(f"Matches at mapped venues: {mapped_matches}")
lines.append(f"Matches at unmapped venues: {unmapped_matches}")
lines.append(f"Coverage: {mapped_matches / total_matches * 100:.1f}%")

if unmapped_venues:
    lines.append("")
    lines.append("UNMAPPED VENUES:")
    for v in unmapped_venues:
        lines.append(f"  {v!r} ({venue_counts[v]} matches)")

output = "\n".join(lines)
print(output)

audit_path = Path('data/processed/venue_audit.txt')
audit_path.write_text(output, encoding='utf-8')
print(f"\nSaved to {audit_path}")
