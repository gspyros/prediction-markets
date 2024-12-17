import math
import numpy as np

def get_prices(net_positions, beta=0.01):
    """
    Calculate prices based on net positions using an exponential function.
    """
    net_positions = np.array(net_positions)  # Convert to NumPy array
    exps = np.exp(beta * net_positions)
    exps_sum = np.sum(exps)
    prices = exps / exps_sum
    return prices.tolist()  # Convert back to list if needed


def get_cost_of_trade(net_positions, instr_name, delta=1, beta=0.01):
    """
    Calculate the cost of trading a specified number of units of an instrument.
    """
    adjusted_net_positions = net_positions.copy()
    adjusted_net_positions[instr_name] += delta

    values = np.array(list(adjusted_net_positions.values()))
    ln_arg = np.sum(np.exp(beta * values)) / np.sum(np.exp(beta * np.array(list(net_positions.values()))))
    cost = (1 / beta) * math.log(ln_arg)
    return cost