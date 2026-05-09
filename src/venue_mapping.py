"""Venue-to-home-team mapping for IPL home/away encoding."""

# Primary and secondary home grounds. Empty set = neutral venue.
VENUE_TO_HOME_TEAM: dict[str, set[str]] = {
    # -- Mumbai Indians --
    "Wankhede Stadium": {"Mumbai Indians"},
    "Wankhede Stadium, Mumbai": {"Mumbai Indians"},
    "Brabourne Stadium": {"Mumbai Indians"},
    "Brabourne Stadium, Mumbai": {"Mumbai Indians"},
    "Dr DY Patil Sports Academy": {"Mumbai Indians"},
    "Dr DY Patil Sports Academy, Mumbai": {"Mumbai Indians"},

    # -- Royal Challengers Bangalore / Bengaluru --
    "M Chinnaswamy Stadium": {"Royal Challengers Bangalore", "Royal Challengers Bengaluru"},
    "M Chinnaswamy Stadium, Bengaluru": {"Royal Challengers Bangalore", "Royal Challengers Bengaluru"},
    "M.Chinnaswamy Stadium": {"Royal Challengers Bangalore", "Royal Challengers Bengaluru"},

    # -- Chennai Super Kings --
    "MA Chidambaram Stadium": {"Chennai Super Kings"},
    "MA Chidambaram Stadium, Chepauk": {"Chennai Super Kings"},
    "MA Chidambaram Stadium, Chepauk, Chennai": {"Chennai Super Kings"},
    "JSCA International Stadium Complex": {"Chennai Super Kings"},  # Ranchi, secondary home

    # -- Kolkata Knight Riders --
    "Eden Gardens": {"Kolkata Knight Riders"},
    "Eden Gardens, Kolkata": {"Kolkata Knight Riders"},

    # -- Delhi Capitals --
    "Feroz Shah Kotla": {"Delhi Capitals"},
    "Arun Jaitley Stadium": {"Delhi Capitals"},
    "Arun Jaitley Stadium, Delhi": {"Delhi Capitals"},

    # -- Rajasthan Royals --
    "Sawai Mansingh Stadium": {"Rajasthan Royals"},
    "Sawai Mansingh Stadium, Jaipur": {"Rajasthan Royals"},
    "Barsapara Cricket Stadium, Guwahati": {"Rajasthan Royals"},

    # -- Punjab Kings / Kings XI Punjab --
    "Punjab Cricket Association Stadium, Mohali": {"Punjab Kings", "Kings XI Punjab"},
    "Punjab Cricket Association IS Bindra Stadium, Mohali": {"Punjab Kings", "Kings XI Punjab"},
    "Punjab Cricket Association IS Bindra Stadium": {"Punjab Kings", "Kings XI Punjab"},
    "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh": {"Punjab Kings", "Kings XI Punjab"},
    "Himachal Pradesh Cricket Association Stadium": {"Punjab Kings", "Kings XI Punjab"},
    "Himachal Pradesh Cricket Association Stadium, Dharamsala": {"Punjab Kings", "Kings XI Punjab"},
    "Holkar Cricket Stadium": {"Punjab Kings", "Kings XI Punjab"},
    "Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur": {"Punjab Kings", "Kings XI Punjab"},
    "Maharaja Yadavindra Singh International Cricket Stadium, New Chandigarh": {"Punjab Kings", "Kings XI Punjab"},

    # -- Sunrisers Hyderabad / Deccan Chargers --
    "Rajiv Gandhi International Stadium, Uppal": {"Sunrisers Hyderabad", "Deccan Chargers"},
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": {"Sunrisers Hyderabad", "Deccan Chargers"},
    "Rajiv Gandhi International Stadium": {"Sunrisers Hyderabad", "Deccan Chargers"},
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium": {"Sunrisers Hyderabad", "Deccan Chargers"},
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam": {"Sunrisers Hyderabad", "Deccan Chargers"},

    # -- Gujarat Titans / Rajasthan Royals (Motera/Ahmedabad) --
    "Narendra Modi Stadium, Ahmedabad": {"Gujarat Titans", "Rajasthan Royals"},
    "Sardar Patel Stadium, Motera": {"Gujarat Titans", "Rajasthan Royals"},

    # -- Lucknow Super Giants / Rising Pune Supergiant(s) --
    "Maharashtra Cricket Association Stadium": {"Lucknow Super Giants", "Rising Pune Supergiant", "Rising Pune Supergiants"},
    "Maharashtra Cricket Association Stadium, Pune": {"Lucknow Super Giants", "Rising Pune Supergiant", "Rising Pune Supergiants"},
    "Subrata Roy Sahara Stadium": {"Lucknow Super Giants", "Rising Pune Supergiant", "Rising Pune Supergiants"},
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow": {"Lucknow Super Giants"},
    "BRSABV Ekana Cricket Stadium": {"Lucknow Super Giants"},

    # -- Neutral venues (UAE) --
    "Sharjah Cricket Stadium": set(),
    "Dubai International Cricket Stadium": set(),
    "Sheikh Zayed Stadium": set(),
    "Zayed Cricket Stadium, Abu Dhabi": set(),

    # -- Neutral venues (India) --
    "Green Park": set(),
    "Vidarbha Cricket Association Stadium, Jamtha": set(),
    "Shaheed Veer Narayan Singh International Stadium": set(),
    "Saurashtra Cricket Association Stadium": set(),

    # -- Neutral venues (South Africa 2009) --
    "Newlands": set(),
    "SuperSport Park": set(),
    "Kingsmead": set(),
    "New Wanderers Stadium": set(),
    "St George's Park": set(),
    "OUTsurance Oval": set(),
    "De Beers Diamond Oval": set(),
    "Buffalo Park": set(),

    # -- Other / defunct / shared --
    "Barabati Stadium": set(),
    "Nehru Stadium": set(),
}


def get_home_team(venue: str) -> set[str]:
    """Return the set of team names that consider this venue home.

    Empty set means the venue is neutral (playoff ground, UAE, etc.).
    """
    return VENUE_TO_HOME_TEAM.get(venue, set())
