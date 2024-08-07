# 1.Travelling-Salesman-Problem
## Overview

This project addresses the Traveling Salesman Problem (TSP) using the Mixed-Integer Linear Programming (MILP) approach with Gurobi. The goal is to find the optimal route that visits each city exactly once and returns to the starting city, minimizing the total travel distance.

## Features

- **Data Reading**: Loads city names and their coordinates from a CSV file.
- **Distance Matrix Calculation**: Computes the distance matrix using the Haversine formula to account for geographical distances.
- **Model Building**: Constructs and solves the TSP model using Gurobi, employing the MTZ (Miller-Tucker-Zemlin) formulation for subtour elimination.
- **Parameter Tuning**: Includes advanced tuning of Gurobi parameters to enhance optimization performance:
  - **Warm Start**: Initializes the model with a feasible solution to speed up convergence.
  - **MIP Focus**: Adjusts the solver's focus to balance between finding feasible solutions and improving optimality.
  - **Time Limit**: Sets a maximum time limit for optimization to control the computational effort.
  - **Heuristics**: Sets the proportion of heuristic solutions to be used to guide the search process.
  - **Cuts**: Specifies the type and number of cuts to be applied for speeding up the solution process.
  - **Presolve**: Applies advanced preprocessing techniques to simplify the model before solving.
- **Route Extraction**: Extracts and prints the optimal route and total distance.
- **Route Visualization**: Generates an interactive map displaying the optimal route using Folium.

## Requirements

- Python 3.x
- Pandas
- Gurobi
- Haversine
- Folium

## Installation

To install the required Python packages, you can use pip:

```bash
pip install pandas gurobipy haversine folium
```

## Usage

1. **Prepare Data File**: Ensure your CSV file (e.g., `sample_tsp_30city.csv`) is in the `../data/` directory. The file should have the following columns:
   - `Place_Name`: Name of the place (city)
   - `Latitude`: Latitude of the place
   - `Longitude`: Longitude of the place

2. **Run the Script**: Execute the script to read the data, solve the TSP, and visualize the route:

   ```bash
   python tsp_solver.py
   ```

3. **Output**:
   - **Optimal Route**: The script will print the optimal route and the total distance.
   - **Map Visualization**: The script will generate an HTML file (`tsp_route_2.html`) in the `../output/` directory with an interactive map displaying the route.

# 2.Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)

## Overview

This project addresses the Capacitated Vehicle Routing Problem with Time Windows (CVRPTW) using Mixed-Integer Linear Programming (MILP) with Gurobi. The objective is to determine the optimal routes for a fleet of vehicles to deliver goods to customers, considering vehicle capacities and customer time windows while minimizing total travel distance and fixed costs.

## Features

- **Data Loading**: Loads location, order, travel matrix, and truck data from CSV and Excel files.
- **Time Window Conversion**: Converts time window information into minutes for easier processing.
- **Model Building**: Constructs and solves the CVRPTW model using Gurobi with the following features:
  - **Decision Variables**: Includes binary variables for route decisions and continuous variables for time management.
  - **Objective Function**: Minimizes total distance and fixed costs associated with vehicle usage.
  - **Constraints**: Incorporates flow balancing, demand satisfaction, depot constraints, time windows, and service time constraints.
- **Solution Extraction**: Extracts and prints the optimal routes for each vehicle.

## Requirements

- Python 3.x
- Pandas
- Gurobi

## Installation

To install the required Python packages, you can use pip:

```bash
pip install pandas gurobipy
```

Ensure that you have Gurobi installed and properly configured. Follow Gurobi's installation guide if needed.

## Usage

1. **Prepare Data Files**: Ensure your data files are in the `../data/MT-CVRPTW_inputs/` directory. The files should include:
   - `locations.csv`: Location data with columns for location code and loading/unloading time windows.
   - `order_list.xlsx`: Orders with destination codes and weights.
   - `travel_matrix.csv`: Travel distances and times between locations.
   - `trucks.csv`: Truck data with maximum weights and IDs.

2. **Run the Script**: Execute the script to solve the CVRPTW and print the solution:

```bash
python cvrptw_solver.py
```

## Output

- **Solution**: The script will print the optimal routes and associated times for each vehicle.

