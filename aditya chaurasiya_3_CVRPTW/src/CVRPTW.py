import pandas as pd
import gurobipy as gp
from gurobipy import GRB

# Loading data
locations_df = pd.read_csv(r'C:\Users\adity\tsp\Assingment3_CVRPTW\data\MT-CVRPTW_inputs\locations.csv')
order_list_df = pd.read_excel(r'C:\Users\adity\tsp\Assingment3_CVRPTW\data\MT-CVRPTW_inputs\order_list.xlsx')
travel_matrix_df = pd.read_csv(r'C:\Users\adity\tsp\Assingment3_CVRPTW\data\MT-CVRPTW_inputs\travel_matrix.csv')
trucks_df = pd.read_csv(r'C:\Users\adity\tsp\Assingment3_CVRPTW\data\MT-CVRPTW_inputs\trucks.csv')

# Convert loading/unloading windows to minutes with explicit format
locations_df['start_minutes'] = pd.to_datetime(locations_df['location_loading_unloading_window_start'], format='%H:%M').dt.hour * 60 + pd.to_datetime(locations_df['location_loading_unloading_window_start'], format='%H:%M').dt.minute
locations_df['end_minutes'] = pd.to_datetime(locations_df['location_loading_unloading_window_end'], format='%H:%M').dt.hour * 60 + pd.to_datetime(locations_df['location_loading_unloading_window_end'], format='%H:%M').dt.minute

# Extracting data
locations = locations_df['location_code'].tolist()
orders = order_list_df.to_dict(orient='records')
travel_matrix = travel_matrix_df.set_index(['source_location_code', 'destination_location_code']).to_dict(orient='index')
trucks = trucks_df.to_dict(orient='records')

# Assuming constant amount of time spent at each location by trucks
service_time_customer = 20
service_time_depot = 60

depot1 = "A123"
customers = locations[:len(locations)-1]

# Initialize the Gurobi model
model = gp.Model("CVRPTW")

# Decision variable
x = {}
t = {}
I = {}

for k in range(len(trucks)):
    I[k] = model.addVar(vtype=GRB.BINARY, name=f'I_{k}')
    for i in locations:
        for j in locations:
            if i != j:
                x[(i, j, k)] = model.addVar(vtype=GRB.BINARY, name=f'x_{i}_{j}_{k}')
        t[(i, k)] = model.addVar(vtype=GRB.CONTINUOUS, name=f't_{i}_{k}', lb=0)

# Objective function: Minimize total distance and fixed costs
model.setObjective(
    gp.quicksum(
        travel_matrix.get((i, j), {}).get('travel_distance_in_km', 0) * x[(i, j, k)] * (20000 - int(truck['truck_max_weight']) / 1000)
        for k, truck in enumerate(trucks)
        for i in locations
        for j in locations if i != j
    ) + gp.quicksum(
        int(truck['truck_max_weight']) * 2 * I[k]
        for k, truck in enumerate(trucks)
    ), GRB.MINIMIZE
)

# Flow balancing constraint
for i in customers:
    model.addConstr(
        gp.quicksum(x[(i, j, k)] for j in locations if i != j for k in range(len(trucks))) == 1,
        name=f"Flow_Balancing_Out_{i}"
    )
    model.addConstr(
        gp.quicksum(x[(j, i, k)] for j in locations if i != j for k in range(len(trucks))) == 1,
        name=f"Flow_Balancing_In_{i}"
    )

# Demand constraint
for k, truck in enumerate(trucks):
    truck_max_weight = int(truck['truck_max_weight'])
    model.addConstr(
        gp.quicksum(order['Total Weight'] * x[(str(order['Destination Code']), j, k)] for order in orders for j in locations if str(order['Destination Code']) != j) <= truck_max_weight * I[k],
        name=f"Demand_{k}"
    )

# Each vehicle should leave the depot once
for k in range(len(trucks)):
    model.addConstr(
        gp.quicksum(x[(depot1, j, k)] for j in customers if depot1 != j) == 1,
        name=f"Leave_Depot_{k}"
    )

# Each vehicle should arrive at the depot once
for k in range(len(trucks)):
    model.addConstr(
        gp.quicksum(x[(i, depot1, k)] for i in customers if i != depot1) == 1,
        name=f"Arrive_Depot_{k}"
    )

# Time window constraints
for k in range(len(trucks)):
    for i in locations:
        start_window = locations_df.loc[locations_df['location_code'] == i, 'start_minutes'].values[0]
        end_window = locations_df.loc[locations_df['location_code'] == i, 'end_minutes'].values[0]
        model.addConstr(t[(i, k)] >= start_window, name=f"Start_Window_{i}_{k}")
        model.addConstr(t[(i, k)] <= end_window, name=f"End_Window_{i}_{k}")

# Service time and travel time constraints
for k in range(len(trucks)):
    for i in locations:
        for j in locations:
            if i != j:
                travel_time = travel_matrix.get((i, j), {}).get('travel_time_in_min', 0)
                service_time = service_time_customer if i != depot1 and j != depot1 else service_time_depot
                model.addConstr(
                    t[(j, k)] >= t[(i, k)] + service_time + travel_time - 1e5 * (1 - x[(i, j, k)]),
                    name=f"Service_Time_{i}_{j}_{k}"
                )

# Linking constraint
for k in range(len(trucks)):
    for i in locations:
        for j in locations:
            if i != j:
                model.addConstr(I[k] >= x[(i, j, k)], name=f"Linking_{i}_{j}_{k}")

# Solve the problem
model.optimize()

# Extract solution
solution = {}
if model.status == GRB.OPTIMAL:
    for k in range(len(trucks)):
        solution[trucks[k]['truck_id']] = []
        for i in locations:
            for j in locations:
                if i != j and x[(i, j, k)].x > 0.5:  # Checking if the variable is in the solution
                    solution[trucks[k]['truck_id']].append((i, j, t[(i, k)].x))
else:
    solution = "No optimal solution found."

print(solution)
# Print solver status
print(f"Status: {model.Status}")
