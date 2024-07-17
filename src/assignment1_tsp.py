import pulp

# Define the problem
# Example data
orders = [1, 2, 3]  # List of orders
warehouses = [1, 2]  # List of warehouses
items = [1, 2]  # List of items
distances = {
    (1, 1): 10, (1, 2): 20,
    (2, 1): 15, (2, 2): 25,
    (3, 1): 30, (3, 2): 35,
}  # Distances between orders and warehouses
quantities_o = {
    (1, 1): 5, (1, 2): 10,
    (2, 1): 7, (2, 2): 8,
    (3, 1): 3, (3, 2): 4,
}  # Quantities needed for each order and item
quantities_w = {
    (1, 1): 20, (1, 2): 30,
    (2, 1): 25, (2, 2): 35,
}  # Quantities available at each warehouse for each item
M = 1000  # A large number for penalty

# for noSplitO and okSplitO
noSplitO = [1, 2]  # Orders that cannot be split
okSplitO = [3]  # Orders that can be split

# Decision variables
X = pulp.LpVariable.dicts("X", [(o, w) for o in orders for w in warehouses], cat='Binary')
K = pulp.LpVariable.dicts("K", [(o, i, w) for o in orders for i in items for w in warehouses], cat='Binary')
Z = pulp.LpVariable.dicts("Z", orders, cat='Binary')
Y = pulp.LpVariable.dicts("Y", [(o, i, w) for o in orders for i in items for w in warehouses], cat='Binary')

# Objective function
prob += pulp.lpSum(distances[o, w] * X[o, w] for o in orders for w in warehouses) + \
        pulp.lpSum(distances[o, w] * Y[o, i, w] for o in orders for i in items for w in warehouses) + \
        pulp.lpSum(M * Z[o] for o in orders), "Minimize_Traveling_Cost_and_Penalty"

# Constraints
for o in orders:
    if o in noSplitO:
        prob += pulp.lpSum(X[o, w] for w in warehouses) + Z[o] == 1, f"Order_{o}_Fulfilled_or_Not"
    elif o in okSplitO:
        for i in items:
            prob += pulp.lpSum(K[o, i, w] for w in warehouses) + Z[o] == 1, f"Order_{o}_Item_{i}_Fulfilled_or_Not"

for w in warehouses:
    for i in items:
        prob += (pulp.lpSum(quantities_o[o, i] * X[o, w] for o in noSplitO) +
                 pulp.lpSum(quantities_o[o, i] * K[o, i, w] for o in okSplitO) <= quantities_w[w, i],
                 f"Warehouse_{w}_Item_{i}_Quantity_Limit")

for o in okSplitO:
    for i in items:
        for w in warehouses:
            prob += Y[o, i, w] >= K[o, i, w], f"Connect_Y_and_X_for_Order_{o}_Item_{i}_Warehouse_{w}"

# Solve the problem
prob.solve()

# Print the results
print("Status:", pulp.LpStatus[prob.status])
for var in prob.variables():
    print(var.name, "=", var.varValue)
print("Total Cost =", pulp.value(prob.objective))
