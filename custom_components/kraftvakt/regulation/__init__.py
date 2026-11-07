"""Regulation logic for Kraftvakt (REG, STR, APP-007, APP-009, LAD-011 to LAD-030).

Pure logic without Home Assistant (B4). The engine takes a snapshot of the
measurements and settings at each decision and returns the commands to carry
out. Time is passed in, so the logic does not depend on a clock (B5).
"""
