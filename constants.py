"""
Constants en configuratie parameters voor synthetische wisselonderhoud dataset generator.

Dit bestand bevat alle configureerbare parameters voor het genereren van realistische
onderhoudsdata voor spoorwegwissels.
"""

import random
from datetime import datetime, timedelta

# ===== WISSEL CONFIGURATIE =====
SWITCH_TYPES = [
    "Enkelvoudige wissel",
    "Kruiswissel", 
    "Dubbele kruiswissel",
    "Engelse wissel",
    "Buitengewone wissel",
    "Flexibele wissel",
    "Beweegbare punt wissel"
]

SWITCH_HANDS = [
    "Links",
    "Rechts"
]

# ===== ONDERHOUD CONFIGURATIE =====
MAINTENANCE_TYPES = [
    "Preventief onderhoud",
    "Correctief onderhoud", 
    "Inspectie",
    "Noodonderhoud",
    "Periodiek onderhoud",
    "Conditie-gericht onderhoud"
]

MAINTENANCE_CATEGORIES = [
    "Smering en reiniging",
    "Wisselmotor service",
    "Blade onderhoud",
    "Slijtage controle",
    "Elektrische controle",
    "Mechanische controle",
    "Veiligheidscontrole",
    "Vervangen onderdelen"
]

WORK_DESCRIPTIONS = [
    "Smering van wisselbladen en geleiders",
    "Controle en afstelling wisselmotor",
    "Vervangen van slijtageplaten",
    "Reiniging van wisselhart en vleugels",
    "Controle van bevestigingsmiddelen",
    "Afstelling van wisselspanning",
    "Vervangen van defecte onderdelen",
    "Visuele inspectie van wissel",
    "Meting van slijtage en speling",
    "Controle van elektrische verbindingen",
    "Onderhoud aan detectiesysteem",
    "Vervangen van wisselbladen"
]

BLADE_CONDITIONS = [
    "Goed",
    "Lichte slijtage",
    "Matige slijtage", 
    "Sterke slijtage",
    "Vervangen nodig",
    "Beschadigd"
]

OPERATION_TEST_RESULTS = [
    "passed",
    "failed", 
    "not tested",
    "partial"
]

# ===== ONDERHOUDSPARTIJEN =====
CONTRACTOR_COMPANIES = [
    "ProRail Onderhoud",
    "Strukton Rail",
    "BAM Infra Rail",
    "Volker Rail",
    "Swietelsky Rail",
    "Movares",
    "Arcadis Nederland",
    "Rijkswaterstaat",
    "Dura Vermeer",
    "KWS Infra"
]

# ===== NUMERIEKE RANGES =====
# Duur van onderhoud in minuten
DURATION_RANGES = {
    "Inspectie": (15, 60),
    "Preventief onderhoud": (30, 180),
    "Correctief onderhoud": (60, 480),
    "Noodonderhoud": (30, 360),
    "Periodiek onderhoud": (45, 240),
    "Conditie-gericht onderhoud": (30, 120)
}

# Slijtage meting in millimeters
WEAR_MEASUREMENT_RANGE = (0.0, 25.0)

# Aantal technici
TECHNICIAN_COUNT_RANGE = (1, 6)

# ===== KANS DISTRIBUTIES =====
# Kans dat smering wordt toegepast per onderhoudstype
LUBRICATION_PROBABILITY = {
    "Preventief onderhoud": 0.8,
    "Correctief onderhoud": 0.4,
    "Inspectie": 0.1,
    "Noodonderhoud": 0.3,
    "Periodiek onderhoud": 0.9,
    "Conditie-gericht onderhoud": 0.6
}

# Kans dat wisselmotor wordt onderhouden per onderhoudstype
MOTOR_SERVICE_PROBABILITY = {
    "Preventief onderhoud": 0.6,
    "Correctief onderhoud": 0.8,
    "Inspectie": 0.1,
    "Noodonderhoud": 0.7,
    "Periodiek onderhoud": 0.5,
    "Conditie-gericht onderhoud": 0.4
}

# Kans distributie voor test resultaten
TEST_RESULT_PROBABILITY = {
    "passed": 0.75,
    "failed": 0.10,
    "not tested": 0.10,
    "partial": 0.05
}

# ===== TIJD CONFIGURATIE =====
# Werkuren (24-uurs formaat)
WORK_HOURS_START = 6
WORK_HOURS_END = 22

# Datum range voor onderhoud (laatste 2 jaar)
START_DATE = datetime.now() - timedelta(days=730)
END_DATE = datetime.now()

# ===== DATASET CONFIGURATIE =====
# Standaard aantal records te genereren
DEFAULT_RECORD_COUNT = 1000

# Aantal unieke wissels
UNIQUE_SWITCH_COUNT = 200

# ===== VERBANDEN CONFIGURATIE =====
# Configuratie voor verbanden tussen onderhoud en storingen
MAINTENANCE_PATTERNS = {
    # Patroon 1: Bepaalde wisseltypen hebben meer onderhoud nodig
    "high_maintenance_switches": {
        "switch_types": ["Kruiswissel", "Dubbele kruiswissel"],
        "maintenance_frequency_multiplier": 2.5,
        "preferred_contractors": ["Strukton Rail", "BAM Infra Rail"]
    },
    
    # Patroon 2: Stations met veel storingen krijgen meer preventief onderhoud
    "high_disruption_stations": {
        "maintenance_type_preference": "Preventief onderhoud",
        "frequency_multiplier": 1.8
    },
    
    # Patroon 3: Bepaalde contractors zijn gespecialiseerd in bepaalde wisseltypen
    "contractor_specialization": {
        "Strukton Rail": ["Kruiswissel", "Dubbele kruiswissel"],
        "Volker Rail": ["Enkelvoudige wissel", "Engelse wissel"],
        "BAM Infra Rail": ["Flexibele wissel", "Buitengewone wissel"]
    },
    
    # Patroon 4: Seizoensgebonden onderhoud
    "seasonal_maintenance": {
        "winter_months": [11, 12, 1, 2],
        "winter_maintenance_increase": 1.4,
        "summer_months": [6, 7, 8],
        "summer_maintenance_decrease": 0.8
    }
}

# ===== HELPER FUNCTIES =====
def get_random_duration(maintenance_type):
    """Geef een realistische duur terug voor een onderhoudstype."""
    if maintenance_type in DURATION_RANGES:
        min_dur, max_dur = DURATION_RANGES[maintenance_type]
        return random.randint(min_dur, max_dur)
    return random.randint(30, 120)  # Default range

def get_random_wear_measurement():
    """Geef een realistische slijtage meting terug."""
    return round(random.uniform(*WEAR_MEASUREMENT_RANGE), 2)

def get_random_technician_count():
    """Geef een realistisch aantal technici terug."""
    return random.randint(*TECHNICIAN_COUNT_RANGE)

def should_apply_lubrication(maintenance_type):
    """Bepaal of smering moet worden toegepast."""
    probability = LUBRICATION_PROBABILITY.get(maintenance_type, 0.5)
    return random.random() < probability

def should_service_motor(maintenance_type):
    """Bepaal of wisselmotor moet worden onderhouden."""
    probability = MOTOR_SERVICE_PROBABILITY.get(maintenance_type, 0.5)
    return random.random() < probability

def get_random_test_result():
    """Geef een gewogen willekeurig test resultaat terug."""
    rand = random.random()
    cumulative = 0
    for result, probability in TEST_RESULT_PROBABILITY.items():
        cumulative += probability
        if rand <= cumulative:
            return result
    return "passed"  # Fallback

def get_random_work_time():
    """Geef een willekeurige werktijd terug binnen werkuren."""
    hour = random.randint(WORK_HOURS_START, WORK_HOURS_END - 1)
    minute = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}"

def get_random_date():
    """Geef een willekeurige datum terug binnen de configureerde range."""
    time_between = END_DATE - START_DATE
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return START_DATE + timedelta(days=random_days)