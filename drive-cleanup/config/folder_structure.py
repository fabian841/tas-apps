"""
Target folder structure for TAS Google Drive workspace.
18 top-level folders, each with specified subfolders + _ARCHIVE.
"""

TARGET_STRUCTURE = {
    "LEGAL": ["CONTRACTS", "SHA"],
    "PEOPLE": ["CORRESPONDENCE"],
    "CLIENTS": ["COMPETITORS"],
    "COMPANY": ["SUPPLIERS", "DISTRIBUTORS"],
    "SALES & MARKETING": ["SALES", "MARKETING", "MEDIA"],
    "PRODUCT & TECH": ["PRODUCT", "SOFTWARE", "CERTIFICATION"],
    "STRATEGY & PLANNING": ["STRATEGY", "PLANNING", "INTELLIGENCE"],
    "FINANCE": [],
    "INSURANCE": [],
    "PERSONAL": [],
    "TRAVEL": [],
    "MEETINGS": [],
    "TRANSCRIPTS": [],
    "HR": [],
    "TRAINING": [],
    "TAS": [],
    "TO SORT": [],
    "_CLAUDE": [],
}

# Old folder -> new location migration map
MIGRATION_MAP = {
    # _CLAUDE numbered subfolders
    "_CLAUDE/01-BIZ BUSINESS": ["FINANCE", "LEGAL", "TAS"],  # by content
    "_CLAUDE/02-PRD PRODUCTS": ["PRODUCT & TECH/PRODUCT"],
    "_CLAUDE/03-MFG MANUFACTURING": ["COMPANY/SUPPLIERS"],
    "_CLAUDE/04-SLS SALES": ["SALES & MARKETING/SALES"],
    "_CLAUDE/05-MKT MARKETING": ["SALES & MARKETING/MARKETING"],
    "_CLAUDE/06-STR STRATEGY": ["STRATEGY & PLANNING/STRATEGY"],
    "_CLAUDE/07-PER PERSONAL": ["PERSONAL"],
    "_CLAUDE/08-CLW CLAUDE WORKSPACE": ["_CLAUDE"],
    "_CLAUDE/09-IDR IDEAS AND RD": ["STRATEGY & PLANNING/PLANNING"],
    "_CLAUDE/10-INT INTERNATIONAL": ["STRATEGY & PLANNING/INTELLIGENCE"],
    "_CLAUDE/11-RSV RESERVED": ["TO SORT"],
    # Standalone old folders
    "CERTIFICATION": ["PRODUCT & TECH/CERTIFICATION"],
    "CLIENTS": ["CLIENTS"],
    "COMPETITORS": ["CLIENTS/COMPETITORS"],
    "CONTRACTS": ["LEGAL/CONTRACTS"],
    "CORROSPONDENCE": ["PEOPLE/CORRESPONDENCE"],
    "DISTRIBUTORS": ["COMPANY/DISTRIBUTORS"],
    "DOCUMENTS/NSP": ["COMPANY/DISTRIBUTORS"],
    "DOCUMENTS/PORTABOOM": ["PRODUCT & TECH/PRODUCT"],
    "DOCUMENTS/TAS": ["TAS"],
    "DOCUMENTS/Web Items": ["SALES & MARKETING/MARKETING"],
    "DOWNLOADS": ["TO SORT"],
    "FINANCE": ["FINANCE"],
    "HR": ["HR"],
    "i-DESKTOP": ["TO SORT"],
    "INSURANCE": ["INSURANCE"],
    "INTELLIGENCE": ["STRATEGY & PLANNING/INTELLIGENCE"],
    "MARKETING": ["SALES & MARKETING/MARKETING"],
    "MEDIA": ["SALES & MARKETING/MEDIA"],
    "MEETINGS": ["MEETINGS"],
    "NOT SYNCED": ["TO SORT"],
    "OS-MARKET": ["STRATEGY & PLANNING/INTELLIGENCE"],
    "PEOPLE": ["PEOPLE"],
    "PERSONAL": ["PERSONAL"],
    "PLANNING": ["STRATEGY & PLANNING/PLANNING"],
    "PRODUCT": ["PRODUCT & TECH/PRODUCT"],
    "SALES": ["SALES & MARKETING/SALES"],
    "SHA": ["LEGAL/SHA"],
    "SOFTWARE": ["PRODUCT & TECH/SOFTWARE"],
    "STRATEGY": ["STRATEGY & PLANNING/STRATEGY"],
    "SUPPLIERS": ["COMPANY/SUPPLIERS"],
    "TAS": ["TAS"],
    "TO SORT": ["TO SORT"],
    "TRAINING": ["TRAINING"],
    "TRANSCRIPTS": ["TRANSCRIPTS"],
    "TRAVEL": ["TRAVEL"],
}

# Filing rules: keyword patterns -> destination folder path
FILING_RULES = [
    # Most specific first
    {"keywords": ["shareholders agreement", "sha"], "destination": "LEGAL/SHA", "priority": 1},
    {"keywords": ["legal agreement", "contract", "mou", "memorandum of understanding"], "destination": "LEGAL/CONTRACTS", "priority": 1},

    # People - specific names
    {"keywords": ["tynan"], "destination": "PEOPLE/Tynan", "priority": 2},
    {"keywords": ["amy harper", "kells"], "destination": "PEOPLE/Amy-Harper", "priority": 2},
    {"keywords": ["sarah cross"], "destination": "PEOPLE/Sarah-Cross", "priority": 2},
    {"keywords": ["paul bland"], "destination": "PEOPLE/Paul-Bland", "priority": 2},
    {"keywords": ["riley"], "destination": "PEOPLE/Riley", "priority": 3},
    {"keywords": ["noel kelly"], "destination": "PEOPLE/Noel-Kelly", "priority": 2},
    {"keywords": ["sam marciano"], "destination": "PEOPLE/Sam-Marciano", "priority": 2},

    # Company - suppliers and distributors
    {"keywords": ["nsp", "nick felmingham", "national safety products"], "destination": "COMPANY/DISTRIBUTORS", "priority": 2},
    {"keywords": ["jaybro"], "destination": "COMPANY/DISTRIBUTORS", "priority": 2},
    {"keywords": ["ankuai", "jack"], "destination": "COMPANY/SUPPLIERS", "priority": 3},
    {"keywords": ["trafficon", "fiona", "vms"], "destination": "COMPANY/SUPPLIERS", "priority": 3},

    # Clients and competitors
    {"keywords": ["competitor", "competitive analysis"], "destination": "CLIENTS/COMPETITORS", "priority": 2},
    {"keywords": ["client", "customer"], "destination": "CLIENTS", "priority": 3},

    # Sales & Marketing
    {"keywords": ["sales pipeline", "quote", "proposal", "order", "pricing"], "destination": "SALES & MARKETING/SALES", "priority": 2},
    {"keywords": ["marketing campaign", "copy", "ad ", "collateral", "brochure"], "destination": "SALES & MARKETING/MARKETING", "priority": 2},
    {"keywords": ["photo", "video", "render", "brand asset", "shoot"], "destination": "SALES & MARKETING/MEDIA", "priority": 2},

    # Product & Tech
    {"keywords": ["pb4000", "portaboom", "product spec", "sop", "manual"], "destination": "PRODUCT & TECH/PRODUCT", "priority": 2},
    {"keywords": ["miniboom", "tz30"], "destination": "PRODUCT & TECH/PRODUCT", "priority": 2},
    {"keywords": ["tastrack", "brain os", "n8n", "zoho", "software", "code", "script"], "destination": "PRODUCT & TECH/SOFTWARE", "priority": 3},
    {"keywords": ["certification", "regulatory", "compliance", "test report"], "destination": "PRODUCT & TECH/CERTIFICATION", "priority": 2},

    # Strategy & Planning
    {"keywords": ["business strategy", "bhag", "board doc", "investor"], "destination": "STRATEGY & PLANNING/STRATEGY", "priority": 2},
    {"keywords": ["business plan", "roadmap", "okr", "project plan"], "destination": "STRATEGY & PLANNING/PLANNING", "priority": 2},
    {"keywords": ["market research", "competitive intel", "industry report"], "destination": "STRATEGY & PLANNING/INTELLIGENCE", "priority": 2},
    {"keywords": ["international", " uk ", "canada", " usa ", " nzl ", "new zealand"], "destination": "STRATEGY & PLANNING/INTELLIGENCE", "priority": 3},

    # Finance
    {"keywords": ["invoice", "p&l", "profit", "loss", "bank", "bas", "budget", "cashflow", "nab"], "destination": "FINANCE", "priority": 2},

    # Insurance
    {"keywords": ["insurance", "policy", "claim", "tmaa"], "destination": "INSURANCE", "priority": 2},

    # Personal
    {"keywords": ["personal", "diego"], "destination": "PERSONAL", "priority": 3},

    # Travel
    {"keywords": ["travel", "itinerary", "booking", "passport", "flight"], "destination": "TRAVEL", "priority": 2},

    # Meetings
    {"keywords": ["meeting", "agenda", "minutes", "action items"], "destination": "MEETINGS", "priority": 2},

    # Transcripts
    {"keywords": ["transcript", "voice note", "plaud", "recording"], "destination": "TRANSCRIPTS", "priority": 2},

    # HR
    {"keywords": ["employment", "onboarding", "leave", "performance review"], "destination": "HR", "priority": 2},

    # Training
    {"keywords": ["training", "staff certification"], "destination": "TRAINING", "priority": 2},

    # TAS company-level
    {"keywords": ["abn", "asic", "company registration", "company structure", "register"], "destination": "TAS", "priority": 2},

    # Correspondence (general)
    {"keywords": ["letter", "correspondence", "formal letter"], "destination": "PEOPLE/CORRESPONDENCE", "priority": 3},
]

# File extensions -> likely media
MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg",
                    ".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav"}
