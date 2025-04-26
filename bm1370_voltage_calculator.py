def calculate_voltage(frequency):
    """
    Calculate the required core voltage for a given frequency (MHz) for the BM1370 ASIC.
    Returns voltage in volts.
    """
    if 400 <= frequency < 550:
        return 0.9 + 0.00133333 * (frequency - 400)
    elif 550 <= frequency <= 1000:
        return 1.1 + 0.000404444 * (frequency - 550)
    elif 1000 < frequency <= 2005:
        return 1.282 + 0.0026 * (frequency - 1000)
    else:
        raise ValueError("Frequency must be between 400 and 1005 MHz")

# Example usage
frequencies = [400, 550, 650, 700, 750, 800, 850, 900, 950, 1000, 1005, 1050, 1075]
for freq in frequencies:
    voltage = calculate_voltage(freq)
    hashrate = 2.04 * freq  # Estimated hashrate in GH/s
    print(f"Frequency: {freq} MHz, Voltage: {voltage:.4f} V, Estimated Hashrate: {hashrate:.1f} GH/s")
