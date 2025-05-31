import requests
import time
import signal
import sys
import argparse
import re
from datetime import datetime
import os
import csv

# ANSI Color Codes
GREEN = "\033[32m"
ORANGE = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"

# Configuration dictionary with detailed comments for each parameter
CONFIG = {
    # Duration of each test run in seconds (default: 600s = 10 minutes).
    # Determines how long the Bitaxe runs at each voltage-frequency pair before advancing.
    # Longer durations provide more stable hashrate measurements but increase total test time.
    # Used in sweep and single-voltage modes; monitor mode runs indefinitely.
    "run_duration": 600,

    # Interval between logging system data to readings.csv in seconds (default: 10s).
    # Controls how frequently metrics (hashrate, temperature, power, etc.) are recorded.
    # Smaller intervals increase log granularity but may increase file size and I/O overhead.
    "log_interval": 10,

    # Interval between fetching and displaying system status in seconds (default: 10s).
    # Determines how often the console updates with current metrics and timers.
    # Smaller intervals provide more frequent updates but may increase API call frequency.
    "status_interval": 10,

    # Warning threshold for chip temperature in °C (default: 65°C).
    # Triggers orange-colored console output when chip temperature exceeds this value.
    # Helps identify potential overheating risks before reaching critical levels.
    "max_temp_warning": 65,

    # Critical threshold for chip temperature in °C (default: 67°C).
    # Triggers test termination and reduces voltage/frequency if exceeded.
    # Protects the Bitaxe from damage due to excessive chip temperature.
    "max_temp_critical": 67,

    # Warning threshold for voltage regulator temperature in °C (default: 80°C).
    # Triggers orange-colored console output when VR temperature exceeds this value.
    # Indicates potential thermal stress on the voltage regulator.
    "max_vrtemp_warning": 80,

    # Critical threshold for voltage regulator temperature in °C (default: 90°C).
    # Triggers test termination and reduces voltage/frequency if exceeded.
    # Protects the voltage regulator from overheating damage.
    "max_vrtemp_critical": 90,

    # Warning threshold for power consumption in watts (default: 38W).
    # Triggers orange-colored console output when power exceeds this value.
    # Helps monitor excessive power draw that may indicate inefficiency or risk.
    "max_power_warning": 38,

    # Critical threshold for power consumption in watts (default: 44W).
    # Triggers test termination and reduces voltage/frequency if exceeded.
    # Prevents damage or instability due to excessive power consumption.
    "max_power_critical": 44,

    # Minimum allowable frequency in MHz (default: 400 MHz).
    # Ensures the Bitaxe does not operate below this frequency to maintain stability.
    # Applied to all frequency settings, including sweeps and CSV-derived values.
    "min_frequency": 400,

    # Minimum allowable core voltage in mV (default: 1000 mV).
    # Ensures the Bitaxe does not operate below this voltage to prevent instability.
    # Applied to all voltage settings, including sweeps and CSV-derived values.
    "min_core_voltage": 1000,

    # Margin below critical thresholds for advancing settings in °C or watts (default: 2).
    # In monitor mode with -values, allows advancing to higher voltage-frequency pairs
    # only if metrics (temperature, VR temperature, power) are below critical thresholds by this margin.
    "critical_advance_margin": 2,

    # Number of readings required before advancing settings in monitor mode (default: 3).
    # Ensures stable measurements before increasing voltage/frequency from values.csv.
    # Prevents premature adjustments due to transient metrics.
    "readings_to_advance": 3,

    # Delay after a critical fallback before advancing settings in seconds (default: 7200s = 120 minutes).
    # In monitor mode with -values, prevents advancing to higher voltage-frequency pairs
    # until this time has elapsed since a critical condition triggered a reduction.
    # Ensures system stability after a critical event.
    "advance_delay": 7200,

    # Frequency range in MHz to test above and below the center frequency (default: 10 MHz).
    # Defines the sweep width around the initial or calculated frequency in sweep mode.
    # Ignored in monitor mode. Larger ranges test more frequencies but increase test time.
    "range": 10,

    # Frequency step size in MHz for sweeps (default: 2 MHz).
    # Determines the increment between tested frequencies within the range.
    # Ignored in monitor mode. Smaller steps increase granularity but extend test duration.
    "step": 2,

    # Number of consecutive identical hashrate readings to trigger a reboot (default: None).
    # If set, reboots the Bitaxe after detecting the specified number of identical hashrates.
    # Helps recover from potential hangs or stalls; disabled if None.
    "reboot": None,
}

# Global variables
system_info = {
    "frequency": None,
    "power": None,
    "voltage": None,
    "current": None,
    "temp": None,
    "vrTemp": None,
    "hashRate": None,
    "coreVoltage": None,
    "coreVoltageActual": None,
    "jth": None
}
global_min_values = {key: float('inf') for key in system_info}
global_max_values = {key: float('-inf') for key in system_info}
is_interrupted = False
critical_temp_reached = False
initial_frequency = None
initial_core_voltage = None
bitaxe_ip = None
readings_filename = None
summaries_filename = None
values_found_filename = None
best_hashrate = 0.0
best_frequency = None
best_voltage = None
best_hashrates = {}
value_pairs = []
last_fallback_time = None
last_fallback_voltage = None

def signal_handler(sig, frame):
    global is_interrupted
    is_interrupted = True
    print(ORANGE + "\nStopping status logger..." + RESET)

signal.signal(signal.SIGINT, signal_handler)

def validate_ip(ip):
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    if not re.match(pattern, ip):
        raise ValueError("Invalid IP address format. Use format like 192.168.2.205")
    return f"http://{ip}"

def calculate_bm1370_frequency(voltage):
    frequency = (voltage - 842.97) / 0.4506
    return max(CONFIG["min_frequency"], int(frequency))

def get_frequency_for_voltage(voltage, values_file):
    if values_file and value_pairs:
        for v, f in value_pairs:
            if v == voltage:
                return f
    return calculate_bm1370_frequency(voltage)

def read_values_csv(filename):
    global value_pairs
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            value_pairs = []
            for row in reader:
                if not row or row[0].strip().startswith('#'):
                    continue
                if len(row) >= 2:
                    try:
                        voltage = int(row[0])
                        frequency = int(row[1])
                        value_pairs.append((voltage, frequency))
                    except ValueError as e:
                        print(ORANGE + f"Skipping invalid row in {filename}: {row} (Error: {e})" + RESET)
                        continue
        value_pairs.sort(key=lambda x: x[0])
        if not value_pairs:
            raise ValueError("Values CSV file is empty or contains no valid voltage-frequency pairs")
        print(GREEN + f"Loaded {len(value_pairs)} voltage-frequency pairs from {filename}" + RESET)
    except FileNotFoundError:
        raise FileNotFoundError(f"Values CSV file '{filename}' not found")
    except Exception as e:
        raise ValueError(f"Error reading values CSV file: {e}")

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Bitaxe status logger for monitoring hashrate, temperature, and power. Configuration values (e.g., test duration, safety thresholds) are defined in the script's CONFIG dictionary and can be viewed in the code. Some options below override these defaults."
    )
    parser.add_argument(
        "-v", "--voltage",
        type=int,
        help="Core voltage in mV (minimum 1000 mV, required for monitor mode or single voltage tests)"
    )
    parser.add_argument(
        "-start", "--start_voltage",
        type=int,
        help="Starting core voltage in mV for voltage sweep (minimum 1000 mV)"
    )
    parser.add_argument(
        "-stop", "--stop_voltage",
        type=int,
        help="Ending core voltage in mV for voltage sweep (minimum 1000 mV)"
    )
    parser.add_argument(
        "-f", "--frequency",
        type=int,
        help="Initial frequency in MHz (minimum 400 MHz, required for monitor mode or single voltage tests without -values)"
    )
    parser.add_argument(
        "-ip", "--ip_address",
        type=str,
        required=True,
        help="Bitaxe IP address (e.g., 192.168.2.205)"
    )
    parser.add_argument(
        "-range",
        type=int,
        default=CONFIG["range"],
        help=f"Frequency range in MHz to test above and below the initial or calculated frequency (default: {CONFIG['range']} MHz, ignored in monitor mode). Controls the sweep width around the center frequency."
    )
    parser.add_argument(
        "-step",
        type=int,
        default=CONFIG["step"],
        help=f"Frequency step size in MHz (default: {CONFIG['step']} MHz, ignored in monitor mode). Determines the increment between tested frequencies in the sweep."
    )
    parser.add_argument(
        "-reboot",
        type=int,
        default=CONFIG["reboot"],
        help=f"Number of consecutive identical hashrate readings to trigger a reboot (default: {CONFIG['reboot']}, disabled if None). Helps recover from potential hangs or stalls."
    )
    parser.add_argument(
        "-m", "--monitor",
        action="store_true",
        help="Run in monitor-only mode at the specified voltage and frequency indefinitely (sets range=0, step=0). Adjusts settings based on values.csv if provided."
    )
    parser.add_argument(
        "-values",
        type=str,
        help="Path to values.csv file with voltage, frequency, and hashrate (used in monitor mode or with -start and -stop). Provides voltage-frequency pairs for testing or monitoring."
    )

    args = parser.parse_args()

    if args.start_voltage is not None or args.stop_voltage is not None:
        if args.start_voltage is None or args.stop_voltage is None:
            parser.error("Both --start_voltage and --stop_voltage must be provided together")
        if args.voltage is not None:
            parser.error("--voltage cannot be used with --start_voltage and --stop_voltage")
        if args.frequency is not None:
            parser.error("--frequency is not used with --start_voltage and --stop_voltage")
        if args.start_voltage < CONFIG["min_core_voltage"]:
            parser.error(f"Start voltage must be at least {CONFIG['min_core_voltage']} mV")
        if args.stop_voltage < CONFIG["min_core_voltage"]:
            parser.error(f"Stop voltage must be at least {CONFIG['min_core_voltage']} mV")
        if args.start_voltage > args.stop_voltage:
            parser.error("Start voltage must not exceed stop voltage")
        if args.monitor:
            parser.error("--start_voltage and --stop_voltage cannot be used with --monitor")
    else:
        if args.voltage is None:
            parser.error("--voltage is required unless --start_voltage and --stop_voltage are used")
        if args.voltage < CONFIG["min_core_voltage"]:
            parser.error(f"Voltage must be at least {CONFIG['min_core_voltage']} mV")
        if not args.values and args.frequency is None:
            parser.error("--frequency is required in monitor mode or single voltage tests unless --values is provided")
        if args.frequency is not None and args.frequency < CONFIG["min_frequency"]:
            parser.error(f"Frequency must be at least {CONFIG['min_frequency']} MHz")

    if args.range < 0:
        parser.error("Range must be non-negative")
    if args.step <= 0:
        parser.error("Step must be positive")
    if args.reboot is not None and args.reboot <= 0:
        parser.error("Reboot threshold must be positive")
    if args.values and not args.monitor and (args.start_voltage is None and args.stop_voltage is None):
        parser.error("The --values option is only valid in monitor mode (-m) or with --start and --stop")
    if args.values:
        read_values_csv(args.values)

    return (
        args.voltage,
        args.start_voltage,
        args.stop_voltage,
        args.frequency,
        validate_ip(args.ip_address),
        args.range,
        args.step,
        args.reboot,
        args.monitor,
        args.values
    )

def fetch_system_info(run_min_values, run_max_values, run_sum_values, run_count_values, hashrate_readings):
    try:
        response = requests.get(f"{bitaxe_ip}/api/system/info", timeout=10)
        response.raise_for_status()
        data = response.json()
        system_info["frequency"] = data.get("frequency", 550)
        system_info["power"] = data.get("power", 0)
        system_info["voltage"] = data.get("voltage", 0)
        system_info["current"] = data.get("current", 0)
        system_info["temp"] = data.get("temp", 0)
        system_info["vrTemp"] = data.get("vrTemp", 0)
        system_info["hashRate"] = data.get("hashRate", 0)
        system_info["coreVoltage"] = data.get("coreVoltage", 1250)
        system_info["coreVoltageActual"] = data.get("coreVoltageActual", 1250)
        system_info["jth"] = system_info["power"] / (system_info["hashRate"] / 1000) if system_info["hashRate"] > 0 else 0
        
        for key in system_info:
            run_min_values[key] = min(run_min_values[key], system_info[key])
            run_max_values[key] = max(run_max_values[key], system_info[key])
            global_min_values[key] = min(global_min_values[key], system_info[key])
            global_max_values[key] = max(global_max_values[key], system_info[key])
            run_sum_values[key] += system_info[key]
            run_count_values[key] += 1
        
        hashrate_readings.append(system_info["hashRate"])
        
        return True
    except requests.RequestException as e:
        print(RED + f"Error fetching system info: {e}" + RESET)
        return False

def set_system_settings(frequency, core_voltage):
    frequency = max(CONFIG["min_frequency"], frequency)
    core_voltage = max(CONFIG["min_core_voltage"], core_voltage)
    try:
        payload = {"frequency": frequency, "coreVoltage": core_voltage}
        print(GREEN + f"Sending PATCH request to {bitaxe_ip}/api/system with payload: {payload}" + RESET)
        response = requests.patch(f"{bitaxe_ip}/api/system", json=payload, timeout=10)
        response.raise_for_status()
        print(GREEN + f"Set frequency to {frequency} MHz, core voltage to {core_voltage} mV" + RESET)
        
        time.sleep(5)
        try:
            response = requests.get(f"{bitaxe_ip}/api/system/info", timeout=10)
            response.raise_for_status()
            data = response.json()
            actual_freq = data.get("frequency", 0)
            actual_volt = data.get("coreVoltage", 0)
            print(GREEN + f"Verified settings: Actual frequency {actual_freq} MHz, actual core voltage {actual_volt} mV" + RESET)
            if abs(actual_freq - frequency) > 1 or abs(actual_volt - core_voltage) > 1:
                print(RED + f"Error: Settings did not apply correctly. Requested: {frequency} MHz, {core_voltage} mV; "
                            f"Actual: {actual_freq} MHz, {actual_volt} mV" + RESET)
                return False
        except requests.RequestException as e:
            print(RED + f"Could not verify settings: {e}" + RESET)
            return False
        
        return True
    except requests.RequestException as e:
        print(RED + f"Error setting system settings (PATCH /api/system): {e}" + RESET)
        return False

def reboot_bitaxe():
    try:
        response = requests.post(f"{bitaxe_ip}/api/system/restart", timeout=10)
        response.raise_for_status()
        print(GREEN + "Bitaxe rebooted successfully." + RESET)
        return True
    except requests.RequestException as e:
        print(RED + f"Error rebooting Bitaxe: {e}" + RESET)
        return False

def log_data(frequency, core_voltage, run_number, note="", min_values=None, max_values=None, sum_values=None, count_values=None):
    global readings_filename, summaries_filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if not min_values and not max_values:
        try:
            with open(readings_filename, "a") as f:
                if os.path.getsize(readings_filename) == 0:
                    f.write("Timestamp,Hashrate(GH/s),Frequency(MHz),Temp(°C),VRTemp(°C),CoreVoltage(mV),CoreVoltageActual(mV),"
                            "Power(W),Current(mA),Voltage(mV),J/TH,Note\n")
                f.write(f"{timestamp},{system_info['hashRate']:.2f},{system_info['frequency']},"
                        f"{system_info['temp']:.2f},{system_info['vrTemp']:.2f},{system_info['coreVoltage']},"
                        f"{system_info['coreVoltageActual']},{system_info['power']:.2f},{system_info['current']:.2f},"
                        f"{system_info['voltage']:.2f},{system_info['jth']:.2f},{note}\n")
            return readings_filename
        except IOError as e:
            print(RED + f"Error logging readings data: {e}" + RESET)
            return readings_filename
    
    try:
        with open(summaries_filename, "a") as f:
            avg_hashrate = sum_values["hashRate"] / count_values["hashRate"] if count_values["hashRate"] > 0 else 0
            f.write(f"\nRun {run_number} Summary: Frequency {frequency} MHz, Voltage {core_voltage} mV, Avg Hashrate {avg_hashrate:.2f} GH/s\n")
            f.write("Metric,Min,Max,Avg\n")
            for key in min_values:
                avg = sum_values[key] / count_values[key] if count_values[key] > 0 else 0
                unit = ' MHz' if key == 'frequency' else ' W' if key == 'power' else '°C' if key in ['temp', 'vrTemp'] else ' GH/s' if key == 'hashRate' else ' J/TH' if key == 'jth' else ' mV' if 'Voltage' in key else ' mA'
                f.write(f"{key},{min_values[key]:.2f}{unit},{max_values[key]:.2f}{unit},{avg:.2f}{unit}\n")
            f.write("\n")
        return summaries_filename
    except IOError as e:
        print(RED + f"Error logging summaries data: {e}" + RESET)
        return summaries_filename

def log_values_found(voltage, frequency, hashrate, min_freq_tested, max_freq_tested, avg_jth):
    global values_found_filename
    try:
        with open(values_found_filename, "a") as f:
            if os.path.getsize(values_found_filename) == 0:
                f.write("Voltage(mV),Frequency(MHz),Hashrate(GH/s),MinFreqTested(MHz),MaxFreqTested(MHz),AvgJTH(J/TH)\n")
            f.write(f"{voltage},{frequency},{hashrate:.2f},{min_freq_tested},{max_freq_tested},{avg_jth:.2f}\n")
        print(GREEN + f"Logged best hashrate for {voltage} mV: {frequency} MHz, {hashrate:.2f} GH/s, "
                      f"MinFreq {min_freq_tested} MHz, MaxFreq {max_freq_tested} MHz, AvgJTH {avg_jth:.2f} J/TH to {values_found_filename}" + RESET)
    except IOError as e:
        print(RED + f"Error logging to values-found file: {e}" + RESET)

def display_status(
    reading_count, total_readings, run_number, total_tests, start_time,
    monitor_mode=False, min_values=None, max_values=None, sum_values=None, count_values=None,
    start_voltage=None, stop_voltage=None, freq_range=None, freq_step=None, core_voltage=None,
    current_voltage_index=None, total_voltages=None
):
    temp_color = RED if system_info["temp"] >= CONFIG["max_temp_critical"] else ORANGE if system_info["temp"] >= CONFIG["max_temp_warning"] else GREEN
    vrtemp_color = RED if system_info["vrTemp"] >= CONFIG["max_vrtemp_critical"] else ORANGE if system_info["vrTemp"] >= CONFIG["max_vrtemp_warning"] else GREEN
    power_color = RED if system_info["power"] >= CONFIG["max_power_critical"] else ORANGE if system_info["power"] >= CONFIG["max_power_warning"] else GREEN
    
    if monitor_mode:
        print(f"{GREEN}Status [{datetime.now().strftime('%H:%M:%S')}] Monitor Mode ({reading_count}/∞){RESET}")
    else:
        elapsed_time = time.time() - start_time
        test_time_remaining = CONFIG["run_duration"] - elapsed_time
        test_hours = int(test_time_remaining // 3600)
        test_minutes = int((test_time_remaining % 3600) // 60)
        if test_time_remaining < 0:
            test_time_remaining = 0
            test_hours = 0
            test_minutes = 0

        remaining_frequencies = total_tests - run_number + 1
        voltage_time_remaining = remaining_frequencies * CONFIG["run_duration"]
        voltage_hours = int(voltage_time_remaining // 3600)
        voltage_minutes = int((voltage_time_remaining % 3600) // 60)

        total_time_required = 0
        if start_voltage is not None and stop_voltage is not None:
            num_voltages = stop_voltage - start_voltage + 1
            expected_freq = calculate_bm1370_frequency(core_voltage) if core_voltage is not None else 400
            num_frequencies = ((expected_freq + freq_range) - (expected_freq - freq_range)) // freq_step + 1
            total_tests_all = num_voltages * num_frequencies
            total_time_required = total_tests_all * CONFIG["run_duration"]
        else:
            total_time_required = total_tests * CONFIG["run_duration"]
        total_hours = int(total_time_required // 3600)
        total_minutes = int((total_time_required % 3600) // 60)

        all_tests_time_remaining = 0
        if start_voltage is not None and stop_voltage is not None:
            remaining_voltages = total_voltages - current_voltage_index
            all_tests_time_remaining = (remaining_voltages * num_frequencies * CONFIG["run_duration"]) + \
                                       (remaining_frequencies - 1) * CONFIG["run_duration"] + test_time_remaining
        else:
            all_tests_time_remaining = (remaining_frequencies - 1) * CONFIG["run_duration"] + test_time_remaining
        all_tests_hours = int(all_tests_time_remaining // 3600)
        all_tests_minutes = int((all_tests_time_remaining % 3600) // 60)

        print(f"{GREEN}Status [{datetime.now().strftime('%H:%M:%S')}] Test {run_number}/{total_tests} ({reading_count}/{total_readings}) "
              f"Test Time Remaining: {test_hours}h {test_minutes}m Voltage Time Remaining: {voltage_hours}h {voltage_minutes}m "
              f"Total Time Required: {total_hours}h {total_minutes}m All Tests Time Remaining: {all_tests_hours}h {all_tests_minutes}m{RESET}")
    
    metrics = [
        ("Hashrate", "hashRate", "GH/s", GREEN),
        ("J/TH", "jth", "J/TH", GREEN),
        ("Temp", "temp", "°C", temp_color),
        ("VR Temp", "vrTemp", "°C", vrtemp_color),
        ("Power", "power", "W", power_color)
    ]
    for label, key, unit, color in metrics:
        avg = sum_values[key] / count_values[key] if count_values[key] > 0 else 0
        print(f"{label}: {color}{system_info[key]:.2f}{RESET} {unit} (Min: {min_values[key]:.2f}, Max: {max_values[key]:.2f}, Avg: {avg:.2f})")
    
    print(f"Frequency: {system_info['frequency']} MHz")
    print(f"Core Voltage: {system_info['coreVoltage']} mV")
    print("-" * 40)

def display_summary(csv_files):
    global summaries_filename
    summary_lines = []
    summary_lines.append("=== Global Summary ===")
    summary_lines.append("Min Values:")
    for key, value in global_min_values.items():
        unit = ' MHz' if key == 'frequency' else ' W' if key == 'power' else '°C' if key in ['temp', 'vrTemp'] else ' GH/s' if key == 'hashRate' else ' J/TH' if key == 'jth' else ' mV' if 'Voltage' in key else ' mA'
        summary_lines.append(f"{key.capitalize()}: {value:.2f}{unit}")
    summary_lines.append("\nMax Values:")
    for key, value in global_max_values.items():
        unit = ' MHz' if key == 'frequency' else ' W' if key == 'power' else '°C' if key in ['temp', 'vrTemp'] else ' GH/s' if key == 'hashRate' else ' J/TH' if key == 'jth' else ' mV' if 'Voltage' in key else ' mA'
        summary_lines.append(f"{key.capitalize()}: {value:.2f}{unit}")
    if best_hashrates:
        summary_lines.append("")
        for voltage, (freq, hashrate, _) in sorted(best_hashrates.items()):
            summary_lines.append(f"Best Hashrate for Voltage {voltage} mV: {hashrate:.2f} GH/s at {freq} MHz")

    for line in summary_lines:
        print(GREEN + line + RESET)
    
    try:
        with open(summaries_filename, "a") as f:
            f.write("\n" + "\n".join(summary_lines) + "\n")
    except IOError as e:
        print(RED + f"Error logging global summary to summaries file: {e}" + RESET)
    
    if csv_files:
        print(GREEN + "\nCSV Files:" + RESET)
        print(f"- Readings: {csv_files[0]}")
        if len(csv_files) > 1:
            print(f"- Summaries: {csv_files[1]}")
            if len(csv_files) > 2:
                print(f"- Values Found: {csv_files[2]}")
    else:
        print(ORANGE + "No CSV files generated." + RESET)

def adjust_settings_based_on_values(frequency, core_voltage):
    global value_pairs, last_fallback_time, last_fallback_voltage
    if not value_pairs:
        return frequency, core_voltage

    current_pair = (core_voltage, frequency)
    try:
        current_index = value_pairs.index(current_pair)
    except ValueError:
        current_index = 0
        for i, (volt, _) in enumerate(value_pairs):
            if volt >= core_voltage:
                current_index = max(0, i - 1)
                break
        else:
            current_index = len(value_pairs) - 1

    critical_hit = (
        system_info["temp"] >= CONFIG["max_temp_critical"] or
        system_info["vrTemp"] >= CONFIG["max_vrtemp_critical"] or
        system_info["power"] >= CONFIG["max_power_critical"]
    )

    if critical_hit:
        if current_index > 0:
            new_voltage, new_frequency = value_pairs[current_index - 1]
            reason = ("critical temperature" if system_info["temp"] >= CONFIG["max_temp_critical"] else
                      "critical VR temperature" if system_info["vrTemp"] >= CONFIG["max_vrtemp_critical"] else
                      "critical power")
            print(RED + f"Critical {reason} (Temp: {system_info['temp']:.2f}°C, VR Temp: {system_info['vrTemp']:.2f}°C, "
                        f"Power: {system_info['power']:.2f} W). Dropping to {new_frequency} MHz, {new_voltage} mV." + RESET)
            last_fallback_time = time.time()
            last_fallback_voltage = core_voltage
            return new_frequency, new_voltage
        else:
            print(RED + "Critical condition hit but already at lowest settings." + RESET)
            return frequency, core_voltage

    safe_margin = (
        system_info["temp"] <= CONFIG["max_temp_critical"] - CONFIG["critical_advance_margin"] and
        system_info["vrTemp"] <= CONFIG["max_vrtemp_critical"] - CONFIG["critical_advance_margin"] and
        system_info["power"] <= CONFIG["max_power_critical"] - CONFIG["critical_advance_margin"]
    )

    can_advance = True
    if last_fallback_time is not None and last_fallback_voltage is not None:
        elapsed_time = time.time() - last_fallback_time
        if elapsed_time < CONFIG["advance_delay"]:
            next_voltage = value_pairs[current_index + 1][0] if current_index < len(value_pairs) - 1 else core_voltage
            if next_voltage >= last_fallback_voltage:
                can_advance = False
                print(ORANGE + f"Advance delayed: {int((CONFIG['advance_delay'] - elapsed_time) / 60)} minutes remaining "
                              f"before advancing to {next_voltage} mV or higher." + RESET)

    if safe_margin and can_advance and current_index < len(value_pairs) - 1:
        new_voltage, new_frequency = value_pairs[current_index + 1]
        print(GREEN + f"All metrics safe (Temp: {system_info['temp']:.2f}°C, VR Temp: {system_info['vrTemp']:.2f}°C, "
                      f"Power: {system_info['power']:.2f} W). Increasing to {new_frequency} MHz, {new_voltage} mV." + RESET)
        return new_frequency, new_voltage
    return frequency, core_voltage

def run_test(
    frequency, core_voltage, run_number, reboot_threshold, total_tests,
    monitor_mode=False, values_file=None, start_voltage=None, stop_voltage=None,
    freq_range=None, freq_step=None, voltage_index=None, total_voltages=None
):
    global best_hashrate, best_frequency, best_voltage, critical_temp_reached, best_hashrates
    if not set_system_settings(frequency, core_voltage):
        print(RED + f"Skipping run {run_number} at {frequency} MHz, {core_voltage} mV" + RESET)
        return None

    print(GREEN + f"Run {run_number}: {frequency} MHz, {core_voltage} mV {'indefinitely' if monitor_mode else f'for {CONFIG['run_duration']}s'}" + RESET)
    start_time = time.time()
    last_log_time = start_time
    reading_count = 0
    total_readings = float('inf') if monitor_mode else int(CONFIG["run_duration"] / CONFIG["status_interval"])
    run_min_values = {key: float('inf') for key in system_info}
    run_max_values = {key: float('-inf') for key in system_info}
    run_sum_values = {key: 0.0 for key in system_info}
    run_count_values = {key: 0 for key in system_info}
    hashrate_readings = []
    last_hashrate = None
    identical_hashrate_count = 0
    readings_since_adjustment = 0

    while (monitor_mode or time.time() - start_time < CONFIG["run_duration"]) and not is_interrupted:
        if not fetch_system_info(run_min_values, run_max_values, run_sum_values, run_count_values, hashrate_readings):
            print(ORANGE + "Retrying in 10s..." + RESET)
            identical_hashrate_count = 0
            time.sleep(10)
            continue

        reading_count += 1

        if reboot_threshold is not None:
            current_hashrate = system_info["hashRate"]
            if last_hashrate is not None and abs(current_hashrate - last_hashrate) < 0.01:
                identical_hashrate_count += 1
                if identical_hashrate_count >= reboot_threshold:
                    print(ORANGE + f"Detected {identical_hashrate_count} identical hashrate readings ({current_hashrate:.2f} GH/s). Rebooting Bitaxe..." + RESET)
                    log_data(frequency, core_voltage, run_number, note=f"Rebooted due to {identical_hashrate_count} identical hashrate readings")
                    if reboot_bitaxe():
                        time.sleep(30)
                        identical_hashrate_count = 0
                        last_hashrate = None
                    else:
                        print(RED + "Reboot failed. Continuing run..." + RESET)
            else:
                identical_hashrate_count = 1
                last_hashrate = current_hashrate

        settings_changed = False
        if monitor_mode and values_file and readings_since_adjustment >= CONFIG["readings_to_advance"]:
            new_frequency, new_core_voltage = adjust_settings_based_on_values(frequency, core_voltage)
            if new_frequency != frequency or new_core_voltage != core_voltage:
                if set_system_settings(new_frequency, new_core_voltage):
                    frequency, core_voltage = new_frequency, new_core_voltage
                    settings_changed = True
                    readings_since_adjustment = 0
                    identical_hashrate_count = 0
                    note = f"Adjusted to {frequency} MHz, {core_voltage} mV"
                    log_data(frequency, core_voltage, run_number, note=note)
                else:
                    print(RED + f"Failed to adjust settings to {new_frequency} MHz, {new_core_voltage} mV. Continuing with current settings." + RESET)
        elif not values_file or not monitor_mode:
            if (system_info["temp"] >= CONFIG["max_temp_critical"] or 
                system_info["vrTemp"] >= CONFIG["max_vrtemp_critical"] or
                system_info["power"] >= CONFIG["max_power_critical"]):
                critical_temp_reached = True
                new_frequency = max(CONFIG["min_frequency"], frequency - 10)
                new_core_voltage = max(CONFIG["min_core_voltage"], core_voltage - 10)
                reason = ("critical temperature" if system_info["temp"] >= CONFIG["max_temp_critical"] else
                          "critical VR temperature" if system_info["vrTemp"] >= CONFIG["max_vrtemp_critical"] else
                          "critical power")
                print(RED + f"Critical {reason} (Temp: {system_info['temp']:.2f}°C, VR Temp: {system_info['vrTemp']:.2f}°C, Power: {system_info['power']:.2f} W). "
                            f"Reducing to {new_frequency} MHz, {new_core_voltage} mV and stopping test." + RESET)
                set_system_settings(new_frequency, new_core_voltage)
                csv_filename = log_data(frequency, core_voltage, run_number,
                                       f"Reduced and stopped due to {reason}")
                if not monitor_mode:
                    if run_count_values["hashRate"] > 0:
                        avg_hashrate = run_sum_values["hashRate"] / run_count_values["hashRate"]
                        avg_jth = run_sum_values["jth"] / run_count_values["jth"] if run_count_values["jth"] > 0 else 0
                        if avg_hashrate > best_hashrate:
                            best_hashrate = avg_hashrate
                            best_frequency = frequency
                            best_voltage = core_voltage
                        if core_voltage not in best_hashrates or avg_hashrate > best_hashrates[core_voltage][1]:
                            best_hashrates[core_voltage] = (frequency, avg_hashrate, avg_jth)
                    csv_filename = log_data(frequency, core_voltage, run_number,
                                           min_values=run_min_values, max_values=run_max_values,
                                           sum_values=run_sum_values, count_values=run_count_values)
                return csv_filename

        readings_since_adjustment += 1

        if time.time() - last_log_time >= CONFIG["log_interval"]:
            csv_filename = log_data(frequency, core_voltage, run_number)
            last_log_time = time.time()

        if not settings_changed:
            display_status(
                reading_count, total_readings, run_number, total_tests, start_time,
                monitor_mode=monitor_mode, min_values=run_min_values, max_values=run_max_values,
                sum_values=run_sum_values, count_values=run_count_values,
                start_voltage=start_voltage, stop_voltage=stop_voltage,
                freq_range=freq_range, freq_step=freq_step, core_voltage=core_voltage,
                current_voltage_index=voltage_index, total_voltages=total_voltages
            )

        time.sleep(CONFIG["status_interval"])

    if not monitor_mode and run_count_values["hashRate"] > 0:
        avg_hashrate = run_sum_values["hashRate"] / run_count_values["hashRate"]
        avg_jth = run_sum_values["jth"] / run_count_values["jth"] if run_count_values["jth"] > 0 else 0
        if avg_hashrate > best_hashrate:
            best_hashrate = avg_hashrate
            best_frequency = frequency
            best_voltage = core_voltage
        if core_voltage not in best_hashrates or avg_hashrate > best_hashrates[core_voltage][1]:
            best_hashrates[core_voltage] = (frequency, avg_hashrate, avg_jth)
        csv_filename = log_data(frequency, core_voltage, run_number,
                               min_values=run_min_values, max_values=run_max_values,
                               sum_values=run_sum_values, count_values=run_count_values)
        return csv_filename
    return readings_filename

def main():
    global initial_frequency, initial_core_voltage, bitaxe_ip, best_frequency, best_voltage, critical_temp_reached
    global readings_filename, summaries_filename, values_found_filename, best_hashrates
    (
        voltage,
        start_voltage,
        stop_voltage,
        frequency,
        bitaxe_ip,
        freq_range,
        freq_step,
        reboot_threshold,
        monitor_mode,
        values_file
    ) = parse_arguments()

    initial_core_voltage = voltage
    if values_file and monitor_mode:
        closest_pair = min(value_pairs, key=lambda x: abs(x[0] - voltage)) if value_pairs else (voltage, 400)
        initial_core_voltage = closest_pair[0]
        initial_frequency = closest_pair[1]
    else:
        initial_frequency = frequency if frequency is not None else calculate_bm1370_frequency(start_voltage) if start_voltage is not None else 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if start_voltage is not None and stop_voltage is not None:
        readings_filename = f"bitaxe_readings_volt_start_{start_voltage}_stop_{stop_voltage}_{timestamp}.csv"
        summaries_filename = f"bitaxe_summaries_volt_start_{start_voltage}_stop_{stop_voltage}_{timestamp}.csv"
        values_found_filename = f"values-found_volt_start_{start_voltage}_stop_{stop_voltage}_{timestamp}.csv"
    else:
        readings_filename = f"bitaxe_readings_volt_{initial_core_voltage}_freq_{initial_frequency}_{timestamp}.csv"
        summaries_filename = f"bitaxe_summaries_volt_{initial_core_voltage}_freq_{initial_frequency}_{timestamp}.csv"

    if monitor_mode:
        freq_range = 0
        freq_step = 1
        total_tests = 1
    else:
        if start_voltage is not None and stop_voltage is not None:
            total_tests = 1
        else:
            total_tests = ((initial_frequency + freq_range) - (initial_frequency - freq_range)) // freq_step + 1

    print(GREEN + f"Initial settings: IP: {bitaxe_ip}" + RESET)
    csv_files = [readings_filename]
    if not monitor_mode:
        csv_files.append(summaries_filename)
        if start_voltage is not None and stop_voltage is not None:
            csv_files.append(values_found_filename)
            print(GREEN + f"Testing voltages from {start_voltage} mV to {stop_voltage} mV, sweeping frequency for each voltage" + RESET)
        else:
            print(GREEN + f"Testing from {initial_frequency - freq_range} MHz to {initial_frequency + freq_range} MHz with step {freq_step} MHz at {voltage} mV" + RESET)
    else:
        print(GREEN + f"Monitoring at {initial_frequency} MHz, {initial_core_voltage} mV indefinitely" + RESET)
        if values_file:
            print(GREEN + f"Using values from {values_file} for dynamic adjustments" + RESET)

    if monitor_mode:
        csv_file = run_test(
            initial_frequency, initial_core_voltage, 1, reboot_threshold, total_tests,
            monitor_mode=True, values_file=values_file
        )
        if csv_file and csv_file not in csv_files:
            csv_files.append(csv_file)
    elif start_voltage is not None and stop_voltage is not None:
        total_voltages = stop_voltage - start_voltage + 1
        for voltage_index, volt in enumerate(range(start_voltage, stop_voltage + 1), 1):
            center_freq = get_frequency_for_voltage(volt, values_file)
            print(GREEN + f"Testing voltage {volt} mV with center frequency {center_freq} MHz ± {freq_range} MHz" + RESET)
            freq_tests = ((center_freq + freq_range) - (center_freq - freq_range)) // freq_step + 1
            min_freq_tested = center_freq - freq_range
            max_freq_tested = center_freq + freq_range
            run_number = 1
            for freq in range(min_freq_tested, max_freq_tested + 1, freq_step):
                start_time = time.time()
                csv_file = run_test(
                    freq, volt, run_number, reboot_threshold, freq_tests,
                    start_voltage=start_voltage, stop_voltage=stop_voltage,
                    freq_range=freq_range, freq_step=freq_step,
                    voltage_index=voltage_index, total_voltages=total_voltages
                )
                if csv_file and csv_file not in csv_files:
                    csv_files.append(csv_file)
                run_number += 1
                if is_interrupted or critical_temp_reached:
                    break
            if is_interrupted or critical_temp_reached:
                break
            if volt in best_hashrates:
                best_freq, best_hash, avg_jth = best_hashrates[volt]
                log_values_found(volt, best_freq, best_hash, min_freq_tested, max_freq_tested, avg_jth)
            critical_temp_reached = False
        if best_hashrate > 0 and best_frequency is not None and best_voltage is not None:
            print(GREEN + f"Setting system to best hashrate settings: {best_frequency} MHz, {best_voltage} mV" + RESET)
            if not set_system_settings(best_frequency, best_voltage):
                print(RED + f"Failed to set best hashrate settings. Reverting to initial settings." + RESET)
                set_system_settings(initial_frequency, initial_core_voltage)
        else:
            print(ORANGE + "No valid runs completed. Reverting to initial settings." + RESET)
            set_system_settings(initial_frequency, initial_core_voltage)
    else:
        run_number = 1
        start_time = time.time()
        for freq in range(initial_frequency - freq_range, initial_frequency + freq_range + 1, freq_step):
            csv_file = run_test(
                freq, voltage, run_number, reboot_threshold, total_tests,
                freq_range=freq_range, freq_step=freq_step
            )
            if csv_file and csv_file not in csv_files:
                csv_files.append(csv_file)
            run_number += 1
            if is_interrupted or critical_temp_reached:
                break

    if not monitor_mode:
        display_summary(csv_files)
    else:
        print(GREEN + "\nMonitor mode terminated. CSV File:" + RESET)
        print(f"- Readings: {csv_files[0]}")

if __name__ == "__main__":
    main()