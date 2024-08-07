import pandas as pd
from haversine import haversine
import gurobipy as gp
from gurobipy import GRB
import folium


def read_data(file_path):
    df = pd.read_csv(file_path)
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


def build_model(places, distance_matrix):
    n = len(places)
    model = gp.Model("TSP")

    # Decision variables: x[i,j] = 1 if edge (i,j) is in the tour
    x = model.addVars(n, n, vtype=GRB.BINARY, name='x')

    # Decision variables: s[i] for MTZ formulation
    s = model.addVars(n, vtype=GRB.INTEGER, name='s')

    # Objective function: minimize the total travel distance
    model.setObjective(gp.quicksum(distance_matrix[i][j] * x[i, j] for i in range(n) for j in range(n)), GRB.MINIMIZE)

    # Constraints: Each city must be departed exactly once
    model.addConstrs(gp.quicksum(x[i, j] for j in range(n) if i != j) == 1 for i in range(n))

    # Constraints: Each city must be arrived at exactly once
    model.addConstrs(gp.quicksum(x[i, j] for i in range(n) if i != j) == 1 for j in range(n))

    # Subtour elimination constraints (MTZ formulation)
    model.addConstrs((s[i] - s[j] + n * x[i, j] <= n - 1) for i in range(1, n) for j in range(1, n) if i != j)

    # Optimize the model
    model.optimize()

    return model, x


def solve_tsp(model, x, places):
    if model.status == GRB.OPTIMAL:
        n = len(places)
        optimal_route = []
        start = 0
        current = start
        while True:
            optimal_route.append(places[current])
            next_city = None
            for j in range(n):
                if x[current, j].X > 0.5:
                    next_city = j
                    break
            if next_city is None:
                break
            current = next_city
            if current == start:
                break
        optimal_route.append(places[start])  # Return to the starting place

        total_distance = model.objVal

        print("Optimal Route:", " -> ".join(optimal_route))
        print("Total Distance:", total_distance)

        return optimal_route, total_distance
    else:
        print("No optimal solution found.")
        return None, None


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
    m.save('../output/tsp_route_2.html')


if __name__ == "__main__":
    data_file_path = '../data/sample_tsp_30city.csv'
    places, coordinates = read_data(data_file_path)
    distance_matrix = calculate_distance_matrix(coordinates)
    model, x = build_model(places, distance_matrix)
    optimal_route, total_distance = solve_tsp(model, x, places)

    if optimal_route:
        plot_route(optimal_route, coordinates, places)
    print(f'Execution complete')
