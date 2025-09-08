"""
Synthetic Insurance Data Generator (Romania)
-------------------------------------------
Generates highly non-uniform (skewed, seasonal, and correlated) datasets for:
  - Homeowners, Renters, Auto, Commercial Property

Adds Romanian-specific geo context:
  - All counties (județe) + a few cities each (non-uniform weights)
  - Synthetic postal codes (6-digit), region tags (coastal/mountain/danube/urban)
  - Geo risk features: hail/flood/wind/fire, crime risk, proximities
  - Auto telematics features
  - Weather at loss date (precipitation, wind, hail size, temperature)

Outputs relational CSVs ready for Azure SQL + a blob manifest.

Run example:
  python synth_insurance_ro.py --policies 12000 --seed 42 --out ./out

Requires: pandas, numpy, faker
"""
from __future__ import annotations
import argparse
import os
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, date
import numpy as np
import pandas as pd
from faker import Faker

# Romanian locale for realistic names
fake = Faker("ro_RO")

np.set_printoptions(suppress=True)

# -------------------------
# Config & Helpers
# -------------------------
@dataclass
class Sizes:
    n_policies: int = 10_000
    auto_share: float = 0.45
    home_share: float = 0.30
    renters_share: float = 0.15
    commercial_share: float = 0.10

PRODUCTS = ["auto", "homeowners", "renters", "commercial_property"]

# County → cities, weight, tags. Tags drive risk and proximities.
# NOTE: City lists are not exhaustive. Postal codes are synthetic.
COUNTIES = [
    {"code":"AB", "name":"Alba", "weight":0.018, "tags":["mountain","transylvania"], "cities":["Alba Iulia","Aiud","Sebes"]},
    {"code":"AR", "name":"Arad", "weight":0.022, "tags":["plain","west"], "cities":["Arad","Ineu","Lipova"]},
    {"code":"AG", "name":"Arges", "weight":0.028, "tags":["hill","south"], "cities":["Pitesti","Campulung","Curtea de Arges"]},
    {"code":"BC", "name":"Bacau", "weight":0.025, "tags":["moldova"], "cities":["Bacau","Onesti","Moinesti"]},
    {"code":"BH", "name":"Bihor", "weight":0.03, "tags":["west","plain"], "cities":["Oradea","Alesd","Salonta"]},
    {"code":"BN", "name":"Bistrita-Nasaud", "weight":0.013, "tags":["mountain","nord"], "cities":["Bistrita","Nasaud"]},
    {"code":"BT", "name":"Botosani", "weight":0.017, "tags":["moldova","north"], "cities":["Botosani","Dorohoi"]},
    {"code":"BV", "name":"Brasov", "weight":0.035, "tags":["mountain","carpathians"], "cities":["Brasov","Fagaras","Sacele"]},
    {"code":"BR", "name":"Braila", "weight":0.017, "tags":["danube","plain"], "cities":["Braila"]},
    {"code":"BZ", "name":"Buzau", "weight":0.022, "tags":["hill","south"], "cities":["Buzau","Ramnicul Sarat"]},
    {"code":"CS", "name":"Caras-Severin", "weight":0.012, "tags":["mountain","banat"], "cities":["Resita","Caransebes"]},
    {"code":"CL", "name":"Calarasi", "weight":0.016, "tags":["danube","plain"], "cities":["Calarasi","Oltenita"]},
    {"code":"CJ", "name":"Cluj", "weight":0.06, "tags":["transylvania","urban_hub"], "cities":["Cluj-Napoca","Turda","Dej"]},
    {"code":"CT", "name":"Constanta", "weight":0.055, "tags":["coastal","danube_delta"], "cities":["Constanta","Mangalia","Medgidia"]},
    {"code":"CV", "name":"Covasna", "weight":0.012, "tags":["mountain"], "cities":["Sfantu Gheorghe","Targu Secuiesc"]},
    {"code":"DB", "name":"Dambovita", "weight":0.023, "tags":["hill","south"], "cities":["Targoviste","Gaesti"]},
    {"code":"DJ", "name":"Dolj", "weight":0.03, "tags":["south","plain"], "cities":["Craiova","Bailesti"]},
    {"code":"GL", "name":"Galati", "weight":0.024, "tags":["danube","moldova"], "cities":["Galati","Tecuci"]},
    {"code":"GR", "name":"Giurgiu", "weight":0.012, "tags":["danube","south"], "cities":["Giurgiu"]},
    {"code":"GJ", "name":"Gorj", "weight":0.017, "tags":["hill","oltenia"], "cities":["Targu Jiu","Motru"]},
    {"code":"HR", "name":"Harghita", "weight":0.016, "tags":["mountain","carpathians"], "cities":["Miercurea Ciuc","Odorheiu Secuiesc"]},
    {"code":"HD", "name":"Hunedoara", "weight":0.02, "tags":["mountain","transylvania"], "cities":["Deva","Hunedoara","Petrosani"]},
    {"code":"IL", "name":"Ialomita", "weight":0.015, "tags":["plain","south"], "cities":["Slobozia","Fetesti"]},
    {"code":"IS", "name":"Iasi", "weight":0.045, "tags":["moldova","urban_hub"], "cities":["Iasi","Pascani"]},
    {"code":"IF", "name":"Ilfov", "weight":0.04, "tags":["suburban","south"], "cities":["Voluntari","Otopeni","Chitila"]},
    {"code":"MM", "name":"Maramures", "weight":0.02, "tags":["mountain","north"], "cities":["Baia Mare","Sighetu Marmatiei"]},
    {"code":"MH", "name":"Mehedinti", "weight":0.014, "tags":["danube","southwest"], "cities":["Drobeta-Turnu Severin"]},
    {"code":"MS", "name":"Mures", "weight":0.025, "tags":["transylvania"], "cities":["Targu Mures","Sighisoara","Reghin"]},
    {"code":"NT", "name":"Neamt", "weight":0.02, "tags":["moldova","carpathians"], "cities":["Piatra Neamt","Roman"]},
    {"code":"OT", "name":"Olt", "weight":0.018, "tags":["south","plain"], "cities":["Slatina","Caracal"]},
    {"code":"PH", "name":"Prahova", "weight":0.04, "tags":["hill","urban_hub"], "cities":["Ploiesti","Campina","Sinaia"]},
    {"code":"SM", "name":"Satu Mare", "weight":0.018, "tags":["northwest","plain"], "cities":["Satu Mare","Carei"]},
    {"code":"SJ", "name":"Salaj", "weight":0.012, "tags":["northwest","hill"], "cities":["Zalau"]},
    {"code":"SB", "name":"Sibiu", "weight":0.028, "tags":["mountain","transylvania"], "cities":["Sibiu","Medias"]},
    {"code":"SV", "name":"Suceava", "weight":0.03, "tags":["north","moldova","carpathians"], "cities":["Suceava","Falticeni","Radauti"]},
    {"code":"TR", "name":"Teleorman", "weight":0.016, "tags":["south","plain"], "cities":["Alexandria","Turnu Magurele"]},
    {"code":"TM", "name":"Timis", "weight":0.06, "tags":["urban_hub","west"], "cities":["Timisoara","Lugoj","Sannicolau Mare"]},
    {"code":"TL", "name":"Tulcea", "weight":0.013, "tags":["coastal","danube_delta"], "cities":["Tulcea","Babadag"]},
    {"code":"VL", "name":"Valcea", "weight":0.02, "tags":["hill","oltenia"], "cities":["Ramnicu Valcea","Dragasani"]},
    {"code":"VS", "name":"Vaslui", "weight":0.018, "tags":["moldova","plain"], "cities":["Vaslui","Barlad","Husi"]},
    {"code":"VN", "name":"Vrancea", "weight":0.017, "tags":["seismic","moldova"], "cities":["Focsani","Adjud"]},
    {"code":"BZB", "name":"Bucuresti", "weight":0.12, "tags":["urban_hub","capital"], "cities":["Sector 1","Sector 2","Sector 3","Sector 4","Sector 5","Sector 6"]},
]

# Normalize weights
w = np.array([c["weight"] for c in COUNTIES], dtype=float)
w = w / w.sum()
for i,c in enumerate(COUNTIES):
    c["weight"] = float(w[i])

# Seasonality multipliers by peril (month index 1..12)
SEASONALITY = {
    "hail": [0.3,0.4,0.6,1.3,1.8,2.0,1.7,1.3,0.8,0.5,0.4,0.3],
    "theft": [1.2,1.1,1.0,0.95,0.9,0.95,1.0,1.05,1.1,1.2,1.3,1.4],
    "collision": [0.9,0.9,1.0,1.0,1.05,1.05,1.1,1.1,1.2,1.25,1.3,1.35],
    "fire": [0.85,0.9,0.95,1.0,1.0,1.05,1.15,1.1,1.0,0.95,0.9,0.85],
    "water_damage": [1.3,1.2,1.15,1.05,1.0,0.9,0.85,0.85,0.95,1.0,1.1,1.25],
}

# Base peril frequencies (claims per policy-year)
BASE_FREQ = {
    "homeowners": {"hail": 0.07, "fire": 0.015, "theft": 0.02, "water_damage": 0.035},
    "renters": {"theft": 0.03, "water_damage": 0.02, "fire": 0.004},
    "auto": {"collision": 0.15, "comprehensive": 0.06, "theft": 0.015},
    "commercial_property": {"fire": 0.025, "theft": 0.02, "water_damage": 0.025}
}

# Severity parameters (lognormal) mu, sigma
SEVERITY_LN = {
    "hail": (8.3, 0.7),
    "theft": (7.3, 0.9),
    "collision": (7.8, 0.8),
    "comprehensive": (7.9, 0.8),
    "fire": (9.0, 1.0),
    "water_damage": (8.0, 0.7)
}

# Coverage menus
COVERAGE_TYPES = {
    "homeowners": ["dwelling","other_structures","personal_property","loss_of_use","personal_liability","medical_payments"],
    "renters": ["personal_property","liability","loss_of_use"],
    "auto": ["liability_bi","liability_pd","collision","comprehensive","uninsured_motorist","medical_payments"],
    "commercial_property": ["building","contents","business_interruption","equipment_breakdown","liability"],
}

rng = np.random.default_rng()

# Helpers

def pick_county_city():
    county = rng.choice(COUNTIES, p=[c["weight"] for c in COUNTIES])
    city = rng.choice(county["cities"])  # simple uniform within county
    return county, city

# Synthetic postal code: RO-<two letters><6 digits>
def make_postal_code(code:str) -> str:
    return f"{rng.integers(100000,999999)}"

# Risk baselines by tags (0..1)
TAG_RISK_BASE = {
    "urban_hub": {"crime": 0.65, "hail": 0.35, "flood": 0.25, "wind": 0.35, "fire": 0.35},
    "capital": {"crime": 0.7, "hail": 0.3, "flood": 0.2, "wind": 0.35, "fire": 0.35},
    "coastal": {"crime": 0.45, "hail": 0.25, "flood": 0.55, "wind": 0.65, "fire": 0.35},
    "danube": {"crime": 0.4, "hail": 0.35, "flood": 0.6, "wind": 0.45, "fire": 0.35},
    "danube_delta": {"crime": 0.35, "hail": 0.25, "flood": 0.7, "wind": 0.55, "fire": 0.35},
    "mountain": {"crime": 0.3, "hail": 0.6, "flood": 0.35, "wind": 0.45, "fire": 0.45},
    "carpathians": {"crime": 0.3, "hail": 0.6, "flood": 0.35, "wind": 0.5, "fire": 0.45},
    "transylvania": {"crime": 0.35, "hail": 0.5, "flood": 0.3, "wind": 0.4, "fire": 0.4},
    "plain": {"crime": 0.4, "hail": 0.35, "flood": 0.35, "wind": 0.35, "fire": 0.35},
    "hill": {"crime": 0.35, "hail": 0.45, "flood": 0.35, "wind": 0.35, "fire": 0.4},
    "moldova": {"crime": 0.45, "hail": 0.4, "flood": 0.4, "wind": 0.4, "fire": 0.4},
    "west": {"crime": 0.4, "hail": 0.45, "flood": 0.3, "wind": 0.45, "fire": 0.35},
    "south": {"crime": 0.45, "hail": 0.35, "flood": 0.4, "wind": 0.4, "fire": 0.35},
    "north": {"crime": 0.35, "hail": 0.5, "flood": 0.35, "wind": 0.4, "fire": 0.4},
    "northwest": {"crime": 0.4, "hail": 0.45, "flood": 0.3, "wind": 0.45, "fire": 0.35},
    "oltenia": {"crime": 0.42, "hail": 0.4, "flood": 0.4, "wind": 0.35, "fire": 0.35},
    "suburban": {"crime": 0.5, "hail": 0.35, "flood": 0.3, "wind": 0.35, "fire": 0.35},
    "seismic": {"crime": 0.4, "hail": 0.35, "flood": 0.35, "wind": 0.35, "fire": 0.45},
}

# Convert county tags into numeric risks (with randomness for non-uniformity)
def county_risks(county_tags:list[str]) -> dict:
    agg = {"crime":0,"hail":0,"flood":0,"wind":0,"fire":0}
    for t in county_tags:
        base = TAG_RISK_BASE.get(t)
        if not base:
            continue
        for k,v in base.items():
            agg[k] += v
    # Average + random jitter
    for k in agg:
        agg[k] = max(0.01, min(0.99, (agg[k]/max(1,len(county_tags))) * rng.uniform(0.85,1.15)))
    return agg

# Proximities (km) based on tags
def proximities(tags:list[str]) -> dict:
    urban = ("urban_hub" in tags) or ("capital" in tags)
    coastal = "coastal" in tags or "danube_delta" in tags
    danube = "danube" in tags or coastal

    def sample_distance(base_small:float, base_large:float, heavy_tail:bool=False):
        if heavy_tail:
            # Pareto-like heavy tail
            x = rng.pareto(2.5) + 0.1
            return float(np.clip(base_small * x, 0, base_large*3))
        if urban:
            return float(np.clip(rng.gamma(2.0, base_small), 0.1, base_large))
        else:
            return float(np.clip(rng.gamma(1.5, base_large/2), 0.2, base_large*1.5))

    return {
        "dist_fire_station_km": sample_distance(0.5, 8, heavy_tail=True),
        "dist_hydrant_km": sample_distance(0.3, 5),
        "dist_police_km": sample_distance(0.7, 12),
        "dist_coast_km": float(rng.uniform(1,30)) if coastal else float(rng.uniform(80,600)),
        "dist_danube_km": float(rng.uniform(1,25)) if danube else float(rng.uniform(30,400)),
    }

# Weather simulator for loss date conditioned on peril + month + tags
def simulate_weather(peril:str, month:int, tags:list[str]) -> dict:
    coastal = "coastal" in tags or "danube_delta" in tags
    mountain = "mountain" in tags or "carpathians" in tags

    # Baselines
    t_base = 10 + 12*np.sin((month-3)/12*2*np.pi)  # crude seasonality
    temp = rng.normal(t_base, 6 if mountain else (5 if coastal else 7))
    precip = max(0, rng.gamma(2.0, 3.5))
    wind = rng.normal(6 if coastal else 3.5, 2.0)
    hail = max(0, rng.normal(0.2 if peril=="hail" else 0.0, 0.25))

    # Peril adjustments
    if peril == "hail":
        precip *= rng.uniform(1.2,2.0)
        wind *= rng.uniform(1.0,1.3)
        hail = max(0.2, rng.normal(1.2, 0.5))
    elif peril in ("water_damage",):
        precip *= rng.uniform(1.3,2.2)
    elif peril in ("fire",):
        precip *= rng.uniform(0.5,0.9)
        wind *= rng.uniform(0.9,1.1)

    return {
        "temperature_c": round(float(temp),1),
        "precip_mm": round(float(precip),1),
        "wind_mps": round(float(max(0,wind)),1),
        "hail_size_cm": round(float(hail),2)
    }

# Telematics generator
def generate_telematics() -> dict:
    score = float(np.clip(rng.normal(70, 12), 20, 98))
    night_pct = float(np.clip(rng.beta(2,5), 0, 1))
    hard_brakes = float(rng.gamma(1.8, 2.5))  # per 100km
    over_speed = float(rng.gamma(1.3, 1.8))
    phone_use = float(np.clip(rng.beta(2.2,6.0),0,1))
    return {
        "telematics_score": round(score,1),
        "night_driving_pct": round(night_pct,3),
        "hard_brakes_per_100km": round(hard_brakes,1),
        "overspeed_events_per_100km": round(over_speed,1),
        "phone_use_pct": round(phone_use,3)
    }

# Premium modeling helpers
def homeowner_premium(repl_cost:float, risks:dict, crime:float, discounts:float) -> float:
    base = 120.0 + 0.0012 * repl_cost
    rf = 1 + 0.5*risks['hail'] + 0.4*risks['flood'] + 0.2*crime + 0.1*risks['fire']
    return float(np.clip(base * rf * (1-discounts), 80, 4000))

def renters_premium(limit_pp:float, risks:dict, crime:float, discounts:float) -> float:
    base = 40 + 0.003*min(limit_pp, 50000)
    rf = 1 + 0.25*risks['water'] + 0.35*crime
    return float(np.clip(base * rf * (1-discounts), 25, 600))

def auto_premium(annual_km:int, telem:dict, risks:dict, crime:float, discounts:float) -> float:
    risk_telem = (100 - telem['telematics_score'])/100
    base = 180 + 0.01*min(annual_km, 30000)
    rf = 1 + 0.6*risk_telem + 0.2*crime + 0.15*risks['wind'] + 0.1*risks['hail']
    return float(np.clip(base * rf * (1-discounts), 120, 2500))

def commercial_premium(building:float, contents:float, risks:dict, crime:float, discounts:float) -> float:
    exposure = building + 0.6*contents
    base = 300 + 0.0006*exposure
    rf = 1 + 0.35*risks['fire'] + 0.4*risks['flood'] + 0.25*crime + 0.1*risks['wind']
    return float(np.clip(base * rf * (1-discounts), 200, 20000))

# Claim severity lognormal
import math

def ln_severity(peril:str) -> float:
    mu, sigma = SEVERITY_LN[peril]
    return float(np.random.lognormal(mu, sigma))

# Frequency modulator by policy risks
def policy_freq_multiplier(product:str, risks:dict, crime:float, telem:dict|None) -> float:
    if product == "homeowners":
        return 1 + 0.8*risks['hail'] + 0.6*risks['flood'] + 0.3*crime
    if product == "renters":
        return 1 + 0.5*crime + 0.3*risks['flood']
    if product == "auto":
        telem_risk = (100 - telem['telematics_score'])/100 if telem else 0.3
        return 1 + 0.9*telem_risk + 0.3*crime + 0.2*risks['wind']
    if product == "commercial_property":
        return 1 + 0.5*risks['fire'] + 0.6*risks['flood'] + 0.3*crime
    return 1.0

# -------------------------
# Generators
# -------------------------

def generate_customers(n:int):
    rows=[]
    for i in range(n):
        county, city = pick_county_city()
        risks = county_risks(county['tags'])
        crime = risks['crime']
        postal = make_postal_code(county['code'])
        prox = proximities(county['tags'])
        rows.append({
            "customer_id": f"C-{i+1:06d}",
            "full_name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "county_code": county['code'],
            "county_name": county['name'],
            "city": city,
            "postal_code": postal,
            "crime_risk": round(crime,3),
            "hail_risk": round(risks['hail'],3),
            "flood_risk": round(risks['flood'],3),
            "wind_risk": round(risks['wind'],3),
            "fire_risk": round(risks['fire'],3),
            **{k:round(v,2) for k,v in prox.items()},
            "dob": fake.date_of_birth(minimum_age=18, maximum_age=80)
        })
    return pd.DataFrame(rows)

VEHICLE_MAKES = {
    "Dacia": ["Logan","Duster","Sandero"],
    "Volkswagen": ["Golf","Passat","Polo"],
    "Renault": ["Clio","Megane","Captur"],
    "Skoda": ["Octavia","Fabia","Superb"],
    "Toyota": ["Corolla","Yaris","RAV4"],
}

COMM_LOC_TYPES = ["office","warehouse","factory","retail"]
CONSTRUCTION = ["brick","concrete","wood","steel"]


def generate_policies(customers:pd.DataFrame, sizes:Sizes):
    n = sizes.n_policies
    # Assign product types by shares
    product_choices = rng.choice(PRODUCTS, size=n, p=[sizes.auto_share, sizes.home_share, sizes.renters_share, sizes.commercial_share])
    cust_ids = rng.choice(customers.customer_id.values, size=n, replace=True)

    rows_pol=[]; rows_cov=[]; rows_prop=[]; rows_rent=[]; rows_veh=[]

    start_base = date(2024,1,1)
    for i in range(n):
        pid = f"P-{i+1:06d}"
        cid = cust_ids[i]
        cust = customers.loc[customers.customer_id==cid].iloc[0]
        product = product_choices[i]
        # policy term random 6-18 months
        start = start_base + timedelta(days=int(rng.integers(0, 365)))
        end = start + timedelta(days=int(rng.integers(180, 540)))
        status = rng.choice(["active","lapsed","cancelled"], p=[0.86,0.09,0.05])
        channel = rng.choice(["agent","online","partner"], p=[0.55,0.35,0.10])
        discounts = float(np.clip(rng.normal(0.05,0.04),0,0.2))
        risks = {"hail":cust.hail_risk,"flood":cust.flood_risk,"wind":cust.wind_risk,"fire":cust.fire_risk}
        crime = float(cust.crime_risk)

        premium = 0.0
        # Product-specific attributes & coverages
        if product == "homeowners":
            area = int(np.clip(rng.normal(110, 40), 40, 350))
            cost_sqm = rng.choice([600,700,800,900,1000], p=[0.1,0.2,0.3,0.25,0.15])
            repl = area*cost_sqm * rng.uniform(0.9,1.3)
            floors = int(np.clip(rng.normal(2,0.8),1,4))
            constr = rng.choice(["brick","concrete","wood"], p=[0.6,0.35,0.05])
            has_alarm = rng.choice([True,False], p=[0.55,0.45])
            premium = homeowner_premium(repl, risks, crime, discounts)
            rows_prop.append({"property_id":f"H-{i+1:06d}","policy_id":pid,"year_built":int(rng.integers(1965,2024)),
                              "construction":constr,"area_sqm":area,"floors":floors,
                              "has_alarm":has_alarm,"replacement_cost":round(repl,2)})
            # coverages
            for ctype in COVERAGE_TYPES['homeowners']:
                limit = {"dwelling":repl, "other_structures":0.1*repl, "personal_property": 0.2*repl,
                         "loss_of_use": 0.1*repl, "personal_liability": 100000, "medical_payments": 5000}[ctype]
                deductible = rng.choice([250,500,1000,1500], p=[0.2,0.45,0.25,0.1])
                rows_cov.append({"coverage_id":f"CV-{len(rows_cov)+1:07d}","policy_id":pid,
                                 "coverage_type":ctype,"limit":round(float(limit),2),"deductible":deductible,
                                 "premium_component":round(premium* rng.uniform(0.1,0.35),2)})
        elif product == "renters":
            limit_pp = float(rng.choice([15000,25000,35000,50000], p=[0.25,0.4,0.25,0.1]))
            roommates = int(rng.integers(0,3))
            premium = renters_premium(limit_pp, {"water":cust.flood_risk}, crime, discounts)
            rows_rent.append({"unit_id":f"R-{i+1:06d}","policy_id":pid,"personal_property_limit":limit_pp,
                              "roommates_count":roommates,"building_type":rng.choice(["block","house"], p=[0.8,0.2])})
            for ctype in COVERAGE_TYPES['renters']:
                limit = {"personal_property":limit_pp, "liability":50000, "loss_of_use":5000}[ctype]
                deductible = rng.choice([100,250,500], p=[0.3,0.5,0.2])
                rows_cov.append({"coverage_id":f"CV-{len(rows_cov)+1:07d}","policy_id":pid,
                                 "coverage_type":ctype,"limit":limit,"deductible":deductible,
                                 "premium_component":round(premium* rng.uniform(0.15,0.4),2)})
        elif product == "auto":
            make = rng.choice(list(VEHICLE_MAKES.keys()))
            model = rng.choice(VEHICLE_MAKES[make])
            year = int(rng.integers(2005,2025))
            annual_km = int(np.clip(rng.normal(12000, 6000), 2000, 35000))
            telem = generate_telematics()
            premium = auto_premium(annual_km, telem, risks, crime, discounts)
            rows_veh.append({"vehicle_id":f"V-{i+1:06d}","policy_id":pid,"make":make,"model":model,
                             "year":year,"annual_mileage":annual_km, **telem})
            for ctype in COVERAGE_TYPES['auto']:
                limit = {"liability_bi":50000, "liability_pd":25000, "collision":15000, "comprehensive":15000,
                         "uninsured_motorist":25000, "medical_payments":5000}[ctype]
                deductible = rng.choice([0,200,400,800], p=[0.1,0.4,0.35,0.15])
                rows_cov.append({"coverage_id":f"CV-{len(rows_cov)+1:07d}","policy_id":pid,
                                 "coverage_type":ctype,"limit":limit,"deductible":deductible,
                                 "premium_component":round(premium* rng.uniform(0.07,0.25),2)})
        else:  # commercial_property
            loc_type = rng.choice(COMM_LOC_TYPES, p=[0.35,0.35,0.15,0.15])
            building = float(rng.uniform(100_000, 5_000_000))
            contents = float(rng.uniform(50_000, 2_500_000))
            premium = commercial_premium(building, contents, risks, crime, discounts)
            rows_prop.append({"property_id":f"C-{i+1:06d}","policy_id":pid,"location_type":loc_type,
                              "sprinkler_grade": rng.choice(["A","B","C","None"], p=[0.25,0.35,0.25,0.15]),
                              "building_value":round(building,2),"contents_value":round(contents,2)})
            for ctype in COVERAGE_TYPES['commercial_property']:
                limit = {"building":building, "contents":contents, "business_interruption":0.4*building,
                         "equipment_breakdown":0.2*building, "liability":250000}[ctype]
                deductible = rng.choice([1000,2500,5000,10000], p=[0.25,0.35,0.25,0.15])
                rows_cov.append({"coverage_id":f"CV-{len(rows_cov)+1:07d}","policy_id":pid,
                                 "coverage_type":ctype,"limit":round(float(limit),2),"deductible":deductible,
                                 "premium_component":round(premium* rng.uniform(0.06,0.22),2)})

        rows_pol.append({
            "policy_id":pid,
            "customer_id":cid,
            "product_type":product,
            "start_date":start,
            "end_date":end,
            "status":status,
            "channel":channel,
            "discount_pct":round(discounts,3),
            "gross_premium":round(premium,2)
        })

    return (
        pd.DataFrame(rows_pol),
        pd.DataFrame(rows_cov),
        pd.DataFrame(rows_prop) if rows_prop else pd.DataFrame(columns=["property_id","policy_id"]),
        pd.DataFrame(rows_rent) if rows_rent else pd.DataFrame(columns=["unit_id","policy_id"]),
        pd.DataFrame(rows_veh) if rows_veh else pd.DataFrame(columns=["vehicle_id","policy_id"]) ,
    )

# Claims generator
PERILS_BY_PRODUCT = {
    "homeowners": ["hail","fire","theft","water_damage"],
    "renters": ["theft","water_damage","fire"],
    "auto": ["collision","theft","comprehensive"],
    "commercial_property": ["fire","theft","water_damage"],
}


def generate_claims(policies:pd.DataFrame, customers:pd.DataFrame, vehicles:pd.DataFrame, properties:pd.DataFrame):
    claims=[]; losses=[]
    veh_by_pid = {r.policy_id:r for _,r in vehicles.iterrows()} if not vehicles.empty else {}
    prop_by_pid = {r.policy_id:r for _,r in properties.iterrows()} if not properties.empty else {}
    for _,p in policies.iterrows():
        cust = customers.loc[customers.customer_id==p.customer_id].iloc[0]
        product = p.product_type
        # Frequency base
        base = BASE_FREQ[product]
        # Policy-level multipliers
        risks = {"hail":cust.hail_risk,"flood":cust.flood_risk,"wind":cust.wind_risk,"fire":cust.fire_risk}
        crime = float(cust.crime_risk)
        telem = veh_by_pid[p.policy_id].to_dict() if product=='auto' and p.policy_id in veh_by_pid else None
        freq_mult = policy_freq_multiplier(product, risks, crime, telem)
        # Expected annual claims across perils
        expected_year = sum(base.values()) * freq_mult
        # Term fraction in years
        term_days = (pd.to_datetime(p.end_date) - pd.to_datetime(p.start_date)).days
        horizon_years = max(0.1, term_days / 365.0)
        lam = expected_year * horizon_years
        n_claims = rng.poisson(lam=lam)
        if n_claims==0:
            continue
        for _ in range(n_claims):
            perils = PERILS_BY_PRODUCT[product]
            probs = np.array([base[x] for x in perils], dtype=float)
            probs = probs / probs.sum()
            peril = rng.choice(perils, p=probs)
            # month weighting
            month = int(rng.integers(1,13))
            if peril in SEASONALITY:
                if rng.random() < 0.7:
                    # biased draw toward seasonal peaks
                    month = rng.choice(range(1,13), p=np.array(SEASONALITY[peril])/np.sum(SEASONALITY[peril]))
            loss_date = pd.to_datetime(p.start_date) + timedelta(days=int(rng.integers(0, term_days)))
            # ensure month alignment
            loss_date = loss_date.replace(month=month, day=min(loss_date.day,28))
            # severity
            sev = ln_severity(peril)
            # Apply deductibles caps approximately by product
            if product=="auto":
                sev = np.clip(sev, 150, 30000)
            elif product=="homeowners":
                base_cap = prop_by_pid.get(p.policy_id, {}).get('replacement_cost', 200000)
                sev = np.clip(sev, 300, 0.6*base_cap)
            elif product=="commercial_property":
                base_cap = prop_by_pid.get(p.policy_id, {}).get('building_value', 1_000_000)
                sev = np.clip(sev, 1000, 0.7*base_cap)
            else:
                sev = np.clip(sev, 150, 25000)

            # status & payments
            status = rng.choice(["open","closed","denied"], p=[0.2,0.73,0.07])
            paid = sev * (rng.uniform(0.6,0.95) if status!="denied" else 0.0)
            reserve = 0.0 if status!="open" else sev * rng.uniform(0.2,0.6)
            close_date = None if status=="open" else (loss_date + timedelta(days=int(rng.gamma(3.0,5.0))))

            # Weather snapshot
            wx = simulate_weather(peril, month, [t for t in COUNTIES if t['code']==cust.county_code][0]['tags'])

            claim_id = f"CL-{len(claims)+1:07d}"
            claims.append({
                "claim_id":claim_id,
                "policy_id":p.policy_id,
                "product_type":product,
                "loss_date": loss_date.date(),
                "peril": peril,
                "status": status,
                "reserve": round(float(reserve),2),
                "paid": round(float(paid),2),
                "report_date": loss_date.date(),
                "close_date": None if close_date is None else close_date.date(),
                "severity_band": rng.choice(["low","medium","high","cat"], p=[0.45,0.35,0.18,0.02])
            })
            losses.append({
                "event_id": f"EV-{len(losses)+1:07d}",
                "claim_id": claim_id,
                "county_code": cust.county_code,
                "county_name": cust.county_name,
                "city": cust.city,
                "postal_code": cust.postal_code,
                **wx
            })
    return pd.DataFrame(claims), pd.DataFrame(losses)

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--policies", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="./out")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    Faker.seed(args.seed)

    os.makedirs(args.out, exist_ok=True)

    # Derive number of customers (some multi-policy)
    n_customers = max(2000, int(args.policies*0.6))

    customers = generate_customers(n_customers)
    policies, coverages, properties, rentals, vehicles = generate_policies(customers, Sizes(n_policies=args.policies))
    claims, loss_events = generate_claims(policies, customers, vehicles, properties)

    # Export
    def dump(df:pd.DataFrame, name:str):
        path = os.path.join(args.out, name)
        df.to_csv(path, index=False)
        print(f"→ {name}: {len(df)} rows")

    dump(customers, "customers.csv")
    dump(policies, "policies.csv")
    dump(coverages, "coverages.csv")
    dump(properties, "properties.csv")
    dump(rentals, "rental_units.csv")
    dump(vehicles, "vehicles.csv")
    dump(claims, "claims.csv")
    dump(loss_events, "loss_events.csv")

    # Geo features extract (unique combos) for reference
    geo = customers[["county_code","county_name","city","postal_code","crime_risk","hail_risk","flood_risk","wind_risk","fire_risk","dist_fire_station_km","dist_hydrant_km","dist_police_km","dist_coast_km","dist_danube_km"]].drop_duplicates()
    dump(geo, "geo_features.csv")

    # Simple blob manifest (no files created, just a template for later uploads)
    manifest = []
    for _,cl in claims.head(min(200, len(claims))).iterrows():
        manifest.append({
            "claim_id": cl.claim_id,
            "blob_path": f"claims/{cl.claim_id}/",
            "expected_files": ["report.pdf","photo_1.jpg","photo_2.jpg"],
            "ocr_text": ""
        })
    with open(os.path.join(args.out, "blob_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("Done. Synthetic Romanian insurance dataset created.")
