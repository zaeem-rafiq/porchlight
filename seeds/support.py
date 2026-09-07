"""P-01 support data: volunteers, cooling-center resources, protocol YAML."""

VOLUNTEERS = [
    ("Marcus Webb", True, "Elm St"),
    ("Priya Raman", True, "Maple Ave"),
    ("Jesse Cole", True, "Willow St"),
    ("Ana Beltran", True, "Oak Dr"),
    ("David Kim", False, "Elm St"),
]

RESOURCES = [
    ("Pea Ridge Library Cooling Center", "cooling_center",
     "191 Price Ave, Pea Ridge, AR", "Mon-Sat 9am-8pm, Sun 1-6pm",
     "+14795550101"),
    ("Bentonville Community Center", "cooling_center",
     "1101 SW Citizenship Cir, Bentonville, AR", "Daily 8am-9pm",
     "+14795550102"),
    ("First Baptist Fellowship Hall", "cooling_center",
     "3980 W Highway 94, Rogers, AR", "Daily 10am-6pm when heat advisory+",
     "+14795550103"),
]

PROTOCOL_YAML = """\
protocol_version: P-01
tiers:
  tier_1_first: "lives_alone and (age_band in [75-84, 85+] or not has_ac or powered_medical_device)"
  tier_2_second: "everyone else"
retry_ladder:
  - "sms, wait 45 min"
  - "sms again with plain-words ask"
  - "voice call (P-08 extra; until then flag for coordinator)"
  - "flag unreachable, notify emergency contact with 'call 911' guidance"
coordinator_ping_conditions:
  - "one consolidated SMS per event after tier-1 wave resolves"
  - "immediate ping on medical need or opt-out spike"
quiet_hours: "21:00-08:00 local; medical overrides"
opt_out: "STOP honored everywhere, first contact carries 'Reply STOP to opt out'; HELP gets usage summary"
languages: "outreach in resident language (en/es); board shows original + translation"
"""
