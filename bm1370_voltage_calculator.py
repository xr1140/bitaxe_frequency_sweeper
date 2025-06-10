import csv
import argparse

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
        raise ValueError("Frequency must be between 400 and 1500 MHz")

def process_frequencies(start_freq, end_freq, step=5, csv_filename=None):
    """
    Process frequencies in the given range and output results to screen and optionally to CSV.
    """
    # Initialize list of valid frequency-voltage pairs
    frequencies = list(range(start_freq, end_freq, step))
    valid_pairs = [(freq, 0.5829 * freq + 716.65) for freq in frequencies]

    # Write CSV header if file will be created
    if csv_filename:
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Voltage", "Frequency"])

    # Calculate for frequencies in the specified range
    for freq in frequencies:
        voltage_mv, hashrate, valid_pairs = calculate_voltage(freq, valid_pairs)
        print(f"Frequency: {freq} MHz, Voltage: {voltage_mv:.1f} mV, Estimated Hashrate: {hashrate:.1f} GH/s")
        
        # Write to CSV if filename is provided
        if csv_filename:
            with open(csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([f"{int(voltage_mv)}", freq])

def main():
    """
    Main function to parse command-line arguments and run the frequency processing.
    """
    parser = argparse.ArgumentParser(description="Calculate ASIC voltage and hashrate for frequency range")
    parser.add_argument("--start-freq", type=int, default=600, help="Starting frequency in MHz (default: 600)")
    parser.add_argument("--end-freq", type=int, default=1000, help="Ending frequency in MHz (default: 1000)")
    parser.add_argument("--csv-file", type=str, default="values0.csv", help="Output CSV file name (optional)")
    args = parser.parse_args()

    process_frequencies(args.start_freq, args.end_freq, csv_filename=args.csv_file)

if __name__ == "__main__":
    main()