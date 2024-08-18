import haversine as hv
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
from itertools import combinations
import time
import logging
import folium
import random
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
random.seed(1517)


def main():
    start_time = time.time()

    try:
        # Load data
        logging.info("Loading data from CSV")
        data_path = os.path.join('..', 'data', 'tsp_input.csv')
        data = pd.read_csv(data_path)

        # Prepare data: Extract capitals and their coordinates
        logging.info("Extracting capitals and coordinates")
        capitals, coordinates = [], {}
        for ind, row in data.iterrows():
            capital = row['Place_Name']
            capitals.append(capital)
            coordinates[capital] = (float(row['Latitude']), float(row['Longitude']))

        # Solve the optimization model
        logging.info("Solving the TSP model")
        tour = solve_tsp_model(capitals, coordinates)

        # Display the optimal route on a map
        logging.info("Mapping the solution")
        map = plot_solution_on_map(tour, coordinates)

        # Save the map
        output_path = os.path.join('..', 'output', 'tsp_lazy.html')
        map.save(output_path)

        logging.info(f"Runtime: {round(time.time() - start_time)} seconds")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


def solve_tsp_model(capitals, coordinates):
    """
    Solve the Traveling Salesman Problem (TSP) using Gurobi.

    Parameters:
        capitals (list): List of city names.
        coordinates (dict): Dictionary of city coordinates.

    Returns:
        list: Ordered list of cities representing the optimal tour.
    """
    # Calculate distances between all pairs of capitals
    logging.info("Calculating distances between cities")
    dist = {(c1, c2): distance(c1, c2, coordinates) for c1, c2 in combinations(capitals, 2)}

    # Create and solve the model
    logging.info("Building the optimization model")
    m = gp.Model()

    # Variables: is city 'i' adjacent to city 'j' on the tour?
    logging.info("Adding variables")
    vars = m.addVars(dist.keys(), obj=dist, vtype=GRB.BINARY, name='x')

    # Symmetric direction: use dict.update to alias variable with new key
    logging.info("Setting symmetric constraints")
    vars.update({(j, i): vars[i, j] for i, j in vars.keys()})

    # Constraints: two edges incident to each city
    logging.info("Adding constraints")
    m.addConstrs(vars.sum(c, '*') == 2 for c in capitals)

    # Optimize the model using a callback for subtour elimination
    logging.info("Optimizing the model")
    m._vars = vars
    m.Params.lazyConstraints = 1
    m.Params.LogToConsole = 0
    m.optimize(lambda model, where: subtourelim(model, where, capitals))

    # Retrieve the solution
    logging.info("Retrieving the solution")
    vals = m.getAttr('x', vars)
    selected = gp.tuplelist((i, j) for i, j in vals.keys() if vals[i, j] > 0.5)

    # Ensure a valid tour
    logging.info("Finding the optimal tour")
    tour = subtour(selected, capitals)
    assert len(tour) == len(capitals), f"Tour does not include all capitals: {len(tour)} vs {len(capitals)}"

    # Dispose of the model and environment
    m.dispose()
    gp.disposeDefaultEnv()

    return tour


def plot_solution_on_map(tour, coordinates):
    """
    Plot the optimal TSP route on a map using Folium with different colored markers for each city.

    Parameters:
        tour (list): Ordered list of cities representing the optimal tour.
        coordinates (dict): Dictionary of city coordinates.

    Returns:
        folium.Map: Map object with the plotted route.
    """
    # Initialize the map centered around the first city in the tour
    map = folium.Map(location=[coordinates[tour[0]][0], coordinates[tour[0]][1]], zoom_start=4)

    # List of colors to choose from
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige',
              'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue',
              'lightgreen', 'gray', 'black', 'lightgray']

    points = []
    for city in tour:
        loc = coordinates[city]
        points.append(loc)
        # Randomly select a color for each city marker
        color = random.choice(colors)
        # Add city markers with tooltips and different colored map signs
        folium.Marker(loc, tooltip=city, icon=folium.Icon(icon="map-sign", color=color)).add_to(map)
    points.append(points[0])  # to create a closed loop

    # Draw the route
    folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(map)

    return map


def distance(city1, city2, coordinates):
    """
    Calculate the Haversine distance between two cities based on their coordinates.
    """
    c1 = coordinates[city1]
    c2 = coordinates[city2]
    dist = round(hv.haversine(c1, c2, hv.Unit.KILOMETERS), 2)
    return dist


def subtourelim(model, where, capitals):
    """
    Callback function to eliminate subtours during optimization.
    """
    if where == GRB.Callback.MIPSOL:
        # Extract the solution
        vals = model.cbGetSolution(model._vars)
        selected = gp.tuplelist((i, j) for i, j in model._vars.keys() if vals[i, j] > 0.5)

        # Find the shortest subtour
        tour = subtour(selected, capitals)
        if len(tour) < len(capitals):
            # Add subtour elimination constraints
            model.cbLazy(gp.quicksum(model._vars[i, j] for i, j in combinations(tour, 2))
                         <= len(tour) - 1)


def subtour(edges, capitals):
    """
    Given a tuplelist of edges, find the shortest subtour.
    """
    unvisited = capitals[:]
    cycle = capitals[:]  # Dummy - guaranteed to be replaced
    while unvisited:  # true if list is non-empty
        thiscycle = []
        neighbors = unvisited
        while neighbors:
            current = neighbors[0]
            thiscycle.append(current)
            unvisited.remove(current)
            neighbors = [j for i, j in edges.select(current, '*') if j in unvisited]
        if len(thiscycle) <= len(cycle):
            cycle = thiscycle  # New shortest subtour
    return cycle


if __name__ == "__main__":
    main()
