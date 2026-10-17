"""
geo_data.py - Chennai Geographic Data and Spatial Utilities
Dark Store Location Optimization Engine
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

# Realistic Bounding Box for Greater Chennai Metropolitan Area
CHENNAI_BOUNDS = {
    "min_lat": 12.9000,
    "max_lat": 13.1500,
    "min_lon": 80.1200,
    "max_lon": 80.2800,
    "center_lat": 13.0400,
    "center_lon": 80.2200,
}

# 50 Prime Candidate Dark Store Locations across Key Commercial & Residential Hubs in Chennai
CANDIDATE_LOCATIONS: List[Dict[str, any]] = [
    {"id": 0, "name": "T. Nagar (Panagal Park)", "lat": 13.0418, "lon": 80.2341, "zone": "Central"},
    {"id": 1, "name": "Anna Nagar (Roundtana)", "lat": 13.0850, "lon": 80.2101, "zone": "North-West"},
    {"id": 2, "name": "Adyar (LB Road)", "lat": 13.0012, "lon": 80.2565, "zone": "South"},
    {"id": 3, "name": "Velachery (Bypass Road)", "lat": 12.9756, "lon": 80.2207, "zone": "South"},
    {"id": 4, "name": "Mylapore (Luz Corner)", "lat": 13.0368, "lon": 80.2676, "zone": "Central"},
    {"id": 5, "name": "OMR Perungudi", "lat": 12.9654, "lon": 80.2461, "zone": "IT Corridor"},
    {"id": 6, "name": "Guindy (Kathipara)", "lat": 13.0067, "lon": 80.2026, "zone": "Central"},
    {"id": 7, "name": "Porur (Junction)", "lat": 13.0382, "lon": 80.1565, "zone": "West"},
    {"id": 8, "name": "Tambaram (Sanatorium)", "lat": 12.9349, "lon": 80.1280, "zone": "South-West"},
    {"id": 9, "name": "Kilpauk (Poonamallee High Rd)", "lat": 13.0827, "lon": 80.2407, "zone": "North-Central"},
    {"id": 10, "name": "Nungambakkam (High Road)", "lat": 13.0569, "lon": 80.2425, "zone": "Central"},
    {"id": 11, "name": "Besant Nagar (Elliot's Beach)", "lat": 12.9982, "lon": 80.2665, "zone": "South-Coastal"},
    {"id": 12, "name": "Vadapalani (100ft Road)", "lat": 13.0500, "lon": 80.2121, "zone": "Central-West"},
    {"id": 13, "name": "Alwarpet (TTK Road)", "lat": 13.0336, "lon": 80.2505, "zone": "Central"},
    {"id": 14, "name": "Thiruvanmiyur (Signal)", "lat": 12.9830, "lon": 80.2594, "zone": "South-Coastal"},
    {"id": 15, "name": "OMR Sholinganallur", "lat": 12.9010, "lon": 80.2279, "zone": "IT Corridor"},
    {"id": 16, "name": "OMR Thoraipakkam", "lat": 12.9382, "lon": 80.2372, "zone": "IT Corridor"},
    {"id": 17, "name": "Chromepet (GST Road)", "lat": 12.9516, "lon": 80.1462, "zone": "South-West"},
    {"id": 18, "name": "Pallavaram", "lat": 12.9675, "lon": 80.1491, "zone": "South-West"},
    {"id": 19, "name": "Saidapet (Anna Salai)", "lat": 13.0213, "lon": 80.2231, "zone": "Central"},
    {"id": 20, "name": "Kodambakkam (Arcot Road)", "lat": 13.0524, "lon": 80.2255, "zone": "Central"},
    {"id": 21, "name": "Ashok Nagar (11th Avenue)", "lat": 13.0373, "lon": 80.2123, "zone": "Central-West"},
    {"id": 22, "name": "K.K. Nagar (Munusamy Salai)", "lat": 13.0410, "lon": 80.1994, "zone": "Central-West"},
    {"id": 23, "name": "Koyambedu (Market)", "lat": 13.0694, "lon": 80.1948, "zone": "West"},
    {"id": 24, "name": "Mogappair (East)", "lat": 13.0837, "lon": 80.1748, "zone": "North-West"},
    {"id": 25, "name": "Ambattur (OT)", "lat": 13.1143, "lon": 80.1548, "zone": "North-West"},
    {"id": 26, "name": "Villivakkam (High Road)", "lat": 13.1075, "lon": 80.2056, "zone": "North-West"},
    {"id": 27, "name": "Kolathur (Redhills Road)", "lat": 13.1242, "lon": 80.2158, "zone": "North"},
    {"id": 28, "name": "Perambur (Paper Mills Rd)", "lat": 13.1110, "lon": 80.2437, "zone": "North"},
    {"id": 29, "name": "Purasawalkam (High Road)", "lat": 13.0903, "lon": 80.2575, "zone": "North-Central"},
    {"id": 30, "name": "Royapettah (High Road)", "lat": 13.0544, "lon": 80.2610, "zone": "Central"},
    {"id": 31, "name": "Triplicane (Pycrofts Rd)", "lat": 13.0587, "lon": 80.2757, "zone": "Central-Coastal"},
    {"id": 32, "name": "George Town (Parrys)", "lat": 13.0900, "lon": 80.2850, "zone": "North-Coastal"},
    {"id": 33, "name": "Egmore (Gandhi Irwin Rd)", "lat": 13.0784, "lon": 80.2608, "zone": "Central"},
    {"id": 34, "name": "Chetpet (Harrington Rd)", "lat": 13.0719, "lon": 80.2415, "zone": "Central"},
    {"id": 35, "name": "Mandaveli (St. Marys Rd)", "lat": 13.0250, "lon": 80.2600, "zone": "South"},
    {"id": 36, "name": "R.A. Puram (Chamiers Rd)", "lat": 13.0210, "lon": 80.2520, "zone": "South"},
    {"id": 37, "name": "Kotturpuram (Gandhi Mandapam Rd)", "lat": 13.0180, "lon": 80.2400, "zone": "South"},
    {"id": 38, "name": "Medavakkam (Junction)", "lat": 12.9180, "lon": 80.1920, "zone": "South"},
    {"id": 39, "name": "Madipakkam (Koot Road)", "lat": 12.9647, "lon": 80.1961, "zone": "South"},
    {"id": 40, "name": "Nanganallur (4th Main Rd)", "lat": 12.9800, "lon": 80.1870, "zone": "South"},
    {"id": 41, "name": "Alandur (Asarhana)", "lat": 13.0030, "lon": 80.2010, "zone": "South-Central"},
    {"id": 42, "name": "Manapakkam (River View Rd)", "lat": 13.0180, "lon": 80.1750, "zone": "West"},
    {"id": 43, "name": "Ramapuram (Mount-Poonamallee)", "lat": 13.0310, "lon": 80.1790, "zone": "West"},
    {"id": 44, "name": "Valasaravakkam (Arcot Rd)", "lat": 13.0410, "lon": 80.1740, "zone": "West"},
    {"id": 45, "name": "Virugambakkam (Kaliappa Rd)", "lat": 13.0510, "lon": 80.1920, "zone": "West"},
    {"id": 46, "name": "Arumbakkam (MMDA)", "lat": 13.0720, "lon": 80.2070, "zone": "Central-West"},
    {"id": 47, "name": "Shenoy Nagar (7th Cross)", "lat": 13.0780, "lon": 80.2250, "zone": "Central-North"},
    {"id": 48, "name": "Pallikaranai (Radial Rd)", "lat": 12.9360, "lon": 80.2130, "zone": "South"},
    {"id": 49, "name": "Ayanavaram (Medavakkam Tank Rd)", "lat": 13.0970, "lon": 80.2330, "zone": "North-Central"},
]


def get_candidate_stores(count: int = 50) -> pd.DataFrame:
    """Return a subset of candidate dark store locations as a DataFrame."""
    count = max(1, min(count, len(CANDIDATE_LOCATIONS)))
    df = pd.DataFrame(CANDIDATE_LOCATIONS[:count])
    return df


def generate_customers(num_customers: int, candidate_df: pd.DataFrame, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic customer locations across Chennai.
    Simulates high-density residential demand around commercial hubs plus
    general urban distribution across Chennai municipal boundaries.
    """
    rng = np.random.default_rng(random_seed)
    
    # 75% clustered around commercial and residential hubs (realistic quick-commerce demand)
    # 25% uniformly distributed across the city area
    num_clustered = int(num_customers * 0.75)
    num_uniform = num_customers - num_clustered
    
    hub_coords = candidate_df[["lat", "lon"]].values
    num_hubs = len(hub_coords)
    
    if num_clustered > 0:
        # Urban density distribution: major central and sub-city hubs have higher customer density
        hub_weights = 1.0 / (np.arange(1, num_hubs + 1) ** 0.6)
        hub_probs = hub_weights / hub_weights.sum()
        cluster_center_indices = rng.choice(num_hubs, size=num_clustered, p=hub_probs)
        centers = hub_coords[cluster_center_indices]
        
        # Standard deviation ~ 0.010 degrees (~1.1 km radius around hubs)
        lat_offsets = rng.normal(loc=0.0, scale=0.010, size=num_clustered)
        lon_offsets = rng.normal(loc=0.0, scale=0.010, size=num_clustered)
        
        clustered_lats = centers[:, 0] + lat_offsets
        clustered_lons = centers[:, 1] + lon_offsets
    else:
        clustered_lats = np.array([])
        clustered_lons = np.array([])
        
    if num_uniform > 0:
        uniform_lats = rng.uniform(CHENNAI_BOUNDS["min_lat"], CHENNAI_BOUNDS["max_lat"], size=num_uniform)
        uniform_lons = rng.uniform(CHENNAI_BOUNDS["min_lon"], CHENNAI_BOUNDS["max_lon"], size=num_uniform)
    else:
        uniform_lats = np.array([])
        uniform_lons = np.array([])
        
    all_lats = np.concatenate([clustered_lats, uniform_lats])
    all_lons = np.concatenate([clustered_lons, uniform_lons])
    
    # Clip strictly within Chennai boundary
    all_lats = np.clip(all_lats, CHENNAI_BOUNDS["min_lat"], CHENNAI_BOUNDS["max_lat"])
    all_lons = np.clip(all_lons, CHENNAI_BOUNDS["min_lon"], CHENNAI_BOUNDS["max_lon"])
    
    # Shuffle order so uniform and clustered are mixed
    shuffle_indices = rng.permutation(num_customers)
    all_lats = all_lats[shuffle_indices]
    all_lons = all_lons[shuffle_indices]
    
    customer_df = pd.DataFrame({
        "id": np.arange(num_customers),
        "lat": np.round(all_lats, 5),
        "lon": np.round(all_lons, 5),
        "demand": np.ones(num_customers, dtype=int),
    })
    return customer_df


def haversine_vectorized(
    lat1: np.ndarray, lon1: np.ndarray,
    lat2: np.ndarray, lon2: np.ndarray,
    circuity_factor: float = 1.25
) -> np.ndarray:
    """
    Computes road distance (km) between coordinates using Haversine formula
    multiplied by urban road circuity factor (default 1.25).
    Inputs can be 1D or 2D broadcastable numpy arrays in degrees.
    """
    EARTH_RADIUS_KM = 6371.0088
    
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    
    haversine_dist = EARTH_RADIUS_KM * c
    return haversine_dist * circuity_factor


def compute_sparse_candidates(
    customers_df: pd.DataFrame,
    stores_df: pd.DataFrame,
    d_max_km: float,
    circuity_factor: float = 1.25
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    High-Performance Spatial Pre-Filtering:
    Computes all candidate pairs (i, j) where road distance d_ij <= d_max_km.
    
    Returns:
        cust_indices: 1D array of customer indices (0 to N-1)
        store_indices: 1D array of candidate store indices (0 to M-1)
        distances: 1D array of distances in km for each valid pair
    """
    cust_lats = customers_df["lat"].values[:, np.newaxis]  # Shape (N, 1)
    cust_lons = customers_df["lon"].values[:, np.newaxis]  # Shape (N, 1)
    
    store_lats = stores_df["lat"].values[np.newaxis, :]    # Shape (1, M)
    store_lons = stores_df["lon"].values[np.newaxis, :]    # Shape (1, M)
    
    # Vectorized Haversine across (N, M) matrix
    dist_matrix = haversine_vectorized(cust_lats, cust_lons, store_lats, store_lons, circuity_factor=circuity_factor)
    
    # Filter pairs strictly within D_max
    valid_mask = dist_matrix <= d_max_km
    cust_indices, store_indices = np.nonzero(valid_mask)
    distances = dist_matrix[cust_indices, store_indices]
    
    return cust_indices, store_indices, distances
