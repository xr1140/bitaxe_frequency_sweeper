def calculate_voltage(frequency):
    """
    Calculate the required core voltage and estimated hashrate for a given frequency (MHz) for the BM1370 ASIC.
    Returns voltage in millivolts (mV) and hashrate in GH/s.
    Note: Voltage model is based on data for 992–1089 MHz and extrapolated for other frequencies.
    """
    if 400 <= frequency <= 1300:
        voltage_mv = 0.4506 * frequency + 842.97  # Voltage in millivolts
        hashrate = 2.15 * frequency  # Estimated hashrate in GH/s
        return voltage_mv, hashrate
    else:
        raise ValueError("Frequency must be between 400 and 1300 MHz")

# Calculate for frequencies from 400 to 1300 MHz in increments of 10 MHz
frequencies = range(650, 1080, 20)
for freq in frequencies:
    voltage_mv, hashrate = calculate_voltage(freq)
    print(f"Frequency: {freq} MHz, Voltage: {voltage_mv:.1f} mV, Estimated Hashrate: {hashrate:.1f} GH/s")
