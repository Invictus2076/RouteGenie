"""
knowledge_base.py
═══════════════════════════════════════════════════════════════
Travel Planner — World Knowledge Base
Stores facts about cities, hotels, attractions, routes, costs.
These facts populate the PDDL problem files at planning time.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Data Classes ──────────────────────────────────────────────────────

@dataclass
class Hotel:
    name: str
    style: str          # budget | midrange | luxury | boutique
    cost_per_night: int # USD per night per room
    stars: int
    amenities: List[str] = field(default_factory=list)

    def pddl_id(self) -> str:
        return self.name.lower().replace(" ", "_").replace("'", "").replace("-", "_")


@dataclass
class Attraction:
    name: str
    category: str       # culture | nature | food | beach | nightlife | shopping
    entry_cost: int     # USD per person
    duration_hours: float
    tip: str = ""

    def pddl_id(self) -> str:
        return self.name.lower().replace(" ", "_").replace("'", "").replace(",", "").replace("-","_").replace("(","").replace(")","")


@dataclass
class City:
    name: str
    country: str
    flag: str
    climate: str
    cost_per_day: int       # avg daily spend per person (excl. hotel)
    best_season: str
    transport_mode: str
    timezone: str
    hotels: Dict[str, Hotel] = field(default_factory=dict)
    attractions: List[Attraction] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def pddl_id(self) -> str:
        return self.name.lower().replace(" ", "_").replace("'", "")


# ── Flight Routes & Costs ─────────────────────────────────────────────

FLIGHT_ROUTES: Dict[tuple, int] = {
    ("new_york",  "paris"):         650,
    ("new_york",  "bali"):         1200,
    ("new_york",  "tokyo"):         800,
    ("new_york",  "rome"):          650,
    ("new_york",  "santorini"):     900,
    ("new_york",  "kyoto"):         850,
    ("new_york",  "machu_picchu"):  700,
    ("london",    "paris"):          85,
    ("london",    "bali"):         1000,
    ("london",    "tokyo"):         900,
    ("london",    "rome"):          120,
    ("london",    "santorini"):     310,
    ("london",    "kyoto"):         950,
    ("london",    "machu_picchu"):  900,
    ("tokyo",     "bali"):          380,
    ("tokyo",     "paris"):         900,
    ("tokyo",     "rome"):          980,
    ("tokyo",     "santorini"):    1300,
    ("tokyo",     "machu_picchu"): 1500,
    ("sydney",    "bali"):          350,
    ("sydney",    "tokyo"):         600,
    ("sydney",    "paris"):        1100,
    ("sydney",    "rome"):         1150,
    ("sydney",    "machu_picchu"): 1600,
    ("dubai",     "paris"):         350,
    ("dubai",     "bali"):          700,
    ("dubai",     "tokyo"):         700,
    ("dubai",     "rome"):          380,
    ("dubai",     "santorini"):     450,
    ("dubai",     "kyoto"):         750,
    ("dubai",     "machu_picchu"): 1200,
    ("paris",     "santorini"):     280,
    ("paris",     "rome"):          140,
}

def get_flight_cost(origin: str, dest: str) -> Optional[int]:
    """Return one-way flight cost (USD) between two city PDDL IDs, or None if no route."""
    key = (origin, dest)
    rev = (dest, origin)
    return FLIGHT_ROUTES.get(key) or FLIGHT_ROUTES.get(rev)


FLIGHT_HOURS: Dict[tuple, float] = {
    ("new_york",  "paris"):        7.0,
    ("new_york",  "bali"):        22.0,
    ("new_york",  "tokyo"):       14.0,
    ("new_york",  "rome"):         9.0,
    ("new_york",  "santorini"):   10.0,
    ("new_york",  "machu_picchu"): 8.5,
    ("london",    "paris"):        1.5,
    ("london",    "bali"):        15.0,
    ("london",    "tokyo"):       11.5,
    ("london",    "rome"):         2.5,
    ("london",    "santorini"):    4.0,
    ("london",    "machu_picchu"):13.0,
    ("tokyo",     "bali"):         7.0,
    ("tokyo",     "paris"):       12.0,
    ("sydney",    "bali"):         5.5,
    ("sydney",    "tokyo"):        9.5,
    ("dubai",     "paris"):        7.0,
    ("paris",     "santorini"):    3.5,
    ("paris",     "rome"):         2.0,
}

def get_flight_hours(origin: str, dest: str) -> float:
    key = (origin, dest)
    rev = (dest, origin)
    return FLIGHT_HOURS.get(key) or FLIGHT_HOURS.get(rev, 9.0)


AIRLINES: Dict[tuple, str] = {
    ("new_york", "paris"):       "Air France",
    ("new_york", "tokyo"):       "Japan Airlines",
    ("new_york", "bali"):        "Singapore Airlines",
    ("new_york", "rome"):        "Alitalia / ITA",
    ("london",   "paris"):       "Eurostar / British Airways",
    ("london",   "bali"):        "Emirates",
    ("london",   "tokyo"):       "British Airways",
    ("london",   "rome"):        "easyJet / BA",
    ("london",   "santorini"):   "EasyJet",
    ("tokyo",    "bali"):        "Garuda Indonesia",
    ("sydney",   "bali"):        "Jetstar",
    ("dubai",    "paris"):       "Emirates",
    ("dubai",    "bali"):        "Emirates",
    ("paris",    "santorini"):   "Aegean Airlines",
    ("paris",    "rome"):        "Air France",
}

def get_airline(origin: str, dest: str) -> str:
    key = (origin, dest)
    rev = (dest, origin)
    return AIRLINES.get(key) or AIRLINES.get(rev, "International Airlines")


# ── City Knowledge Base ───────────────────────────────────────────────

CITIES: Dict[str, City] = {

    "paris": City(
        name="Paris", country="France", flag="🇫🇷",
        climate="Temperate Oceanic", cost_per_day=200,
        best_season="Apr–Jun, Sep–Oct", transport_mode="Metro",
        timezone="CET (UTC+1)",
        hotels={
            "budget":   Hotel("Generator Paris",      "budget",   60,  3, ["WiFi","Bar"]),
            "midrange": Hotel("Hotel du Marais",      "midrange", 160, 4, ["WiFi","Breakfast","Concierge"]),
            "luxury":   Hotel("Le Bristol Paris",     "luxury",   750, 5, ["Spa","Pool","Michelin Restaurant","Butler"]),
            "boutique": Hotel("Maison Souquet",       "boutique", 380, 5, ["Library Bar","Courtyard","Art Collection"]),
        },
        attractions=[
            Attraction("Eiffel Tower",        "culture",  30, 2.5, "Book skip-the-line tickets. Visit at sunset."),
            Attraction("Louvre Museum",        "culture",  17, 4.0, "Start at Denon wing — Mona Lisa, Venus de Milo."),
            Attraction("Notre-Dame Cathedral", "culture",   0, 1.5, "Exterior visit only; interior still under restoration."),
            Attraction("Musée d'Orsay",        "culture",  16, 3.0, "Best Impressionist collection in the world."),
            Attraction("Palace of Versailles", "culture",  20, 4.5, "Take the RER C train. Arrive before 9 AM."),
            Attraction("Montmartre & Sacré-Cœur","culture",0, 2.0, "Walk the cobblestone streets. Artists quarter."),
            Attraction("Seine River Cruise",   "culture",  17, 1.5, "Bateaux Parisiens evening cruise highly recommended."),
            Attraction("Champs-Élysées",       "shopping",  0, 2.0, "Walk from Arc de Triomphe to Place de la Concorde."),
            Attraction("Sainte-Chapelle",      "culture",  13, 1.0, "Stunning Gothic stained glass. Hidden gem."),
        ],
        tags=["culture","food","shopping","photography","romance"]
    ),

    "bali": City(
        name="Bali", country="Indonesia", flag="🇮🇩",
        climate="Tropical", cost_per_day=80,
        best_season="Apr–Oct", transport_mode="Scooter & Private Driver",
        timezone="WITA (UTC+8)",
        hotels={
            "budget":   Hotel("Kuta Beach Hostel",   "budget",   25, 2, ["Pool","Common Kitchen"]),
            "midrange": Hotel("The Layar Villa",     "midrange", 120, 4, ["Private Pool","Breakfast","Garden"]),
            "luxury":   Hotel("COMO Uma Ubud",       "luxury",   550, 5, ["Spa","Yoga Pavilion","Jungle View"]),
            "boutique": Hotel("Alaya Resort Ubud",   "boutique", 200, 4, ["Rice Field View","Cooking Class","Pool"]),
        },
        attractions=[
            Attraction("Tanah Lot Temple",       "culture",  60, 2.0, "Iconic sea temple. Best at sunset."),
            Attraction("Ubud Rice Terraces",     "nature",    0, 2.0, "Tegalalang — arrive at dawn before crowds."),
            Attraction("Sacred Monkey Forest",   "nature",   80, 1.5, "Keep valuables hidden. Feed the macaques."),
            Attraction("Mount Batur Sunrise Trek","nature",  350, 5.0, "Start at 2 AM. Guide required. Sunrise unforgettable."),
            Attraction("Uluwatu Temple",         "culture",   50, 1.5, "Clifftop temple with Kecak fire dance at dusk."),
            Attraction("Seminyak Beach",         "beach",     0, 3.0, "Best beach clubs: Potato Head, Ku De Ta."),
            Attraction("Tirta Empul Temple",     "culture",   50, 1.5, "Holy spring water purification ritual. Bring sarong."),
            Attraction("Nusa Penida Day Trip",   "nature",   200, 8.0, "Kelingking Beach — most dramatic view in Bali."),
        ],
        tags=["beach","culture","nature","hiking","wellness"]
    ),

    "tokyo": City(
        name="Tokyo", country="Japan", flag="🇯🇵",
        climate="Temperate", cost_per_day=180,
        best_season="Mar–May (Cherry Blossom), Sep–Nov",
        transport_mode="Subway & JR Pass", timezone="JST (UTC+9)",
        hotels={
            "budget":   Hotel("Khaosan Tokyo Hostel",   "budget",   45, 2, ["Capsule Option","Common Area"]),
            "midrange": Hotel("Shinjuku Granbell Hotel","midrange", 140, 4, ["WiFi","Bar","City View"]),
            "luxury":   Hotel("The Peninsula Tokyo",   "luxury",   700, 5, ["Spa","Helicopter Pad","5 Restaurants"]),
            "boutique": Hotel("Trunk Hotel Shibuya",   "boutique", 300, 4, ["Social Lounge","Design Rooms","Rooftop"]),
        },
        attractions=[
            Attraction("Shibuya Crossing",         "culture",   0, 1.0, "Visit at night for full impact. Starbucks view famous."),
            Attraction("Senso-ji Temple",           "culture",   0, 1.5, "Asakusa district. Nakamise Shopping Street nearby."),
            Attraction("teamLab Borderless",        "culture", 3200, 2.5, "Book months ahead. Immersive digital art."),
            Attraction("Tsukiji Outer Market",      "food",      0, 2.0, "Best sushi breakfast at 6 AM. Omakase counters."),
            Attraction("Shinjuku Gyoen Garden",     "nature",   500, 2.0, "Best cherry blossom spot. Peaceful urban escape."),
            Attraction("Akihabara Electric Town",   "shopping",  0, 2.5, "Anime, gaming, electronics wonderland."),
            Attraction("Tokyo Skytree",             "culture",2100, 1.5, "Buy tickets online. Views reach Mt. Fuji on clear days."),
            Attraction("Harajuku Takeshita Street", "culture",   0, 1.5, "Fashion subcultures. Crepe shops everywhere."),
            Attraction("Meiji Jingu Shrine",        "culture",   0, 1.0, "Forested sanctuary in central Tokyo. Very serene."),
        ],
        tags=["culture","food","shopping","nightlife","photography","anime"]
    ),

    "rome": City(
        name="Rome", country="Italy", flag="🇮🇹",
        climate="Mediterranean", cost_per_day=170,
        best_season="Apr–Jun, Sep–Oct", transport_mode="Bus & Walking",
        timezone="CET (UTC+1)",
        hotels={
            "budget":   Hotel("Alessandro Palace Hostel","budget",  50, 2, ["Rooftop Bar","Tours"]),
            "midrange": Hotel("Hotel Capo d'Africa",    "midrange",155, 4, ["Rooftop Pool","Colosseum View"]),
            "luxury":   Hotel("Hotel de Russie",        "luxury",  680, 5, ["Secret Garden","Spa","Le Jardin de Russie"]),
            "boutique": Hotel("Portrait Roma",          "boutique",420, 5, ["Piazza di Spagna Views","Salvatore Ferragamo"]),
        },
        attractions=[
            Attraction("Colosseum & Roman Forum",   "culture",  18, 3.5, "Book combined ticket. Avoid midday heat."),
            Attraction("Vatican Museums & Sistine Chapel","culture",20,4.0,"Book 6+ weeks ahead. Join early-morning tour."),
            Attraction("Trevi Fountain",            "culture",   0, 0.5, "Visit at midnight to avoid the crowds."),
            Attraction("Pantheon",                  "culture",   5, 1.0, "Free on Sundays. Engineering marvel — 2000 years old."),
            Attraction("Borghese Gallery",          "culture",  15, 2.0, "Timed tickets mandatory. Bernini sculptures unmissable."),
            Attraction("Trastevere Neighborhood",   "culture",   0, 2.5, "Medieval alleyways. Best neighbourhood for dinner."),
            Attraction("Campo de' Fiori Market",    "food",      0, 1.0, "Morning market. Fresh produce, flowers, street food."),
            Attraction("Palatine Hill",             "culture",  18, 1.5, "Best views over the Forum. Included in Colosseum ticket."),
        ],
        tags=["culture","food","history","photography","romance"]
    ),

    "santorini": City(
        name="Santorini", country="Greece", flag="🇬🇷",
        climate="Mediterranean", cost_per_day=220,
        best_season="May–Oct", transport_mode="ATV & Bus & Cable Car",
        timezone="EET (UTC+2)",
        hotels={
            "budget":   Hotel("Fira Backpackers",        "budget",  55, 2, ["Pool","Caldera Views"]),
            "midrange": Hotel("Katikies Cliff Side",    "midrange",280, 4, ["Infinity Pool","Breakfast","Sea View"]),
            "luxury":   Hotel("Mystique Hotel Santorini","luxury",  900, 5, ["Plunge Pools","Thalasso Spa","Iconic Suites"]),
            "boutique": Hotel("Andronis Boutique Hotel","boutique", 500, 5, ["Cave Suites","Private Terrace","Sunset Views"]),
        },
        attractions=[
            Attraction("Oia Sunset Viewpoint",      "photography",0, 2.0, "Arrive 2 hours early for a good spot. Worth every minute."),
            Attraction("Akrotiri Ruins",             "culture",   14, 2.0, "Bronze Age Pompeii. Well-preserved — visually stunning."),
            Attraction("Red Beach",                  "beach",      0, 2.0, "15-min walk from Akrotiri. Dramatic red volcanic cliffs."),
            Attraction("Caldera Boat Tour",          "nature",    80, 4.0, "Sail to volcano, hot springs, and Thirassia island."),
            Attraction("Santorini Wine Tour",        "food",      50, 3.0, "Visit Santo Wines & Venetsanos. Assyrtiko wine tasting."),
            Attraction("Pyrgos Village",             "culture",    0, 1.5, "Highest point on island. Authentic non-touristy experience."),
            Attraction("Perissa Black Sand Beach",  "beach",      0, 3.0, "Volcanic black sand. Many beach bars and tavernas."),
        ],
        tags=["beach","photography","food","romance","sunsets"]
    ),

    "kyoto": City(
        name="Kyoto", country="Japan", flag="🇯🇵",
        climate="Temperate", cost_per_day=160,
        best_season="Mar–May (Sakura), Oct–Nov (Koyo)",
        transport_mode="Bus & Bicycle", timezone="JST (UTC+9)",
        hotels={
            "budget":   Hotel("Piece Hostel Kyoto",    "budget",   40, 2, ["Bike Rental","Common Kitchen"]),
            "midrange": Hotel("Hotel Granvia Kyoto",  "midrange", 130, 4, ["Station Access","Restaurants"]),
            "luxury":   Hotel("Aman Kyoto",           "luxury",  1200, 5, ["Secret Garden","Onsen","Forest Retreat"]),
            "boutique": Hotel("Tawaraya Ryokan",      "boutique", 650, 5, ["Traditional Kaiseki","Tatami Rooms","800 Years Old"]),
        },
        attractions=[
            Attraction("Fushimi Inari Taisha",     "culture",   0, 3.0, "10,000 torii gates. Go at 6 AM — trails empty and magical."),
            Attraction("Arashiyama Bamboo Grove",  "nature",    0, 1.5, "Arrive before 7 AM. Stunning, meditative walk."),
            Attraction("Kinkaku-ji (Gold Pavilion)","culture", 500, 1.0, "Zen temple coated in gold leaf. Reflective pond iconic."),
            Attraction("Gion Geisha District",     "culture",   0, 2.0, "Evening stroll on Hanamikoji Street. Spot real Maiko."),
            Attraction("Nishiki Market",            "food",      0, 2.0, "Kyoto's Kitchen — 400-year-old covered market."),
            Attraction("Philosopher's Path",        "nature",    0, 1.5, "2km canal walk lined with cherry trees."),
            Attraction("Nijo Castle",              "culture",  800, 2.0, "Shogun palace with 'nightingale floors' — no nails used."),
            Attraction("Ryoan-ji Zen Garden",      "culture",  600, 1.0, "Most famous karesansui rock garden in Japan."),
        ],
        tags=["culture","photography","nature","food","tradition"]
    ),

    "new_york": City(
        name="New York", country="USA", flag="🇺🇸",
        climate="Continental", cost_per_day=250,
        best_season="Apr–Jun, Sep–Nov", transport_mode="Subway & Walking",
        timezone="EST (UTC−5)",
        hotels={
            "budget":   Hotel("The Local NYC",       "budget",   80, 3, ["Bar","LIC Location","Skyline View"]),
            "midrange": Hotel("Hotel Indigo LIC",   "midrange", 200, 4, ["Rooftop Pool","Manhattan Views"]),
            "luxury":   Hotel("The Plaza Hotel",    "luxury",   900, 5, ["Central Park Views","Eloise Suite","Afternoon Tea"]),
            "boutique": Hotel("The NoMad Hotel",    "boutique", 450, 5, ["Rooftop Bar","Library Lounge","NoMad Restaurant"]),
        },
        attractions=[
            Attraction("Central Park",              "nature",    0, 3.0, "Rent a rowboat. Strawberry Fields. Belvedere Castle."),
            Attraction("Metropolitan Museum of Art","culture",   30, 4.0, "Temple of Dendur, Egyptian Wing, Rooftop Garden."),
            Attraction("Brooklyn Bridge Walk",      "photography",0,1.5, "Walk Manhattan→Brooklyn. Best views from DUMBO afterward."),
            Attraction("Statue of Liberty & Ellis Island","culture",25,4.0,"Book crown tickets months ahead."),
            Attraction("MoMA",                      "culture",   30, 3.0, "Picasso, Warhol, Van Gogh's Starry Night."),
            Attraction("High Line Park",            "culture",    0, 2.0, "Elevated rail-to-park. Beautiful gardens and food stalls."),
            Attraction("Times Square",              "culture",    0, 1.0, "Overwhelming but unmissable. Better at midnight."),
            Attraction("One World Trade & 9/11 Memorial","culture",33,2.5,"Emotional and important. Book in advance."),
        ],
        tags=["culture","food","shopping","nightlife","photography"]
    ),

    "machu_picchu": City(
        name="Machu Picchu", country="Peru", flag="🇵🇪",
        climate="Highland Subtropical", cost_per_day=120,
        best_season="May–Sep (Dry Season)", transport_mode="Train & Bus",
        timezone="PET (UTC−5)",
        hotels={
            "budget":   Hotel("Hatun Inti Lodge",          "budget",   40, 2, ["Mountain Views","Breakfast"]),
            "midrange": Hotel("El Mapi Hotel Aguas Calientes","midrange",120,4,["Rooftop Terrace","Pool"]),
            "luxury":   Hotel("Belmond Sanctuary Lodge",  "luxury",   700, 5, ["Only Hotel At Ruins Gate","Garden","Pool"]),
            "boutique": Hotel("Inkaterra Machu Picchu",   "boutique", 350, 4, ["Cloud Forest","Orchid Garden","Birdwatching"]),
        },
        attractions=[
            Attraction("Machu Picchu Citadel",     "culture",   152, 4.0, "Buy government tickets weeks ahead. 2 entries per ticket."),
            Attraction("Sun Gate (Inti Punku)",     "hiking",      0, 3.0, "3-hour round trip from citadel. Sunrise view of Machu Picchu."),
            Attraction("Huayna Picchu Trek",        "hiking",     88, 4.0, "Very steep. Only 400 spots daily — book months ahead."),
            Attraction("Sacred Valley Tour",        "culture",    80, 8.0, "Pisac Market, Ollantaytambo fortress, Moray Terraces."),
            Attraction("Rainbow Mountain (Vinicunca)","nature",  30, 8.0, "Day trip from Cusco. Altitude 5,200m — acclimatise first."),
            Attraction("Aguas Calientes Town",     "culture",     0, 2.0, "Hot springs, local markets, fresh trout restaurants."),
        ],
        tags=["hiking","nature","culture","photography","adventure"]
    ),

}

# Origin cities (departure only — no full tourism data needed)
ORIGIN_CITIES = {
    "new_york":  {"name": "New York",  "flag": "🗽", "country": "USA"},
    "london":    {"name": "London",    "flag": "🎡", "country": "UK"},
    "tokyo":     {"name": "Tokyo",     "flag": "🗼", "country": "Japan"},
    "paris":     {"name": "Paris",     "flag": "🗼", "country": "France"},
    "sydney":    {"name": "Sydney",    "flag": "🦘", "country": "Australia"},
    "dubai":     {"name": "Dubai",     "flag": "🏙️", "country": "UAE"},
}

DESTINATION_IDS = list(CITIES.keys())
ORIGIN_IDS = list(ORIGIN_CITIES.keys())

ALL_CITY_NAMES = {k: v["name"] if isinstance(v, dict) else v.name
                  for k, v in {**ORIGIN_CITIES,
                                **{k: v for k, v in CITIES.items()}}.items()}
