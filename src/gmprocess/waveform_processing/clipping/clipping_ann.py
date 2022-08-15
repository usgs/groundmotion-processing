#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module for implementing the Artificial Neural Net model for clipping, as
developed by Kleckner et al. This code is based on Xavier Bellagamba's python
NN implementation of "A neural network for automated quality screening of
ground motion records from small magnitude earthquakes"
DOI: 10.1193/122118EQS292M
"""

import csv
import numpy as np
import os

from gmprocess.utils.constants import DATA_DIR

# Path to model data
NN_PATH = DATA_DIR / "nn_clipping"


class clipNet:
    """
    Class allowing the instantiation and use of simple (1 or 2 layers)
    neural networks
    """

    def __init__(self):
        """
        Instantiate an empty neural network (no weights, functions, or
        biases loaded
        """
        self.n_input = 0
        self.n_neuron_H1 = 0
        self.n_neuron_H2 = -1
        self.n_output = 0
        self.activation_H1 = "NA"
        self.activation_H2 = "NA"
        self.activation_output = "NA"
        self.w_H1 = []
        self.w_H2 = []
        self.b_H1 = []
        self.b_H2 = []
        self.w_output = []
        self.b_output = []

        data_path = os.path.join(NN_PATH, "masterF.txt")
        with open(data_path) as masterF:
            readCSV = csv.reader(masterF)
            for row in readCSV:
                if len(row) == 7:
                    self.n_input = int(row[0])
                    self.n_neuron_H1 = int(row[1])
                    # self.n_neuron_H2 = int(row[3])
                    self.n_output = int(row[5])
                    self.activation_H1 = row[2]
                    # self.activation_H2 = row[4]
                    self.activation_output = row[6]
                elif len(row) == 5:
                    self.n_input = int(row[0])
                    self.n_neuron_H1 = int(row[1])
                    self.n_output = int(row[3])
                    self.activation_H1 = row[2]
                    self.activation_output = row[4]

        masterF.close()

        # Load weights and biases
        # Weights first hidden layer
        data_path = os.path.join(NN_PATH, "weight_1.csv")
        self.w_H1 = np.asarray(loadCSV(data_path))

        # Biases first hidden layer
        data_path = os.path.join(NN_PATH, "bias_1.csv")
        self.b_H1 = np.asarray(loadCSV(data_path))

        # Weights output layer
        data_path = os.path.join(NN_PATH, "weight_output.csv")
        self.w_output = np.asarray(loadCSV(data_path))

        # Biases output layer
        data_path = os.path.join(NN_PATH, "bias_output.csv")
        self.b_output = np.asarray(loadCSV(data_path))

        # Second hidden layer
        if self.n_neuron_H2 != -1:
            # Weights second hidden layer
            data_path = os.path.join(NN_PATH, "weight_2.csv")
            self.w_H2 = np.asarray(loadCSV(data_path))

            # Biases second hidden layer
            data_path = os.path.join(NN_PATH, "bias_2.csv")
            self.b_H2 = np.asarray(loadCSV(data_path))

    def evaluate(self, v_input):
        """
        Use a populated neural network (i.e. from the input, returns the
        classification score or the regression result).

        Args:
            v_input (list or np.array):
                Values to correspond to the following paramters: mag, dist, 6M
                amplitude check, histogram check, ping check.

        Returns:
            np.array: numpy array containing the results.
        """
        # Transform input if required
        if isinstance(v_input, list):
            v_input = np.asarray(v_input)

        t1 = np.array([8.8, 445.8965938, 1.0, 1.0, 1.0])
        t2 = np.array([4, 0.68681514, 0.0, 0.0, 0.0])
        t3 = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        v_input = 2.0 / (t1 - t2) * (v_input - t3)

        v_inter = np.array([])

        # First layer
        if self.activation_H1 == "sigmoid":
            v_inter = sigmoid(np.dot(v_input.T, self.w_H1) + self.b_H1)
        elif self.activation_H1 == "tanh":
            v_inter = tanh(np.dot(v_input.T, self.w_H1) + self.b_H1)
        elif self.activation_H1 == "relu":
            v_inter = relu(np.dot(v_input.T, self.w_H1) + self.b_H1)
        else:
            v_inter = relu(np.dot(v_input.T, self.w_H1) + self.b_H1.T)

        # If second layer exist
        if self.n_neuron_H2 != -1:
            if self.activation_H2 == "sigmoid":
                v_inter = sigmoid(np.dot(v_inter, self.w_H2) + self.b_H2)
            elif self.activation_H2 == "tanh":
                v_inter = tanh(np.dot(v_inter, self.w_H2) + self.b_H2)
            else:
                v_inter = np.dot(v_inter, self.w_H2) + self.b_H2

        # Final layer
        if self.activation_output == "sigmoid":
            v_inter = sigmoid(np.dot(v_inter, self.w_output) + self.b_output)
        elif self.activation_output == "tanh":
            v_inter = tanh(np.dot(v_inter, self.w_output) + self.b_output)
        else:
            v_inter = sigmoid(np.dot(v_inter, self.w_output) + self.b_output)

        return v_inter


def loadCSV(data_path, row_ignore=0, col_ignore=0):
    """
    Load csv files from a given path and returns a list of list.
    For all imported data, check if is a number. If so, returns a
    float. If not, returns a string.

    Args:
        data_path (string):
            path to the csv to load.
        row_ignore (int):
            number of rows to ignore.
        col_ignore (int):
            number of columns to ignore.

    Returns:
        list of list: containing the data from the csv
    """

    M = []
    with open(data_path) as csvfile:
        readCSV = csv.reader(csvfile)

        # Skip header
        for i in range(row_ignore):
            next(csvfile)

        for row in readCSV:
            # Input vector
            single_line = []
            for i in range(col_ignore, len(row)):
                if isNumber(row[i]):
                    single_line.append(float(row[i]))
                else:
                    single_line.append(row[i])
            M.append(single_line)

    return M


def sigmoid(v_input):
    """
    Performs a sigmoid operation on the input (1/(e(-x)+1))

    Args:
        v_input (float):
            a number defined on R (real).

    Returns:
        float: sigmoid result (a number between 0 and 1).
    """
    v_act = []
    for x in v_input:
        v_act.append(1.0 / (1 + np.exp(-x)))
    return v_act


def tanh(v_input):
    """
    Performs a hyperbolic tangent operation on the input (2/(e(2x)+1))

    Args:
        v_input (float):
            a number defined on R (real).

    Returns:
        float: tanh result (a number between -1 and 1).
    """
    v_act = []
    for x in v_input:
        v_act.append(np.tanh(x))
    return v_act


def relu(v_input):
    """
    Performs a hyperbolic tangent operation on the input (2/(e(2x)+1))

    Args:
        v_input (float):
            a number defined on R (real).

    Returns:
        float: tanh result (a number between -1 and 1).
    """
    v_act = []
    for x in v_input:
        v_act.append(np.maximum(0.0, x))
    return v_act


def isNumber(s):
    """
    Check if given input is a number.

    Args:
        s (any type):
            Data to test.

    Returns:
        bool: True if is a number, False if isn't
    """
    try:
        float(s)
        return True

    except ValueError:
        return False
