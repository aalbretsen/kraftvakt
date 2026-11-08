"""Regulation logic for Kraftvakt: appliances, variants, penalty and EV chargers.

Pure logic without Home Assistant. The engine takes a snapshot of the
measurements and settings at each decision and returns the commands to carry
out. Time is passed in, so the logic does not depend on a clock.
"""
