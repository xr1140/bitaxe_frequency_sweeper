def calculate_voltage(frequency):
    """
    Calculate the required core voltage for a given frequency (MHz) for the BM1370 ASIC.
    Returns voltage in millivolts (mV).
    """
    if 400 <= frequency < 550:
        voltage_v = 0.9 + 0.00133333 * (frequency - 400)
    elif 550 <= frequency <= 1000:
        voltage_v = 1.1 + 0.000437778 * (frequency - 550)
    elif 1000 < frequency <= 1300:
        voltage_v = 1.297 + 0.0004 * (frequency - 1000)
    else:
        raise ValueError("Frequency must be between 400 and 1300 MHz")
    return voltage_v * 1000  # Convert to mV

def calculate_hashrate(frequency):
    """
    Estimate the average hashrate (GH/s) for a given frequency (MHz) for the BM1370 ASIC.
    """
    return 2.1085 * frequency

# Generate table for 400–1300 MHz in 50 MHz increments
frequencies = list(range(400, 1350, 10))  # Up to 1300 MHz
print("BM1370 Voltage and Hashrate Estimates (400–1300 MHz, 50 MHz increments):")
print("Frequency (MHz) | Voltage (mV) | Est. Hashrate (GH/s)")
print("-" * 48)
for freq in frequencies:
    try:
        voltage = calculate_voltage(freq)
        hashrate = calculate_hashrate(freq)
        print(f"{freq:15} | {voltage:.1f}       | {hashrate:.1f}")
    except ValueError as e:
        print(f"{freq:15} | Error: {e}")
