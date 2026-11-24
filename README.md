# Overview

A set of minimal and beginner-friendly implementations
of quantum crypto algorithms based on qiskit.
We use statevectors and require no backend access to a real QPU or a simulator.

- Quantum Key Distribution Basics 

# Installation

Python and qiskit are required to run the scripts.  Follow IBM's
installation guide on
https://quantum.cloud.ibm.com/docs/en/guides/install-qiskit.

# Algorithms and Usage

## Quantum Key Distribution Basics

This script simulates the basics of quantum key distribution (QKD).
This includes preparing a random binary key along with a randomly
chosen signalling base for each bit. We implement a simple channel
model and the detection at the receiver.  Two postprocessing steps are
currently implemented: key sifting and qber estimation. Further
postprocessing will be implemented in the future.
