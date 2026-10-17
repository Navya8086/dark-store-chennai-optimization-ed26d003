"""
optimizer.py - High-Performance Mixed-Integer Linear Programming (MILP) Solver
Dark Store Location Optimization Engine with Maximum Distance Constraint
"""

import time
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from ortools.linear_solver import pywraplp
from geo_data import compute_sparse_candidates


def solve_dark_store_optimization(
    customers_df: pd.DataFrame,
    stores_df: pd.DataFrame,
    d_max_km: float = 3.0,
    max_stores_allowed_k: int = 10,
    revenue_per_order: float = 120.0,
    delivery_cost_per_km: float = 15.0,
    fixed_cost_per_store: float = 10000.0,
    store_capacity: int = 2000,
    circuity_factor: float = 1.25,
    solver_time_limit_sec: int = 60,
) -> Dict[str, Any]:
    """
    Solves the Dark Store Location Optimization MIP model using Google OR-Tools.
    
    Model formulation:
      Maximize: Sum_{i, j: d_ij <= D_max} (Revenue - DelCost * d_ij) * x_ij - Sum_j FixedCost * y_j
      Subject to:
        1. Demand satisfaction: Sum_{j} x_ij <= Demand_i (for each customer i)
        2. Store capacity:      Sum_{i} x_ij <= Capacity_j * y_j (for each store j)
        3. Maximum distance:    x_ij = 0 if d_ij > D_max (enforced via sparse variable creation)
        4. Max stores allowed:  Sum_j y_j <= K
        5. Binary / bounds:     y_j in {0, 1}, 0 <= x_ij <= 1
    """
    start_time = time.time()
    
    num_customers = len(customers_df)
    num_stores = len(stores_df)
    
    # Step 1: High-Performance Spatial Pre-filtering
    # Only generate decision variables for pairs within maximum allowable distance D_max
    cust_idx_arr, store_idx_arr, distances = compute_sparse_candidates(
        customers_df, stores_df, d_max_km=d_max_km, circuity_factor=circuity_factor
    )
    num_sparse_vars = len(distances)
    
    # Step 2: Initialize Fast MIP Solver (CBC primary, SCIP fallback)
    solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        solver = pywraplp.Solver.CreateSolver("HIGHS")
    if not solver:
        raise RuntimeError("No suitable MIP solver (CBC/SCIP/HIGHS) found in Google OR-Tools.")
        
    solver.SetTimeLimit(int(solver_time_limit_sec * 1000))
    params = pywraplp.MPSolverParameters()
    params.SetDoubleParam(pywraplp.MPSolverParameters.RELATIVE_MIP_GAP, 0.01)
    
    # Step 3: Decision Variables
    # y[j]: Binary variable, 1 if candidate store j is opened, 0 otherwise
    y = {}
    for j in range(num_stores):
        y[j] = solver.BoolVar(f"y_{j}")
        
    # x[k]: Continuous / integer variable for customer serving (since demand=1, continuous relaxation [0, 1] is exact and faster)
    # x[k] = 1 if customer cust_idx_arr[k] is served by store store_idx_arr[k]
    x = {}
    for k in range(num_sparse_vars):
        x[k] = solver.NumVar(0.0, 1.0, f"x_{cust_idx_arr[k]}_{store_idx_arr[k]}")
        
    # Step 4: Constraints
    
    # Constraint 1: Maximum Stores Allowed Limit (Sum_j y_j <= K)
    k_constraint = solver.Constraint(0.0, float(max_stores_allowed_k), "MaxStoresLimit")
    for j in range(num_stores):
        k_constraint.SetCoefficient(y[j], 1.0)
        
    # Group sparse variables by customer and by store for efficient constraint generation
    cust_to_vars: List[List[int]] = [[] for _ in range(num_customers)]
    store_to_vars: List[List[int]] = [[] for _ in range(num_stores)]
    
    for k in range(num_sparse_vars):
        c_i = cust_idx_arr[k]
        s_j = store_idx_arr[k]
        cust_to_vars[c_i].append(k)
        store_to_vars[s_j].append(k)
        
    # Constraint 2: Demand Satisfaction (Sum_{j: d_ij <= D_max} x_ij <= Demand_i)
    # Note: Customers without any store within D_max have empty cust_to_vars and cannot be served
    demands = customers_df["demand"].values
    for i in range(num_customers):
        var_indices = cust_to_vars[i]
        if var_indices:
            cust_constraint = solver.Constraint(0.0, float(demands[i]), f"Demand_{i}")
            for k in var_indices:
                cust_constraint.SetCoefficient(x[k], 1.0)
                
    # Constraint 3: Store Capacity & Activation (Sum_{i: d_ij <= D_max} x_ij - Capacity_j * y_j <= 0)
    for j in range(num_stores):
        var_indices = store_to_vars[j]
        cap_constraint = solver.Constraint(-solver.infinity(), 0.0, f"Capacity_{j}")
        cap_constraint.SetCoefficient(y[j], -float(store_capacity))
        for k in var_indices:
            cap_constraint.SetCoefficient(x[k], 1.0)
            
    # Step 5: Objective Function (Maximize Net Profit)
    # Net Profit = Sum_{k} (Revenue - DelCost * dist_k) * x_k - Sum_j FixedCost * y_j
    objective = solver.Objective()
    objective.SetMaximization()
    
    # Store opening fixed cost penalty
    for j in range(num_stores):
        objective.SetCoefficient(y[j], -float(fixed_cost_per_store))
        
    # Margin contribution per fulfilled delivery
    for k in range(num_sparse_vars):
        delivery_cost = delivery_cost_per_km * distances[k]
        margin_contribution = revenue_per_order - delivery_cost
        objective.SetCoefficient(x[k], float(margin_contribution))
        
    # Step 6: Solve
    status_code = solver.Solve(params)
    solve_duration = round(time.time() - start_time, 3)
    
    status_map = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
        pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
    }
    status_str = status_map.get(status_code, "UNKNOWN")
    
    # Step 7: Parse and Structure Results
    opened_store_mask = np.zeros(num_stores, dtype=bool)
    if status_code in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        for j in range(num_stores):
            if y[j].solution_value() > 0.5:
                opened_store_mask[j] = True
                
    # Extract assignments
    assignments_list = []
    store_orders = np.zeros(num_stores, dtype=int)
    store_delivery_costs = np.zeros(num_stores, dtype=float)
    store_revenues = np.zeros(num_stores, dtype=float)
    served_customer_ids = set()
    
    total_delivery_cost = 0.0
    total_distance_served = 0.0
    
    if status_code in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        for k in range(num_sparse_vars):
            val = x[k].solution_value()
            if val > 0.5:  # Customer served
                c_i = cust_idx_arr[k]
                s_j = store_idx_arr[k]
                dist = distances[k]
                del_cost = dist * delivery_cost_per_km
                
                served_customer_ids.add(c_i)
                store_orders[s_j] += 1
                store_delivery_costs[s_j] += del_cost
                store_revenues[s_j] += revenue_per_order
                
                total_delivery_cost += del_cost
                total_distance_served += dist
                
                assignments_list.append({
                    "customer_id": int(customers_df["id"].iloc[c_i]),
                    "store_id": int(stores_df["id"].iloc[s_j]),
                    "store_name": str(stores_df["name"].iloc[s_j]),
                    "store_zone": str(stores_df["zone"].iloc[s_j]),
                    "customer_lat": float(customers_df["lat"].iloc[c_i]),
                    "customer_lon": float(customers_df["lon"].iloc[c_i]),
                    "store_lat": float(stores_df["lat"].iloc[s_j]),
                    "store_lon": float(stores_df["lon"].iloc[s_j]),
                    "distance_km": round(float(dist), 2),
                    "delivery_cost": round(float(del_cost), 2),
                })
                
    assignments_df = pd.DataFrame(assignments_list)
    
    total_demand_count = int(customers_df["demand"].sum())
    fulfilled_count = len(served_customer_ids)
    fulfillment_rate = (fulfilled_count / total_demand_count * 100.0) if total_demand_count > 0 else 0.0
    avg_delivery_dist = (total_distance_served / fulfilled_count) if fulfilled_count > 0 else 0.0
    
    opened_count = int(opened_store_mask.sum())
    total_fixed_cost = opened_count * fixed_cost_per_store
    total_revenue = fulfilled_count * revenue_per_order
    net_profit = total_revenue - total_delivery_cost - total_fixed_cost
    
    # Store-by-store breakdown table
    store_records = []
    for j in range(num_stores):
        is_opened = bool(opened_store_mask[j])
        orders = int(store_orders[j])
        utilization = (orders / store_capacity * 100.0) if store_capacity > 0 else 0.0
        s_rev = float(store_revenues[j])
        s_del_cost = float(store_delivery_costs[j])
        s_fix_cost = fixed_cost_per_store if is_opened else 0.0
        s_profit = s_rev - s_del_cost - s_fix_cost
        
        store_records.append({
            "Store ID": int(stores_df["id"].iloc[j]),
            "Name": str(stores_df["name"].iloc[j]),
            "Zone": str(stores_df["zone"].iloc[j]),
            "Latitude": float(stores_df["lat"].iloc[j]),
            "Longitude": float(stores_df["lon"].iloc[j]),
            "Status": "OPENED" if is_opened else "CLOSED",
            "Is Opened": is_opened,
            "Orders Fulfilled": orders,
            "Capacity": store_capacity,
            "Capacity Utilization (%)": round(utilization, 1),
            "Revenue (₹)": round(s_rev, 2),
            "Delivery Cost (₹)": round(s_del_cost, 2),
            "Fixed Cost (₹)": round(s_fix_cost, 2),
            "Net Profit Contribution (₹)": round(s_profit, 2),
        })
    store_results_df = pd.DataFrame(store_records)
    
    # Identify unserved customers
    all_cust_ids = set(customers_df["id"].values)
    unserved_ids = all_cust_ids - served_customer_ids
    unserved_df = customers_df[customers_df["id"].isin(unserved_ids)].copy()
    
    kpis = {
        "solver_status": status_str,
        "solve_duration_sec": solve_duration,
        "sparse_variable_count": num_sparse_vars,
        "max_stores_allowed_k": max_stores_allowed_k,
        "stores_opened": opened_count,
        "total_demand": total_demand_count,
        "demand_fulfilled": fulfilled_count,
        "fulfillment_rate_pct": round(fulfillment_rate, 2),
        "total_revenue": round(total_revenue, 2),
        "total_delivery_cost": round(total_delivery_cost, 2),
        "total_fixed_cost": round(total_fixed_cost, 2),
        "net_profit": round(net_profit, 2),
        "avg_delivery_distance_km": round(avg_delivery_dist, 2),
    }
    
    return {
        "kpis": kpis,
        "store_results": store_results_df,
        "assignments": assignments_df,
        "unserved_customers": unserved_df,
    }


def run_k_benchmark(
    customers_df: pd.DataFrame,
    stores_df: pd.DataFrame,
    k_values: List[int] = [2, 5, 10, 20, 25],
    d_max_km: float = 3.0,
    revenue_per_order: float = 120.0,
    delivery_cost_per_km: float = 15.0,
    fixed_cost_per_store: float = 10000.0,
    store_capacity: int = 2000,
    circuity_factor: float = 1.25,
) -> pd.DataFrame:
    """
    Runs the sensitivity analysis across multiple values of K (e.g. 2, 5, 10, 20, 25)
    for 10,000 customers and 50 candidate stores.
    Returns a benchmark comparison DataFrame suitable for plotting.
    """
    benchmark_results = []
    
    for k in k_values:
        res = solve_dark_store_optimization(
            customers_df=customers_df,
            stores_df=stores_df,
            d_max_km=d_max_km,
            max_stores_allowed_k=k,
            revenue_per_order=revenue_per_order,
            delivery_cost_per_km=delivery_cost_per_km,
            fixed_cost_per_store=fixed_cost_per_store,
            store_capacity=store_capacity,
            circuity_factor=circuity_factor,
        )
        kpi = res["kpis"]
        benchmark_results.append({
            "Max Stores Allowed (K)": k,
            "Stores Actually Opened": kpi["stores_opened"],
            "Net Profit (₹)": kpi["net_profit"],
            "Total Revenue (₹)": kpi["total_revenue"],
            "Total Delivery Cost (₹)": kpi["total_delivery_cost"],
            "Fixed Operating Cost (₹)": kpi["total_fixed_cost"],
            "Demand Fulfilled (Orders)": kpi["demand_fulfilled"],
            "Fulfillment Rate (%)": kpi["fulfillment_rate_pct"],
            "Avg Distance (km)": kpi["avg_delivery_distance_km"],
            "Solve Time (s)": kpi["solve_duration_sec"],
        })
        
    return pd.DataFrame(benchmark_results)
