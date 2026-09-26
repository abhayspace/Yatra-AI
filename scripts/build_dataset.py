"""Generates data/destinations.json.

The curated part (attractions, restaurants, stay and food rates) is written out by hand
below. The origin -> destination fare table is derived from great-circle distance with
simple per-mode rate formulas, so every origin/destination pair has consistent numbers.
All figures are rough, rounded, INR estimates for a typical mid-season week. They are
illustrative planning numbers, not live fares or prices.

Run:  python scripts/build_dataset.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "destinations.json"

# name -> (lat, lon, aliases)
ORIGINS: dict[str, tuple[float, float, list[str]]] = {
    "Delhi": (28.61, 77.21, ["new delhi", "ncr", "gurgaon", "gurugram", "noida", "delhi ncr"]),
    "Mumbai": (19.08, 72.88, ["bombay", "navi mumbai", "thane"]),
    "Bengaluru": (12.97, 77.59, ["bangalore", "bengaluru"]),
    "Kolkata": (22.57, 88.36, ["calcutta"]),
    "Chennai": (13.08, 80.27, ["madras"]),
    "Hyderabad": (17.39, 78.49, ["secunderabad"]),
    "Pune": (18.52, 73.86, ["poona"]),
    "Ahmedabad": (23.02, 72.57, ["amdavad"]),
    "Jaipur": (26.91, 75.79, []),
    "Lucknow": (26.85, 80.95, []),
    "Chandigarh": (30.73, 76.78, ["mohali", "panchkula"]),
    "Kochi": (9.93, 76.27, ["cochin", "ernakulam"]),
    "Guwahati": (26.14, 91.74, []),
    "Nagpur": (21.15, 79.09, []),
    "Bhopal": (23.26, 77.41, []),
}

# Attraction tuple: slug, name, type, themes, hours, cost_pp, indoor, best_time, area, note
A = tuple
# Restaurant tuple: slug, name, cuisine, meals, tier, cost_pp, signature, area
R = tuple

DESTINATIONS: list[dict] = [
    {
        "id": "goa", "name": "Goa", "state": "Goa", "region": "West Coast",
        "aliases": ["north goa", "south goa", "panjim", "panaji", "calangute", "baga"],
        "lat": 15.4989, "lon": 73.8278,
        "tagline": "Beaches, Portuguese-era lanes and a serious seafood scene.",
        "best_months": [11, 12, 1, 2, 3], "avoid_months": [6, 7, 8],
        "avoid_reason": "monsoon: heavy rain, rough seas and many beach shacks closed",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 400, "air_surcharge": 0},
        "stay": {"budget": 1600, "mid": 4200, "premium": 11000},
        "breakfast_pp": {"budget": 150, "mid": 300, "premium": 700},
        "generic_meal_pp": {"budget": 300, "mid": 600, "premium": 1400},
        "local_transport_per_day": 800,
        "attractions": [
            A(("baga-watersports", "Baga Beach and water sports", "beach", ["beach", "adventure"], 3, 1200, False, "afternoon", "North Goa", "Parasailing, jet-ski and banana-boat packages")),
            A(("anjuna-market", "Anjuna flea market", "shopping", ["shopping", "culture"], 2, 0, False, "afternoon", "North Goa", "Wednesday market: boho clothes, spices, souvenirs")),
            A(("aguada-fort", "Fort Aguada and Sinquerim sunset", "heritage", ["heritage", "nature"], 2, 50, False, "evening", "North Goa", "17th-century Portuguese fort with a lighthouse")),
            A(("old-goa", "Old Goa churches", "heritage", ["heritage", "culture", "spiritual"], 2.5, 0, False, "morning", "Old Goa", "Basilica of Bom Jesus and Se Cathedral, UNESCO sites")),
            A(("fontainhas", "Fontainhas Latin Quarter walk", "culture", ["culture", "heritage", "food"], 2, 500, False, "morning", "Panjim", "Guided walk through painted Portuguese-era lanes with bakery stops")),
            A(("dudhsagar", "Dudhsagar Falls jeep safari", "nature", ["nature", "adventure", "wildlife"], 6, 900, False, "morning", "South Goa", "Jeep ride through Mollem forest to a four-tier waterfall")),
            A(("palolem", "Palolem beach and kayaking", "beach", ["beach", "nature", "relaxation"], 4, 600, False, "any", "South Goa", "Crescent bay with calm water and dolphin-spotting boats")),
            A(("spice-plantation", "Spice plantation tour with lunch", "nature", ["nature", "food"], 3, 700, False, "morning", "Ponda", "Walk a working plantation and eat a Goan thali on banana leaf")),
            A(("goan-cooking-class", "Goan cooking class", "food", ["food", "culture"], 3, 1800, True, "afternoon", "Assagao", "Hands-on class: xacuti, prawn balchao, bebinca")),
            A(("mandovi-cruise", "Mandovi river sunset cruise", "relaxation", ["relaxation", "nightlife", "culture"], 1.5, 500, False, "evening", "Panjim", "Live Goan folk music on a river cruise")),
            A(("cabo-de-rama", "Cabo de Rama fort and cliffs", "nature", ["nature", "heritage"], 3, 0, False, "afternoon", "South Goa", "Quiet clifftop fort and a secluded beach below")),
            A(("arpora-bazaar", "Saturday Night Bazaar, Arpora", "nightlife", ["nightlife", "shopping", "food"], 3, 200, False, "evening", "North Goa", "Night market with live music and street food")),
            A(("ayurveda-spa", "Ayurvedic massage session", "wellness", ["wellness", "relaxation"], 1.5, 1800, True, "afternoon", "North Goa", "Traditional abhyanga massage")),
        ],
        "restaurants": [
            R(("vinayak", "Vinayak Family Restaurant", "Goan", ["lunch", "dinner"], "budget", 450, "Chicken cafreal and fish thali", "Assagao")),
            R(("ritz-classic", "Ritz Classic", "Goan thali", ["lunch"], "budget", 350, "Goan fish curry-rice thali", "Panjim")),
            R(("fishermans-wharf", "Fisherman's Wharf", "Goan seafood", ["dinner", "lunch"], "mid", 900, "Butter-garlic prawns", "Cavelossim")),
            R(("britto", "Britto's", "Seafood", ["lunch", "dinner"], "mid", 800, "Fish recheado and beach-side seafood platter", "Baga")),
            R(("cafe-bodega", "Cafe Bodega", "Cafe", ["lunch"], "mid", 700, "Sourdough sandwiches and cold brew in a heritage house", "Panjim")),
            R(("gunpowder", "Gunpowder", "Kerala and South Indian", ["dinner"], "mid", 1000, "Appam with stew, Kerala fish curry", "Assagao")),
            R(("thalassa", "Thalassa", "Greek", ["dinner"], "premium", 1800, "Sunset-view mezze and grilled seafood", "Vagator")),
            R(("martins-corner", "Martin's Corner", "Goan seafood", ["dinner"], "premium", 1500, "Kingfish rawa fry and crab xec xec", "Betalbatim")),
        ],
    },
    {
        "id": "kerala", "name": "Kerala (Kochi, Munnar, Alleppey)", "state": "Kerala", "region": "South India",
        "aliases": ["munnar", "alleppey", "alappuzha", "kochi", "cochin", "backwaters", "kumarakom", "god's own country"],
        "lat": 10.0889, "lon": 77.0595,
        "tagline": "Tea-covered hills, backwater houseboats and a spice-driven cuisine.",
        "best_months": [9, 10, 11, 12, 1, 2, 3], "avoid_months": [6, 7],
        "avoid_reason": "peak monsoon: landslides in the hills and rough backwater conditions",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 500, "air_surcharge": 0},
        "stay": {"budget": 1800, "mid": 4500, "premium": 12000},
        "breakfast_pp": {"budget": 150, "mid": 350, "premium": 800},
        "generic_meal_pp": {"budget": 300, "mid": 650, "premium": 1500},
        "local_transport_per_day": 1800,
        "attractions": [
            A(("munnar-tea", "Tea plantation walk and factory visit", "nature", ["nature", "food"], 3, 300, False, "morning", "Munnar", "Kolukkumalai or Kanan Devan estate walk with tea tasting")),
            A(("eravikulam", "Eravikulam National Park", "nature", ["nature", "wildlife"], 3, 400, False, "morning", "Munnar", "Nilgiri tahr sightings and rolling grassland")),
            A(("top-station", "Top Station viewpoint", "nature", ["nature", "relaxation"], 2, 100, False, "afternoon", "Munnar", "Panoramic view over the Western Ghats")),
            A(("mattupetty", "Mattupetty Dam boating", "nature", ["nature", "relaxation"], 1.5, 350, False, "afternoon", "Munnar", "Speedboat and pedal boats on a hill reservoir")),
            A(("alleppey-houseboat", "Alleppey houseboat backwater cruise", "relaxation", ["relaxation", "nature", "food"], 6, 3500, False, "any", "Alleppey", "Day cruise on a kettuvallam with a Kerala lunch on board")),
            A(("kumarakom-birds", "Kumarakom bird sanctuary", "wildlife", ["wildlife", "nature"], 2.5, 200, False, "morning", "Kumarakom", "Migratory birds on Vembanad lake")),
            A(("fort-kochi", "Fort Kochi heritage walk", "heritage", ["heritage", "culture"], 3, 300, False, "morning", "Kochi", "Chinese fishing nets, Dutch Palace, Jew Town")),
            A(("kathakali", "Kathakali performance", "culture", ["culture"], 1.5, 400, True, "evening", "Kochi", "Classical dance-drama with a green-room makeup demo")),
            A(("spice-market", "Mattancherry spice market and food walk", "food", ["food", "culture", "shopping"], 2.5, 900, False, "morning", "Kochi", "Guided tasting through spice merchants and local bakeries")),
            A(("kerala-cooking", "Kerala home-style cooking class", "food", ["food", "culture"], 3, 1500, True, "afternoon", "Alleppey", "Learn karimeen pollichathu, appam and thoran with a local family")),
            A(("ayurveda-kerala", "Ayurvedic massage and steam", "wellness", ["wellness", "relaxation"], 2, 2200, True, "afternoon", "Munnar", "Traditional abhyangam and shirodhara session")),
            A(("marari-beach", "Marari beach afternoon", "beach", ["beach", "relaxation"], 3, 0, False, "afternoon", "Alleppey", "Quiet fishing-village beach")),
        ],
        "restaurants": [
            R(("saravana-munnar", "Saravana Bhavan Munnar", "South Indian", ["breakfast", "lunch"], "budget", 250, "Idli, dosa and unlimited meals", "Munnar")),
            R(("rapsy", "Rapsy Restaurant", "Kerala", ["lunch", "dinner"], "budget", 400, "Parotta with beef or chicken roast", "Munnar")),
            R(("mayoori", "Mayoori Restaurant", "Kerala", ["lunch", "dinner"], "mid", 550, "Kerala fish meals", "Munnar")),
            R(("thaff", "Thaff Restaurant", "Kerala Malabar", ["lunch", "dinner"], "mid", 600, "Malabar biryani, karimeen fry", "Alleppey")),
            R(("kashi-art-cafe", "Kashi Art Cafe", "Cafe", ["lunch"], "mid", 700, "Baked goods and coffee in an art gallery", "Fort Kochi")),
            R(("dhe-puttu", "Dhe Puttu", "Kerala", ["lunch", "dinner"], "mid", 650, "Puttu with kadala curry", "Kochi")),
            R(("fry-fish", "Fry's Fish Curry House", "Kerala seafood", ["dinner"], "mid", 850, "Meen moilee and prawn masala", "Fort Kochi")),
            R(("fort-house", "Fort House Waterfront", "Seafood", ["dinner"], "premium", 1600, "Waterfront grilled seafood", "Fort Kochi")),
        ],
    },
    {
        "id": "rishikesh", "name": "Rishikesh", "state": "Uttarakhand", "region": "Himalayan foothills",
        "aliases": ["haridwar", "tapovan", "laxman jhula", "yoga capital", "uttarakhand"],
        "lat": 30.0869, "lon": 78.2676,
        "tagline": "River rafting, ashrams and Ganga aarti at the edge of the Himalaya.",
        "best_months": [2, 3, 4, 9, 10, 11], "avoid_months": [7, 8],
        "avoid_reason": "monsoon: rafting is suspended and roads can flood",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 150, "air_surcharge": 0},
        "stay": {"budget": 1200, "mid": 3200, "premium": 9000},
        "breakfast_pp": {"budget": 120, "mid": 250, "premium": 600},
        "generic_meal_pp": {"budget": 250, "mid": 500, "premium": 1100},
        "local_transport_per_day": 600,
        "attractions": [
            A(("jhulas", "Laxman Jhula and Ram Jhula walk", "spiritual", ["spiritual", "culture"], 1.5, 0, False, "morning", "Tapovan", "Iconic suspension bridges over the Ganga")),
            A(("ganga-aarti", "Ganga aarti at Triveni Ghat", "spiritual", ["spiritual", "culture"], 1.5, 0, False, "evening", "Triveni Ghat", "Evening lamp ceremony on the riverbank")),
            A(("rafting", "River rafting, Shivpuri to Rishikesh", "adventure", ["adventure", "nature"], 3, 1100, False, "morning", "Shivpuri", "16 km guided run through Grade II-III rapids")),
            A(("neer-garh", "Neer Garh waterfall trek", "nature", ["nature", "adventure"], 2.5, 100, False, "morning", "Lakshman Jhula", "Short forest trail to a tiered waterfall")),
            A(("beatles-ashram", "Beatles Ashram (Chaurasi Kutia)", "heritage", ["heritage", "culture", "nature"], 2, 150, False, "morning", "Muni ki Reti", "Graffiti-covered ruins in a forest reserve")),
            A(("yoga-class", "Morning yoga class at an ashram", "wellness", ["wellness", "spiritual", "relaxation"], 1.5, 400, False, "morning", "Tapovan", "Drop-in hatha and pranayama session")),
            A(("kunjapuri", "Kunjapuri Devi sunrise viewpoint", "nature", ["nature", "spiritual"], 3, 300, False, "morning", "Kunjapuri", "Sunrise over the Himalayan range from a hilltop temple")),
            A(("cafe-hopping", "Tapovan cafe hopping", "food", ["food", "relaxation"], 2, 0, True, "afternoon", "Tapovan", "Riverside cafes and bakeries")),
            A(("rajaji", "Rajaji National Park jungle safari", "wildlife", ["wildlife", "nature", "adventure"], 3.5, 1500, False, "morning", "Chilla", "Jeep safari, elephant and deer sightings")),
            A(("haridwar-har-ki-pauri", "Har Ki Pauri evening, Haridwar", "spiritual", ["spiritual", "culture"], 3, 300, False, "evening", "Haridwar", "Larger aarti ceremony a short drive away")),
            A(("bungee", "Giant swing and flying fox", "adventure", ["adventure"], 2, 3500, False, "morning", "Mohan Chatti", "India's highest fixed-platform bungee jump area")),
        ],
        "restaurants": [
            R(("chotiwala", "Chotiwala", "North Indian vegetarian", ["lunch", "dinner"], "budget", 250, "Thali and jalebi", "Swarg Ashram")),
            R(("madras-cafe", "Madras Cafe", "South Indian", ["breakfast", "lunch"], "budget", 250, "Filter coffee and masala dosa", "Tapovan")),
            R(("little-buddha", "Little Buddha Cafe", "Tibetan and continental", ["lunch", "dinner"], "mid", 550, "Thukpa and momos with a river view", "Laxman Jhula")),
            R(("beatles-cafe", "The Beatles Cafe", "Continental", ["lunch", "dinner"], "mid", 650, "Wood-fired pizza and banana pancakes", "Laxman Jhula")),
            R(("pyramid-cafe", "Pyramid Cafe", "Multi-cuisine", ["lunch", "dinner"], "mid", 600, "Israeli breakfast and falafel", "Tapovan")),
            R(("ramanas", "Ramana's Organic Cafe", "Healthy vegetarian", ["lunch"], "mid", 500, "Organic bowls and fresh juices", "Tapovan")),
            R(("ganga-view", "Ganga Beach Cafe", "Multi-cuisine", ["dinner"], "mid", 700, "Riverside dinner on the sands", "Ram Jhula")),
            R(("the-glasshouse", "The Glasshouse on the Ganges", "Continental", ["dinner"], "premium", 1600, "Fine dining with a river deck", "Kaudiyala")),
        ],
    },
    {
        "id": "manali", "name": "Manali", "state": "Himachal Pradesh", "region": "Himachal Pradesh",
        "aliases": ["himachal", "kullu", "solang", "old manali", "atal tunnel", "kasol"],
        "lat": 32.2396, "lon": 77.1887,
        "tagline": "Snow peaks, pine forests, cafes and easy adventure in the Beas valley.",
        "best_months": [3, 4, 5, 6, 9, 10, 12], "avoid_months": [7, 8],
        "avoid_reason": "monsoon: landslides and road closures on the Kullu-Manali highway",
        "access": {"rail": False, "air": True, "bus": True, "last_mile_pp": 300, "air_surcharge": 800},
        "stay": {"budget": 1400, "mid": 3800, "premium": 10000},
        "breakfast_pp": {"budget": 150, "mid": 300, "premium": 650},
        "generic_meal_pp": {"budget": 300, "mid": 600, "premium": 1300},
        "local_transport_per_day": 1500,
        "attractions": [
            A(("hadimba", "Hadimba Devi Temple and cedar forest", "spiritual", ["spiritual", "culture", "nature"], 1.5, 0, False, "morning", "Manali", "Wooden pagoda-style temple inside a deodar forest")),
            A(("old-manali", "Old Manali cafe trail", "food", ["food", "relaxation", "culture"], 2.5, 0, True, "afternoon", "Old Manali", "Bakeries and riverside cafes")),
            A(("solang", "Solang Valley activities", "adventure", ["adventure", "nature"], 4, 1500, False, "morning", "Solang", "Paragliding, zorbing or snow play depending on season")),
            A(("atal-tunnel", "Atal Tunnel and Sissu", "nature", ["nature", "adventure"], 5, 800, False, "morning", "Lahaul", "Drive through the world's longest highway tunnel above 10,000 ft")),
            A(("jogini-falls", "Jogini Waterfall trek", "nature", ["nature"], 3, 0, False, "morning", "Vashisht", "Trail to a Himalayan waterfall")),
            A(("vashisht-springs", "Vashisht hot springs", "wellness", ["wellness", "relaxation", "culture"], 1.5, 50, False, "afternoon", "Vashisht", "Natural sulphur springs beside an old temple")),
            A(("beas-rafting", "Beas river rafting", "adventure", ["adventure", "nature"], 2, 800, False, "afternoon", "Kullu", "Short rafting run through the Kullu valley")),
            A(("mall-road", "Mall Road and Tibetan market", "shopping", ["shopping", "culture"], 2, 0, False, "evening", "Manali", "Woollens, shawls and street snacks")),
            A(("naggar-castle", "Naggar Castle and Roerich Art Gallery", "heritage", ["heritage", "culture"], 2.5, 100, True, "morning", "Naggar", "Medieval castle and the Roerich museum")),
            A(("manu-temple-hike", "Riverside picnic and easy walk at Manu Temple", "relaxation", ["relaxation", "nature"], 2, 0, False, "afternoon", "Old Manali", "Slow riverside walk and packed picnic")),
        ],
        "restaurants": [
            R(("mitthu-dhaba", "Mitthu Da Dhaba", "Punjabi", ["lunch", "dinner"], "budget", 350, "Butter chicken and dal makhani", "Manali")),
            R(("johnson-cafe", "Johnson's Cafe", "Continental", ["lunch", "dinner"], "mid", 900, "Trout fish and garden seating", "Manali")),
            R(("chopsticks", "Chopsticks", "Tibetan and Asian", ["lunch", "dinner"], "mid", 500, "Momos and thukpa", "Manali")),
            R(("drifters-cafe", "Drifter's Cafe", "Cafe", ["breakfast", "lunch"], "mid", 500, "Shakshuka and pancakes with a mountain view", "Old Manali")),
            R(("dylans", "Dylan's Toasted and Roasted", "Cafe", ["lunch"], "mid", 450, "Coffee and cheesecake", "Manali")),
            R(("casa-bella-vista", "Casa Bella Vista", "Italian", ["dinner"], "premium", 1400, "Wood-fired pizza and pasta", "Old Manali")),
            R(("himachali-rasoi", "Himachali Rasoi", "Himachali", ["lunch", "dinner"], "budget", 400, "Siddu, dham and madra", "Manali")),
            R(("the-lazy-dog", "The Lazy Dog", "Continental", ["dinner"], "premium", 1500, "Riverside fine dining", "Manali")),
        ],
    },
    {
        "id": "jaipur", "name": "Jaipur", "state": "Rajasthan", "region": "Rajasthan",
        "aliases": ["pink city", "rajasthan", "amer", "amber"],
        "lat": 26.9124, "lon": 75.7873,
        "tagline": "Forts, palaces, bazaars and a rich Rajasthani food tradition.",
        "best_months": [10, 11, 12, 1, 2, 3], "avoid_months": [5, 6],
        "avoid_reason": "extreme summer heat above 42°C",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 100, "air_surcharge": 0},
        "stay": {"budget": 1300, "mid": 3600, "premium": 10500},
        "breakfast_pp": {"budget": 150, "mid": 350, "premium": 800},
        "generic_meal_pp": {"budget": 250, "mid": 600, "premium": 1400},
        "local_transport_per_day": 1200,
        "attractions": [
            A(("amer-fort", "Amber Fort", "heritage", ["heritage", "culture"], 3, 200, False, "morning", "Amer", "Hilltop fort with the Sheesh Mahal mirror hall")),
            A(("city-palace", "City Palace and Jantar Mantar", "heritage", ["heritage", "culture"], 3, 700, True, "afternoon", "Old City", "Royal residence museum and the UNESCO astronomical observatory")),
            A(("hawa-mahal", "Hawa Mahal photo stop", "heritage", ["heritage"], 1, 50, False, "morning", "Old City", "The Palace of Winds facade")),
            A(("nahargarh", "Nahargarh Fort sunset", "nature", ["nature", "heritage", "relaxation"], 2.5, 200, False, "evening", "Nahargarh", "Sunset view over the city")),
            A(("johari-bazaar", "Johari and Bapu Bazaar shopping", "shopping", ["shopping", "culture"], 3, 0, False, "afternoon", "Old City", "Block-print textiles, jewellery and juttis")),
            A(("chokhi-dhani", "Chokhi Dhani village evening", "culture", ["culture", "food"], 3, 900, False, "evening", "Tonk Road", "Folk dance, puppetry and a traditional thali")),
            A(("food-walk", "Old City Rajasthani food walk", "food", ["food", "culture"], 3, 1200, False, "morning", "Old City", "Kachori, ghewar, lassi and mirchi vada with a local guide")),
            A(("jaigarh", "Jaigarh Fort and the world's largest cannon on wheels", "heritage", ["heritage"], 2, 150, False, "afternoon", "Amer", "Fort above Amber with panoramic views")),
            A(("elefun", "Elephant sanctuary visit", "wildlife", ["wildlife", "nature"], 2, 1000, False, "morning", "Amer", "Ethical elephant-care visit; no rides")),
            A(("block-print", "Block-printing workshop", "culture", ["culture", "shopping"], 2.5, 700, True, "afternoon", "Sanganer", "Print your own fabric with local artisans")),
            A(("patrika-gate", "Patrika Gate and Jawahar Circle Garden", "relaxation", ["relaxation", "nature"], 1.5, 0, False, "evening", "Malviya Nagar", "Colourful gate and a landscaped garden")),
        ],
        "restaurants": [
            R(("lmb", "Laxmi Misthan Bhandar (LMB)", "Rajasthani vegetarian", ["lunch", "dinner"], "mid", 500, "Dal baati churma and ghewar", "Johari Bazaar")),
            R(("rawat-misthan", "Rawat Misthan Bhandar", "Rajasthani", ["breakfast", "lunch"], "budget", 200, "Pyaaz kachori", "Station Road")),
            R(("handi", "Handi Restaurant", "Mughlai", ["lunch", "dinner"], "mid", 650, "Laal maas and butter chicken", "MI Road")),
            R(("spice-court", "Spice Court", "Rajasthani", ["dinner"], "mid", 850, "Laal maas and gatte ki sabzi", "Bani Park")),
            R(("tapri", "Tapri Central", "Cafe", ["breakfast", "lunch"], "mid", 450, "Chai and snacks with a city view", "C-Scheme")),
            R(("suvarna-mahal", "Suvarna Mahal", "Royal Rajasthani", ["dinner"], "premium", 2200, "Royal thali in a palace hotel", "Rambagh Palace")),
            R(("chokhi-thali", "Chokhi Dhani Thali", "Rajasthani", ["dinner"], "mid", 800, "Village-style thali", "Tonk Road")),
            R(("nibs-cafe", "Nibs Cafe", "Cafe", ["lunch"], "mid", 500, "Sandwiches and coffee", "Malviya Nagar")),
        ],
    },
    {
        "id": "udaipur", "name": "Udaipur", "state": "Rajasthan", "region": "Rajasthan",
        "aliases": ["city of lakes", "lake pichola", "rajasthan"],
        "lat": 24.5854, "lon": 73.7125,
        "tagline": "Lakeside palaces, sunset boat rides and a romantic old town.",
        "best_months": [10, 11, 12, 1, 2, 3], "avoid_months": [5, 6],
        "avoid_reason": "summer heat above 40°C",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 100, "air_surcharge": 0},
        "stay": {"budget": 1500, "mid": 4000, "premium": 12000},
        "breakfast_pp": {"budget": 150, "mid": 350, "premium": 800},
        "generic_meal_pp": {"budget": 280, "mid": 650, "premium": 1500},
        "local_transport_per_day": 1000,
        "attractions": [
            A(("city-palace-udaipur", "City Palace complex", "heritage", ["heritage", "culture"], 2.5, 400, True, "morning", "Old City", "Palace museum over Lake Pichola")),
            A(("pichola-boat", "Lake Pichola sunset boat ride", "relaxation", ["relaxation", "nature", "heritage"], 1.5, 500, False, "evening", "Lake Pichola", "Boat past Jag Mandir and the Lake Palace")),
            A(("saheliyon-ki-bari", "Saheliyon ki Bari garden", "nature", ["nature", "relaxation", "heritage"], 1.5, 50, False, "morning", "Old City", "Fountain garden built for royal ladies")),
            A(("monsoon-palace", "Monsoon Palace sunset", "nature", ["nature", "heritage"], 2, 200, False, "evening", "Sajjangarh", "Hilltop palace with valley views")),
            A(("bagore-dance", "Bagore Ki Haveli folk dance show", "culture", ["culture"], 1.5, 150, True, "evening", "Gangaur Ghat", "Rajasthani folk dance and puppet show")),
            A(("jagdish-temple", "Jagdish Temple and old-town lanes", "spiritual", ["spiritual", "culture", "shopping"], 2, 0, False, "morning", "Old City", "Indo-Aryan temple and nearby art shops")),
            A(("kumbhalgarh", "Kumbhalgarh Fort day trip", "heritage", ["heritage", "nature", "adventure"], 6, 1500, False, "morning", "Kumbhalgarh", "Great wall of India, 80 km away")),
            A(("food-walk-udaipur", "Udaipur street food walk", "food", ["food", "culture"], 2.5, 900, False, "afternoon", "Old City", "Dal baati, mirchi bada and kulfi with a guide")),
            A(("cooking-udaipur", "Rajasthani cooking class", "food", ["food", "culture"], 3, 1500, True, "afternoon", "Old City", "Learn laal maas and dal baati at a family home")),
            A(("shilpgram", "Shilpgram craft village", "culture", ["culture", "shopping"], 2.5, 100, False, "afternoon", "Shilpgram", "Rural arts and crafts complex")),
            A(("fatehsagar", "Fateh Sagar lakefront evening", "relaxation", ["relaxation", "nature"], 2, 0, False, "evening", "Fateh Sagar", "Promenade with corn and street snacks")),
        ],
        "restaurants": [
            R(("natraj", "Natraj Dining Hall", "Rajasthani thali", ["lunch", "dinner"], "budget", 350, "Unlimited Rajasthani thali", "Old City")),
            R(("ambrai", "Ambrai", "Indian", ["dinner"], "premium", 1800, "Lakeside dinner with a palace view", "Amet Haveli")),
            R(("upre", "Upre by 1559 AD", "Multi-cuisine", ["dinner"], "premium", 1600, "Rooftop dinner facing the Pichola", "Old City")),
            R(("millets-of-mewar", "Millets of Mewar", "Rajasthani millet cuisine", ["lunch", "dinner"], "mid", 650, "Millet thali and traditional sweets", "Old City")),
            R(("edelweiss", "Edelweiss Cafe", "Cafe", ["breakfast", "lunch"], "mid", 500, "European bakes and coffee", "Old City")),
            R(("garden-cafe", "Jheel's Ginger Coffee Bar", "Cafe", ["lunch"], "mid", 450, "Sandwiches and coffee on the lake", "Lal Ghat")),
            R(("raj-bhog", "Raj Bhog", "Rajasthani vegetarian", ["lunch", "dinner"], "budget", 400, "Bajra roti and ker sangri", "Old City")),
        ],
    },
    {
        "id": "darjeeling", "name": "Darjeeling", "state": "West Bengal", "region": "Eastern Himalaya",
        "aliases": ["kalimpong", "toy train", "tiger hill", "north bengal"],
        "lat": 27.0410, "lon": 88.2663,
        "tagline": "Tea gardens, the toy train and Kanchenjunga at sunrise.",
        "best_months": [3, 4, 5, 10, 11], "avoid_months": [6, 7, 8],
        "avoid_reason": "monsoon: heavy rain, clouds hide the peaks and landslides are common",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 700, "air_surcharge": 0},
        "stay": {"budget": 1300, "mid": 3500, "premium": 9500},
        "breakfast_pp": {"budget": 130, "mid": 300, "premium": 650},
        "generic_meal_pp": {"budget": 250, "mid": 550, "premium": 1200},
        "local_transport_per_day": 1400,
        "attractions": [
            A(("tiger-hill", "Tiger Hill sunrise", "nature", ["nature", "relaxation"], 3, 350, False, "morning", "Ghum", "Sunrise over Kanchenjunga (weather permitting)")),
            A(("toy-train", "Darjeeling Himalayan Railway joyride", "heritage", ["heritage", "culture", "nature"], 2, 1500, False, "morning", "Darjeeling", "UNESCO-listed steam toy train to Ghum")),
            A(("happy-valley-tea", "Happy Valley Tea Estate tour", "nature", ["nature", "food"], 2, 200, False, "morning", "Darjeeling", "Factory tour and first-flush tasting")),
            A(("batasia", "Batasia Loop and Ghum Monastery", "culture", ["culture", "spiritual", "nature"], 2, 100, False, "afternoon", "Ghum", "War memorial loop and Tibetan Buddhist monastery")),
            A(("himalayan-zoo", "Padmaja Naidu Zoo and HMI", "wildlife", ["wildlife", "heritage", "nature"], 3, 400, False, "afternoon", "Darjeeling", "Red pandas, snow leopards and the mountaineering museum")),
            A(("mall-darj", "Chowrasta and the Mall", "shopping", ["shopping", "relaxation", "food"], 2, 0, False, "evening", "Darjeeling", "Promenade with tea shops and bookstores")),
            A(("rock-garden", "Rock Garden and Ganga Maya Park", "nature", ["nature", "relaxation"], 2.5, 100, False, "afternoon", "Chunnu Summer Falls", "Terraced garden around a waterfall")),
            A(("momo-walk", "Darjeeling momo and Tibetan food trail", "food", ["food", "culture"], 2.5, 700, True, "afternoon", "Darjeeling", "Momos, thukpa and butter tea")),
            A(("singalila", "Sandakphu day hike at Manebhanjan", "adventure", ["adventure", "nature"], 5, 800, False, "morning", "Manebhanjan", "Short section of the Singalila ridge trail")),
            A(("tibetan-refugee", "Tibetan Refugee Self-Help Centre", "culture", ["culture", "shopping"], 1.5, 0, True, "afternoon", "Darjeeling", "Handmade carpets and crafts")),
        ],
        "restaurants": [
            R(("glenary", "Glenary's", "Continental and bakery", ["breakfast", "lunch", "dinner"], "mid", 700, "Cakes and Darjeeling tea", "Mall Road")),
            R(("kunga", "Kunga Restaurant", "Tibetan", ["lunch", "dinner"], "budget", 300, "Thenthuk and momos", "Gandhi Road")),
            R(("sonam", "Sonam's Kitchen", "Tibetan", ["lunch", "dinner"], "budget", 350, "Butter tea and fried momo", "Darjeeling")),
            R(("keventers", "Keventer's", "Cafe", ["breakfast", "lunch"], "mid", 500, "Sausage breakfast and milkshakes", "Nehru Road")),
            R(("dekeva", "Dekeva", "Continental", ["dinner"], "mid", 700, "Wood-fired dishes", "Nehru Road")),
            R(("penang", "Penang Restaurant", "Chinese", ["dinner"], "mid", 650, "Hakka noodles and chilli chicken", "Nehru Road")),
            R(("the-elgin", "Elgin Tea Lounge", "Colonial", ["dinner"], "premium", 1800, "Heritage hotel high tea", "Elgin Hotel")),
            R(("hot-stimulating", "Hot Stimulating Cafe", "Cafe", ["lunch"], "mid", 400, "Cappuccino and cookies", "Darjeeling")),
        ],
    },
    {
        "id": "leh", "name": "Leh-Ladakh", "state": "Ladakh", "region": "Ladakh",
        "aliases": ["ladakh", "leh", "nubra", "pangong", "khardung la"],
        "lat": 34.1526, "lon": 77.5771,
        "tagline": "High-altitude monasteries, moonscapes and turquoise lakes.",
        "best_months": [5, 6, 7, 8, 9], "avoid_months": [11, 12, 1, 2, 3],
        "avoid_reason": "winter: passes closed, many hotels shut and temperatures fall far below zero",
        "access": {"rail": False, "air": True, "bus": False, "last_mile_pp": 300, "air_surcharge": 2200},
        "stay": {"budget": 1800, "mid": 4500, "premium": 12000},
        "breakfast_pp": {"budget": 180, "mid": 400, "premium": 800},
        "generic_meal_pp": {"budget": 350, "mid": 700, "premium": 1500},
        "local_transport_per_day": 2500,
        "attractions": [
            A(("shanti-stupa", "Shanti Stupa and Leh Palace", "heritage", ["heritage", "spiritual", "nature"], 3, 100, False, "evening", "Leh", "Sunset from the hilltop stupa; nine-storey palace")),
            A(("thiksey", "Thiksey Monastery", "spiritual", ["spiritual", "culture", "heritage"], 2.5, 30, False, "morning", "Thiksey", "Twelve-storey monastery resembling the Potala")),
            A(("hemis", "Hemis Monastery", "spiritual", ["spiritual", "culture", "heritage"], 2, 100, False, "morning", "Hemis", "Ladakh's largest monastery")),
            A(("magnetic-hill", "Magnetic Hill and Sangam", "nature", ["nature"], 2.5, 0, False, "afternoon", "Nimmu", "Confluence of the Indus and Zanskar")),
            A(("pangong", "Pangong Tso day excursion", "nature", ["nature", "adventure", "relaxation"], 10, 3200, False, "morning", "Pangong", "Long drive to the changing-colour high-altitude lake")),
            A(("nubra", "Nubra Valley and Diskit", "adventure", ["adventure", "nature", "culture"], 8, 3000, False, "morning", "Nubra", "Khardung La pass, dunes and double-humped camels")),
            A(("leh-market", "Leh Main Bazaar", "shopping", ["shopping", "food", "culture"], 2, 0, False, "evening", "Leh", "Pashmina, prayer flags and Tibetan snacks")),
            A(("acclimatise", "Slow acclimatisation day at Leh cafes", "relaxation", ["relaxation", "food"], 3, 0, True, "any", "Leh", "Rest at altitude before higher passes")),
            A(("river-rafting-zanskar", "Zanskar-Indus rafting", "adventure", ["adventure", "nature"], 3, 1800, False, "morning", "Nimmu", "Grade II-III rafting run")),
            A(("alchi", "Alchi Monastery", "heritage", ["heritage", "culture", "spiritual"], 2, 50, True, "afternoon", "Alchi", "11th-century murals")),
        ],
        "restaurants": [
            R(("tibetan-kitchen", "The Tibetan Kitchen", "Tibetan", ["lunch", "dinner"], "mid", 600, "Thukpa and momo", "Leh")),
            R(("gesmo", "Gesmo Restaurant", "Continental", ["breakfast", "lunch"], "mid", 500, "Fresh bakery and coffee", "Leh")),
            R(("bon-appetit", "Bon Appetit", "Ladakhi", ["dinner"], "mid", 700, "Skyu and tigmo", "Leh")),
            R(("lala-s-cafe", "Lala's Art Cafe", "Cafe", ["lunch"], "mid", 450, "Sandwiches and courtyard seating", "Leh")),
            R(("zomsa", "Zomsa Bakery", "Bakery", ["breakfast"], "budget", 200, "Apricot cake and butter tea", "Leh")),
            R(("chopsticks-leh", "Chopsticks Noodle Bar", "Tibetan and Chinese", ["lunch", "dinner"], "budget", 400, "Noodles and momos", "Leh")),
            R(("the-grand-dragon", "Grand Dragon Restaurant", "Multi-cuisine", ["dinner"], "premium", 1500, "Hotel buffet", "Old Road")),
            R(("summer-harvest", "Summer Harvest", "Ladakhi and Indian", ["lunch", "dinner"], "mid", 650, "Apricot dishes and veggies", "Leh")),
        ],
    },
    {
        "id": "coorg", "name": "Coorg (Kodagu)", "state": "Karnataka", "region": "Western Ghats",
        "aliases": ["kodagu", "madikeri", "coffee country", "kushalnagar"],
        "lat": 12.4244, "lon": 75.7382,
        "tagline": "Coffee estates, misty hills, waterfalls and Kodava cuisine.",
        "best_months": [10, 11, 12, 1, 2, 3], "avoid_months": [6, 7, 8],
        "avoid_reason": "heavy monsoon rainfall and leech-prone trails",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 700, "air_surcharge": 0},
        "stay": {"budget": 1500, "mid": 4000, "premium": 10500},
        "breakfast_pp": {"budget": 150, "mid": 350, "premium": 700},
        "generic_meal_pp": {"budget": 300, "mid": 600, "premium": 1300},
        "local_transport_per_day": 1500,
        "attractions": [
            A(("coffee-estate", "Coffee plantation walk and tasting", "nature", ["nature", "food"], 3, 500, False, "morning", "Madikeri", "Walk an estate and taste fresh-roasted Coorg coffee")),
            A(("abbey-falls", "Abbey Falls", "nature", ["nature"], 1.5, 50, False, "morning", "Madikeri", "Waterfall inside a coffee and spice plantation")),
            A(("raja-seat", "Raja's Seat sunset", "nature", ["nature", "relaxation"], 1.5, 20, False, "evening", "Madikeri", "Royal sunset viewpoint")),
            A(("dubare", "Dubare Elephant Camp", "wildlife", ["wildlife", "nature"], 3, 500, False, "morning", "Kushalnagar", "Bathing and feeding elephants by the Cauvery")),
            A(("namdroling", "Namdroling Monastery (Golden Temple)", "spiritual", ["spiritual", "culture", "heritage"], 2, 0, False, "afternoon", "Bylakuppe", "Tibetan settlement and golden Buddha statues")),
            A(("iruppu", "Iruppu Falls trek", "nature", ["nature", "adventure"], 3, 100, False, "morning", "Brahmagiri", "Forest walk to a sacred waterfall")),
            A(("tadiandamol", "Tadiandamol peak trek", "adventure", ["adventure", "nature"], 5, 600, False, "morning", "Kakkabe", "Coorg's highest peak")),
            A(("kodava-cooking", "Kodava cooking class", "food", ["food", "culture"], 3, 1500, True, "afternoon", "Madikeri", "Pandi curry, kadambuttu and akki roti at a homestay")),
            A(("madikeri-fort", "Madikeri Fort and museum", "heritage", ["heritage", "culture"], 1.5, 25, True, "afternoon", "Madikeri", "Old fort with a small museum")),
            A(("harangi", "Harangi reservoir boating", "relaxation", ["relaxation", "nature"], 2, 300, False, "afternoon", "Harangi", "Calm reservoir with a picnic area")),
        ],
        "restaurants": [
            R(("raintree", "Raintree Restaurant", "Kodava", ["lunch", "dinner"], "mid", 700, "Pandi curry with kadambuttu", "Madikeri")),
            R(("coorg-cuisine", "Coorg Cuisine", "Kodava", ["lunch", "dinner"], "mid", 600, "Bamboo shoot curry and akki roti", "Madikeri")),
            R(("hotel-deepika", "Hotel Deepika", "South Indian", ["breakfast", "lunch"], "budget", 200, "Neer dosa and filter coffee", "Madikeri")),
            R(("the-coffee-cup", "The Coffee Cup", "Cafe", ["lunch"], "mid", 350, "Coffee and snacks", "Madikeri")),
            R(("madikeri-bakes", "Millers 49", "Bakery", ["breakfast"], "budget", 180, "Fresh bread and pastries", "Madikeri")),
            R(("kaveri-food", "Kaveri Homestay Kitchen", "Kodava home-cooked", ["dinner"], "mid", 800, "Home-cooked Kodava meal", "Kushalnagar")),
            R(("the-tamara-dining", "Tamara Dining", "Multi-cuisine", ["dinner"], "premium", 1600, "Estate dining", "Kabbinakad")),
            R(("mysore-mess", "Mysore Mess", "Andhra and Karnataka", ["lunch", "dinner"], "budget", 350, "Meals on banana leaf", "Kushalnagar")),
        ],
    },
    {
        "id": "pondicherry", "name": "Pondicherry", "state": "Puducherry", "region": "Coromandel Coast",
        "aliases": ["puducherry", "pondy", "auroville", "white town"],
        "lat": 11.9416, "lon": 79.8083,
        "tagline": "French Quarter cafes, seaside promenades and Auroville calm.",
        "best_months": [10, 11, 12, 1, 2, 3], "avoid_months": [5, 6],
        "avoid_reason": "hot and humid, with rain from the northeast monsoon in November",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 500, "air_surcharge": 0},
        "stay": {"budget": 1500, "mid": 3800, "premium": 9500},
        "breakfast_pp": {"budget": 150, "mid": 350, "premium": 700},
        "generic_meal_pp": {"budget": 300, "mid": 650, "premium": 1400},
        "local_transport_per_day": 700,
        "attractions": [
            A(("white-town", "White Town heritage walk", "heritage", ["heritage", "culture", "relaxation"], 2.5, 0, False, "morning", "White Town", "Yellow-walled French colonial lanes")),
            A(("promenade", "Rock Beach promenade sunrise", "relaxation", ["relaxation", "beach"], 1.5, 0, False, "morning", "Promenade", "Early walk along the seafront")),
            A(("auroville", "Auroville and Matrimandir", "spiritual", ["spiritual", "wellness", "culture"], 3, 100, False, "morning", "Auroville", "Experimental township with the golden Matrimandir")),
            A(("paradise-beach", "Paradise Beach boat trip", "beach", ["beach", "relaxation", "nature"], 4, 400, False, "afternoon", "Chunnambar", "Backwater ferry to a sandy beach")),
            A(("aurobindo", "Sri Aurobindo Ashram", "spiritual", ["spiritual", "culture"], 1.5, 0, False, "morning", "White Town", "Quiet ashram and samadhi")),
            A(("french-food-walk", "French Quarter cafe and food walk", "food", ["food", "culture"], 3, 1000, False, "afternoon", "White Town", "Croissants, crepes and Tamil-French fusion")),
            A(("scuba", "Discover scuba at Temple Reef", "adventure", ["adventure", "nature"], 3, 4500, False, "morning", "Pondicherry", "Beginner scuba with an instructor")),
            A(("pottery", "Ceramics and pottery workshop", "culture", ["culture", "relaxation"], 2, 800, True, "afternoon", "Auroville", "Hands-on wheel pottery session")),
            A(("sunday-market", "Goubert Market and Nehru Street", "shopping", ["shopping", "culture", "food"], 2, 0, False, "evening", "Pondicherry", "Fresh produce and boutiques")),
            A(("french-cooking", "Tamil-French cooking class", "food", ["food", "culture"], 3, 1600, True, "afternoon", "White Town", "Coconut-based curries and French bakes")),
        ],
        "restaurants": [
            R(("le-cafe", "Le Cafe", "Cafe", ["breakfast", "lunch"], "mid", 450, "Croissants and coffee by the sea", "Promenade")),
            R(("villa-shanti", "Villa Shanti", "French-Indian", ["dinner"], "premium", 1800, "Prawn bisque and duck confit", "White Town")),
            R(("surguru", "Surguru Restaurant", "South Indian", ["lunch", "dinner"], "budget", 350, "Meals on banana leaf", "Pondicherry")),
            R(("baker-street", "Baker Street", "Bakery", ["breakfast", "lunch"], "mid", 400, "Quiche and cakes", "White Town")),
            R(("coromandel-cafe", "Coromandel Cafe", "Continental", ["lunch", "dinner"], "mid", 800, "Garden dining", "White Town")),
            R(("mango-hill", "Mango Hill", "Multi-cuisine", ["lunch", "dinner"], "mid", 700, "Garden dining and seafood", "Pondicherry")),
            R(("hidden-gem", "Hidden Gem", "French", ["dinner"], "mid", 900, "Steak and fresh pasta", "White Town")),
            R(("rasa-cafe", "Rasa Vegetarian", "Vegetarian", ["lunch"], "budget", 300, "Thali and dosa", "Pondicherry")),
        ],
    },
    {
        "id": "varanasi", "name": "Varanasi", "state": "Uttar Pradesh", "region": "Gangetic plains",
        "aliases": ["banaras", "benares", "kashi", "sarnath"],
        "lat": 25.3176, "lon": 82.9739,
        "tagline": "Ghats, ganga aarti and one of the world's oldest living street food scenes.",
        "best_months": [10, 11, 12, 1, 2, 3], "avoid_months": [5, 6],
        "avoid_reason": "extreme heat above 42°C",
        "access": {"rail": True, "air": True, "bus": True, "last_mile_pp": 100, "air_surcharge": 0},
        "stay": {"budget": 1200, "mid": 3200, "premium": 9000},
        "breakfast_pp": {"budget": 120, "mid": 300, "premium": 650},
        "generic_meal_pp": {"budget": 250, "mid": 500, "premium": 1200},
        "local_transport_per_day": 700,
        "attractions": [
            A(("dawn-boat", "Sunrise boat ride on the Ganga", "spiritual", ["spiritual", "culture", "relaxation"], 2, 400, False, "morning", "Assi to Dashashwamedh", "Row past the ghats at dawn")),
            A(("ganga-aarti-varanasi", "Dashashwamedh Ghat evening aarti", "spiritual", ["spiritual", "culture"], 1.5, 0, False, "evening", "Dashashwamedh", "Large evening lamp ceremony")),
            A(("kashi-vishwanath", "Kashi Vishwanath Temple", "spiritual", ["spiritual", "heritage", "culture"], 2, 0, False, "morning", "Old City", "One of the twelve Jyotirlinga shrines")),
            A(("sarnath", "Sarnath", "heritage", ["heritage", "spiritual", "culture"], 3, 100, False, "afternoon", "Sarnath", "Where the Buddha gave his first sermon")),
            A(("food-walk-varanasi", "Kachori Gali and Banarasi street-food walk", "food", ["food", "culture"], 3, 800, False, "morning", "Old City", "Kachori, lassi, tamatar chaat, malaiyyo")),
            A(("silk-weaving", "Banarasi silk weaving workshop", "culture", ["culture", "shopping"], 2, 300, True, "afternoon", "Lallapura", "Watch handloom weavers")),
            A(("bhu", "BHU campus and Bharat Kala Bhavan", "heritage", ["heritage", "culture", "nature"], 2, 100, True, "afternoon", "BHU", "Museum and Vishwanath Temple in a sprawling campus")),
            A(("ramnagar", "Ramnagar Fort", "heritage", ["heritage"], 2, 100, False, "afternoon", "Ramnagar", "18th-century fort across the river")),
            A(("assi-yoga", "Assi Ghat sunrise yoga", "wellness", ["wellness", "spiritual", "relaxation"], 1.5, 300, False, "morning", "Assi", "Riverside yoga at dawn")),
            A(("ghat-walk", "Ghat-to-ghat evening walk", "relaxation", ["relaxation", "culture"], 2, 0, False, "evening", "Ghats", "Walk from Assi to Manikarnika")),
        ],
        "restaurants": [
            R(("kachori-gali", "Kachori Gali", "Street food", ["breakfast", "lunch"], "budget", 150, "Kachori-sabzi and jalebi", "Old City")),
            R(("blue-lassi", "Blue Lassi", "Lassi shop", ["lunch"], "budget", 200, "Fruit lassi and thandai", "Old City")),
            R(("deena-chat", "Deena Chat Bhandar", "Street food", ["lunch", "dinner"], "budget", 250, "Tamatar chaat", "Old City")),
            R(("kashi-chat", "Kashi Chat Bhandar", "Chaat", ["lunch", "dinner"], "budget", 250, "Aloo tikki and papdi chaat", "Godowlia")),
            R(("brown-bread", "Brown Bread Bakery", "Cafe", ["breakfast", "lunch"], "mid", 450, "Organic breakfast and fresh bakes", "Old City")),
            R(("haifa", "Haifa Restaurant", "Israeli and continental", ["lunch", "dinner"], "mid", 500, "Falafel and hummus", "Assi Ghat")),
            R(("ganga-fuji", "Ganga Fuji", "Multi-cuisine", ["dinner"], "mid", 700, "Riverside dinner", "Assi Ghat")),
            R(("taj-ganges", "Nadesar Palace Dining", "Fine dining", ["dinner"], "premium", 2000, "Royal Awadhi and Banarasi cuisine", "Nadesar")),
        ],
    },
    {
        "id": "andaman", "name": "Andaman Islands", "state": "Andaman and Nicobar Islands", "region": "Andaman Sea",
        "aliases": ["port blair", "havelock", "swaraj dweep", "neil island", "andamans"],
        "lat": 11.6234, "lon": 92.7265,
        "tagline": "Turquoise water, coral reefs and quiet white-sand beaches.",
        "best_months": [11, 12, 1, 2, 3, 4], "avoid_months": [6, 7, 8, 9],
        "avoid_reason": "monsoon: ferries and water sports are frequently cancelled",
        "access": {"rail": False, "air": True, "bus": False, "last_mile_pp": 200, "air_surcharge": 3500},
        "stay": {"budget": 2200, "mid": 5500, "premium": 14000},
        "breakfast_pp": {"budget": 200, "mid": 450, "premium": 900},
        "generic_meal_pp": {"budget": 400, "mid": 800, "premium": 1800},
        "local_transport_per_day": 1800,
        "attractions": [
            A(("radhanagar", "Radhanagar Beach, Havelock", "beach", ["beach", "nature", "relaxation"], 4, 0, False, "afternoon", "Havelock", "Frequently ranked among Asia's best beaches")),
            A(("scuba-havelock", "Scuba diving at Havelock", "adventure", ["adventure", "nature"], 3, 4200, False, "morning", "Havelock", "Beginner dive with an instructor")),
            A(("elephant-beach", "Elephant Beach snorkelling", "adventure", ["adventure", "beach", "nature"], 3, 1800, False, "morning", "Havelock", "Snorkelling at a coral beach")),
            A(("cellular-jail", "Cellular Jail and light-and-sound show", "heritage", ["heritage", "culture"], 2.5, 100, True, "evening", "Port Blair", "Colonial-era prison and evening show")),
            A(("ross-island", "Ross Island and North Bay", "heritage", ["heritage", "nature", "beach"], 4, 800, False, "morning", "Port Blair", "British ruins and coral snorkelling")),
            A(("neil-island", "Neil Island day trip", "beach", ["beach", "relaxation", "nature"], 6, 1500, False, "morning", "Neil Island", "Bharatpur and Laxmanpur beaches")),
            A(("baratang", "Limestone caves at Baratang", "nature", ["nature", "adventure", "wildlife"], 8, 1800, False, "morning", "Baratang", "Mangrove creeks and limestone caves")),
            A(("kalapather", "Kalapathar beach sunrise", "relaxation", ["relaxation", "nature", "beach"], 2, 0, False, "morning", "Havelock", "Black rock beach at sunrise")),
            A(("seafood-cooking", "Fresh-catch seafood tasting", "food", ["food", "culture"], 2.5, 1200, False, "afternoon", "Port Blair", "Local fishermen's catch grilled and curried")),
            A(("sea-walk", "North Bay sea walk", "adventure", ["adventure", "nature"], 2, 3500, False, "morning", "Port Blair", "Walk on the seabed in a helmet")),
        ],
        "restaurants": [
            R(("annapurna-pb", "Annapurna Cafeteria", "South Indian", ["breakfast", "lunch", "dinner"], "budget", 300, "Meals and dosa", "Port Blair")),
            R(("lighthouse-pb", "New Lighthouse Restaurant", "Seafood", ["lunch", "dinner"], "mid", 700, "Grilled fish and tandoori crab", "Port Blair")),
            R(("full-moon-cafe", "Full Moon Cafe", "Multi-cuisine", ["lunch", "dinner"], "mid", 800, "Coconut-crusted fish", "Havelock")),
            R(("anju-coco", "Anju Coco Resto", "Seafood", ["dinner"], "mid", 750, "Lobster and prawn platters", "Havelock")),
            R(("infinity-cafe", "Infinity Cafe", "Cafe", ["lunch"], "mid", 500, "Pancakes and smoothies", "Havelock")),
            R(("nemo-cafe", "Nemo Cafe", "Multi-cuisine", ["dinner"], "mid", 650, "Seafood curries", "Havelock")),
            R(("wild-orchid", "Wild Orchid Dining", "Continental", ["dinner"], "premium", 2000, "Resort seafood dinner", "Havelock")),
            R(("dolphin-shack", "Dolphin Beach Shack", "Beach shack", ["lunch"], "budget", 400, "Fresh catch with rice", "Neil Island")),
        ],
    },
]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def round_to(x: float, step: int = 50) -> int:
    return int(round(x / step) * step)


def transport_options(o_lat, o_lon, dest: dict) -> list[dict]:
    d = haversine(o_lat, o_lon, dest["lat"], dest["lon"])
    acc = dest["access"]
    last_mile = acc["last_mile_pp"]
    opts: list[dict] = []
    ground = d * 1.3  # road/rail circuity
    if acc["rail"] and ground <= 2600:
        opts.append({
            "mode": "train",
            "one_way_per_person": round_to(250 + 1.35 * ground + last_mile * 0.6),
            "hours": round(ground / 55 + 2.0, 1),
        })
    if acc["bus"] and ground <= 1100:
        opts.append({
            "mode": "bus",
            "one_way_per_person": round_to(300 + 1.05 * ground + last_mile * 0.4),
            "hours": round(ground / 42 + 1.0, 1),
        })
    if acc["air"] and d >= 250:
        opts.append({
            "mode": "flight",
            "one_way_per_person": round_to(2400 + 1.2 * d + acc["air_surcharge"] + last_mile),
            "hours": round(d / 700 + 2.2 + last_mile / 700, 1),
        })
    if not opts:
        # very short hops: cab is the only sensible mode
        opts.append({"mode": "cab", "one_way_per_person": round_to(800 + 8 * ground), "hours": round(ground / 45 + 0.5, 1)})
    return opts


def build() -> dict:
    origins = {}
    for name, (lat, lon, aliases) in ORIGINS.items():
        origins[name] = {"name": name, "lat": lat, "lon": lon, "aliases": aliases}

    destinations = []
    for dest in DESTINATIONS:
        item = {k: v for k, v in dest.items() if k not in ("attractions", "restaurants")}
        item["attractions"] = [
            dict(zip(
                ["id", "name", "type", "themes", "duration_hours", "cost_per_person", "indoor", "best_time", "area", "note"],
                (f"{dest['id']}-{t[0]}", *t[1:]),
            ))
            for t in dest["attractions"]
        ]
        item["restaurants"] = [
            dict(zip(
                ["id", "name", "cuisine", "meals", "tier", "cost_per_person", "signature", "area"],
                (f"{dest['id']}-{t[0]}", *t[1:]),
            ))
            for t in dest["restaurants"]
        ]
        themes: dict[str, int] = {}
        for a in item["attractions"]:
            for th in a["themes"]:
                themes[th] = themes.get(th, 0) + 1
        item["themes"] = sorted(themes, key=lambda k: -themes[k])
        item["transport_from"] = {
            name: transport_options(lat, lon, dest) for name, (lat, lon, _) in ORIGINS.items()
        }
        destinations.append(item)

    return {
        "meta": {
            "currency": "INR",
            "note": "Illustrative planning estimates for a typical mid-season week, rounded. Not live fares or prices.",
            "version": 1,
        },
        "origins": origins,
        "destinations": destinations,
    }


if __name__ == "__main__":
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    n_att = sum(len(d["attractions"]) for d in data["destinations"])
    n_res = sum(len(d["restaurants"]) for d in data["destinations"])
    print(f"wrote {OUT}: {len(data['destinations'])} destinations, {n_att} attractions, {n_res} restaurants")
