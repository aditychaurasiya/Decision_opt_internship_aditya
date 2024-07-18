import pandas as pd
from haversine import haversine
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import gurobipy as gp
from gurobipy import GRB
import time
import folium
import os

# Create the output directory if it doesn't exist
if not os.path.exists("output"):
    os.makedirs("output")

def read_data(file_path, num_places):
    df = pd.read_csv(file_path)
    df = df.head(num_places)
    print(df)
    places = df['Place_Name'].unique().tolist()
    coordinates = list(zip(df['Latitude'], df['Longitude']))
    return places, coordinates

def calculate_distance_matrix(coordinates):
    n = len(coordinates)
    distance_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = haversine(coordinates[i], coordinates[j])
    return distance_matrix

def solve_tsp_ortools(distance_matrix):
    """Solves the TSP problem using OR-Tools and returns the solution."""
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)  # Convert to integer for OR-Tools

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Extract the solution route.
    if solution:
        index = routing.Start(0)
        plan = []
        total_distance = 0
        while not routing.IsEnd(index):
            plan.append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_distance += routing.GetArcCostForVehicle(previous_index, index, 0) / 1000.0  # Convert back to float
        plan.append(manager.IndexToNode(index))
        return plan, total_distance
    else:
        return None, None

def build_gurobi_model(places, distance_matrix, initial_solution):
    """Build the TSP model using Gurobi with an initial solution as a warm start."""
    n = len(places)
    model = gp.Model('TSP')

    # Define variables
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    u = model.addVars(n, vtype=GRB.INTEGER, name="u")

    # Set objective
    model.setObjective(gp.quicksum(distance_matrix[i][j] * x[i, j] for i in range(n) for j in range(n)), GRB.MINIMIZE)

    # Add constraints
    model.addConstrs(gp.quicksum(x[i, j] for j in range(n) if j != i) == 1 for i in range(n))
    model.addConstrs(gp.quicksum(x[j, i] for j in range(n) if j != i) == 1 for i in range(n))
    model.addConstrs((u[i] - u[j] + n * x[i, j] <= n - 1) for i in range(1, n) for j in range(1, n) if i != j)

    # Warm start: set initial solution
    if initial_solution:
        for i in range(n - 1):
            x[initial_solution[i], initial_solution[i + 1]].start = 1
        x[initial_solution[-1], initial_solution[0]].start = 1

    # Save the formulation to a file
    model.write("tsp2.lp")

    return model, x

def extract_solution(model, x, n):
    """Extract the solution from the Gurobi model."""
    model.optimize()

    if model.status == GRB.OPTIMAL:
        solution = []
        for i in range(n):
            for j in range(n):
                if x[i, j].X > 0.5:
                    solution.append((i, j))
        return solution
    else:
        print("No optimal solution found.")
        return None

def plot_route(optimal_route, coordinates, places):
    # Create a map centered around the first place
    start_coord = coordinates[places.index(optimal_route[0])]
    m = folium.Map(location=start_coord, zoom_start=6)

    # Add markers for each place with tooltips
    for idx in optimal_route:
        folium.Marker(
            location=coordinates[places.index(idx)],
            popup=coordinates[places.index(idx)],
            tooltip=coordinates[places.index(idx)]
        ).add_to(m)

    # Add lines to show the route
    route_coords = [coordinates[places.index(i)] for i in optimal_route]
    folium.PolyLine(locations=route_coords, color='blue').add_to(m)

    # Save the map
    m.save('output/tsp_route_warm2.html')

if __name__ == '__main__':
    data_file_path = r'C:\Users\adity\tsp\tsp\data\tsp_input.csv'
    num_places = 40

    start_time = time.time()  # Start timing
    places, coordinates = read_data(data_file_path, num_places)
    distance_matrix = calculate_distance_matrix(coordinates)
    initial_solution_indices, total_distance = solve_tsp_ortools(distance_matrix)

    if initial_solution_indices:
        initial_solution = initial_solution_indices
        print("Initial Solution (OR-Tools):", " -> ".join(map(str, initial_solution)))
        print("Total Distance (Objective Value):", total_distance)

        # Build and solve the Gurobi model with the warm start
        model, x = build_gurobi_model(places, distance_matrix, initial_solution)
        tsp_solution = extract_solution(model, x, len(places))

        if tsp_solution:
            optimal_route = [places[i[0]] for i in tsp_solution]
            optimal_route.append(optimal_route[0])  # Return to the starting place
            print("Optimal Route (Gurobi):", " -> ".join(optimal_route))
            plot_route(optimal_route, coordinates, places)
    else:
        print("No solution found using OR-Tools.")

    end_time = time.time()  # End timing
    execution_time = end_time - start_time
    print(f'Execution complete')
    print(f'Execution time: {execution_time} seconds')
