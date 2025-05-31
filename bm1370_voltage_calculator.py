def calculate_voltage(frequency, valid_pairs):
    """
    Calculate the required core voltage and estimated hashrate for a given frequency (MHz) for the BM1370 ASIC.
    If voltage exceeds 1350 mV, select the next lowest safe frequency from valid_pairs.
    Returns voltage in millivolts (mV), hashrate in GH/s, and updated valid_pairs.
    Note: Voltage model is based on data for 967–1078 MHz and extrapolated for other frequencies.
    """
    if 400 <= frequency <= 1500:
        voltage_mv = 0.5829 * frequency + 716.65  # Voltage in millivolts
        hashrate = 2.15 * frequency  # Estimated hashrate in GH/s
        
        # Check for critical voltage
        if voltage_mv > 1350:
            # Find the next lowest frequency with safe voltage
            safe_pairs = [(f, v) for f, v in valid_pairs if v <= 1350 and f < frequency]
            if not safe_pairs:
                raise ValueError(f"No safe frequency below {frequency} MHz with voltage <= 1350 mV")
            next_safe_freq, next_safe_voltage = max(safe_pairs, key=lambda x: x[0])
            # Remove the critical frequency-voltage pair
            valid_pairs[:] = [(f, v) for f, v in valid_pairs if f != frequency]
            return next_safe_voltage, 2.15 * next_safe_freq, valid_pairs
        return voltage_mv, hashrate, valid_pairs
    else:
        raise ValueError("Frequency must be between 400 and 1300 MHz")

# Initialize list of valid frequency-voltage pairs
frequencies = list(range(900, 1400, 5))
valid_pairs = [(freq, 0.5829 * freq + 716.65) for freq in frequencies]

# Calculate for frequencies from 400 to 1300 MHz in increments of 10 MHz
for freq in frequencies:
    voltage_mv, hashrate, valid_pairs = calculate_voltage(freq, valid_pairs)
    print(f"Frequency: {freq} MHz, Voltage: {voltage_mv:.1f} mV, Estimated Hashrate: {hashrate:.1f} GH/s")
