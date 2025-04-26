import requests
import time
import signal
import sys
import argparse
import re
from datetime import datetime
import os

# ANSI Color Codes
GREEN = "\033[32m"  # Darker green
ORANGE = "\033[33m"  # Orange
RED = "\033[91m"
RESET = "\033[0m"

# Configuration
CONFIG = {
    "run_duration": 600,  # seconds (10 minutes per run)
    "log_interval": 60,  # seconds (1 minute)
    "status_interval": 10,  # seconds
    "max_temp_warning": 63,  # °C for chip temperature
    "max_temp_critical": 67,  # °C for chip temperature
    "max_vrtemp_warning": 80,  # °C for voltage regulator temperature
    "max_vrtemp_critical": 90,  # °C for voltage regulator temperature
    "max_power_warning": 35,  # W for power
    "max_power_critical": 39,  # W for power
    "min_frequency": 400,  # MHz (safety minimum)
    "min_core_voltage": 1000,  # mV (safety minimum)
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
    "jth": None  # Joules per Terahash (J/TH)
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
best_hashrate = 0.0
best_frequency = None
best_voltage = None

def signal_handler(sig, frame):
    global is_interrupted
    is_interrupted = True
    print(ORANGE + "\nStopping status logger..." + RESET)

signal.signal(signal.SIGINT, signal_handler)

def validate_ip(ip):
    """Basic IP address validation."""
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    if not re.match(pattern, ip):
        raise ValueError("Invalid IP address format. Use format like 192.168.2.205")
    return f"http://{ip}"

def parse_arguments():
    """Parse command-line arguments and print help if required parameters are missing."""
    parser = argparse.ArgumentParser(
        description="Bitaxe status logger for monitoring hashrate, temperature, and power across a frequency range."
    )
    parser.add_argument(
        "-v", "--voltage",
        type=int,
        required=True,
        help="Core voltage in mV (minimum 1000 mV)"
    )
    parser.add_argument(
        "-f", "--frequency",
        type=int,
        required=True,
        help="Initial frequency in MHz (minimum 400 MHz)"
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
        default=10,
        help="Frequency range in MHz to test above and below the initial frequency (default 10 MHz)"
    )
    parser.add_argument(
        "-step",
        type=int,
        default=2,
        help="Frequency step size in MHz (default 2 MHz)"
    )
    parser.add_argument(
        "-reboot",
        type=int,
        default=None,
        help="Number of consecutive identical hashrate readings to trigger a reboot (optional)"
    )

    args = parser.parse_args()

    if args.voltage < CONFIG["min_core_voltage"]:
        parser.error(f"Voltage must be at least {CONFIG['min_core_voltage']} mV")
    if args.frequency < CONFIG["min_frequency"]:
        parser.error(f"Frequency must be at least {CONFIG['min_frequency']} MHz")
    if args.range < 0:
        parser.error("Range must be non-negative")
    if args.step <= 0:
        parser.error("Step must be positive")
    if args.reboot is not None and args.reboot <= 0:
        parser.error("Reboot threshold must be positive")

    return args.voltage, args.frequency, validate_ip(args.ip_address), args.range, args.step, args.reboot

def fetch_system_info(run_min_values, run_max_values, run_sum_values, run_count_values, hashrate_readings):
    """Fetch system settings and update min/max/sum/count and hashrate readings."""
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
        
        # Update run-specific and global min/max, and run-specific sum/count
        for key in system_info:
            run_min_values[key] = min(run_min_values[key], system_info[key])
            run_max_values[key] = max(run_max_values[key], system_info[key])
            global_min_values[key] = min(global_min_values[key], system_info[key])
            global_max_values[key] = max(global_max_values[key], system_info[key])
            run_sum_values[key] += system_info[key]
            run_count_values[key] += 1
        
        # Append hashrate to readings list for reboot tracking
        hashrate_readings.append(system_info["hashRate"])
        
        return True
    except requests.RequestException as e:
        print(RED + f"Error fetching system info: {e}" + RESET)
        return False

def set_system_settings(frequency, core_voltage):
    """Set Bitaxe frequency and core voltage."""
    frequency = max(CONFIG["min_frequency"], frequency)
    core_voltage = max(CONFIG["min_core_voltage"], core_voltage)
    try:
        # Use PATCH to /api/system with correct key "coreVoltage"
        payload = {"frequency": frequency, "coreVoltage": core_voltage}
        print(GREEN + f"Sending PATCH request to {bitaxe_ip}/api/system with payload: {payload}" + RESET)
        response = requests.patch(f"{bitaxe_ip}/api/system", json=payload, timeout=10)
        response.raise_for_status()
        print(GREEN + f"Set frequency to {frequency} MHz, core voltage to {core_voltage} mV" + RESET)
        
        # Verify settings
        time.sleep(5)  # Allow settings to stabilize
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
    """Reboot the Bitaxe using the API."""
    try:
        response = requests.post(f"{bitaxe_ip}/api/system/restart", timeout=10)
        response.raise_for_status()
        print(GREEN + "Bitaxe rebooted successfully." + RESET)
        return True
    except requests.RequestException as e:
        print(RED + f"Error rebooting Bitaxe: {e}" + RESET)
        return False

def log_data(frequency, core_voltage, run_number, note="", min_values=None, max_values=None, sum_values=None, count_values=None):
    """Log system data to readings file or summaries to summaries file."""
    global readings_filename, summaries_filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Log time-series data to readings file
    if not min_values and not max_values:
        try:
            with open(readings_filename, "a") as f:
                if os.path.getsize(readings_filename) == 0:
                    f.write("Timestamp,Frequency(MHz),Power(W),Voltage(mV),Current(mA),"
                            "Temp(°C),VRTemp(°C),Hashrate(GH/s),J/TH,CoreVoltage(mV),CoreVoltageActual(mV),Note\n")
                f.write(f"{timestamp},{system_info['frequency']},"
                        f"{system_info['power']:.2f},{system_info['voltage']:.2f},"
                        f"{system_info['current']:.2f},{system_info['temp']:.2f},"
                        f"{system_info['vrTemp']:.2f},{system_info['hashRate']:.2f},"
                        f"{system_info['jth']:.2f},{system_info['coreVoltage']},"
                        f"{system_info['coreVoltageActual']},{note}\n")
            return readings_filename
        except IOError as e:
            print(RED + f"Error logging readings data: {e}" + RESET)
            return readings_filename
    
    # Log summaries to summaries file
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

def display_status(reading_count, total_readings):
    """Display current system status, including coreVoltage and reading progress (x/y)."""
    temp_color = RED if system_info["temp"] >= CONFIG["max_temp_critical"] else ORANGE if system_info["temp"] >= CONFIG["max_temp_warning"] else GREEN
    vrtemp_color = RED if system_info["vrTemp"] >= CONFIG["max_vrtemp_critical"] else ORANGE if system_info["vrTemp"] >= CONFIG["max_vrtemp_warning"] else GREEN
    power_color = RED if system_info["power"] >= CONFIG["max_power_critical"] else ORANGE if system_info["power"] >= CONFIG["max_power_warning"] else GREEN
    print(f"{GREEN}Status [{datetime.now().strftime('%H:%M:%S')} ({reading_count}/{total_readings})]{RESET}")
    print(f"Hashrate: {system_info['hashRate']:.2f} GH/s")
    print(f"J/TH: {system_info['jth']:.2f} J/TH")
    print(f"Temp: {temp_color}{system_info['temp']:.2f}°C{RESET}")
    print(f"VR Temp: {vrtemp_color}{system_info['vrTemp']:.2f}°C{RESET}")
    print(f"Power: {power_color}{system_info['power']:.2f} W{RESET}")
    print(f"Frequency: {system_info['frequency']} MHz")
    print(f"Core Voltage: {system_info['coreVoltage']} mV")
    print("-" * 40)

def display_summary(csv_files):
    """Display global min/max summary and best hashrate settings, and log to summaries file."""
    global summaries_filename
    
    # Prepare summary text
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
    if best_hashrate > 0:
        summary_lines.append(f"\nBest Average Hashrate: {best_hashrate:.2f} GH/s at {best_frequency} MHz, {best_voltage} mV")
    
    # Print to console
    for line in summary_lines:
        print(GREEN + line + RESET)
    
    # Log to summaries file
    try:
        with open(summaries_filename, "a") as f:
            f.write("\n" + "\n".join(summary_lines) + "\n")
    except IOError as e:
        print(RED + f"Error logging global summary to summaries file: {e}" + RESET)
    
    if csv_files:
        print(GREEN + "\nCSV Files:" + RESET)
        print(f"- Readings: {csv_files[0]}")
        print(f"- Summaries: {csv_files[1]}")
    else:
        print(ORANGE + "No CSV files generated." + RESET)

def run_test(frequency, core_voltage, run_number, reboot_threshold):
    """Run a single test at specified frequency and core voltage."""
    global best_hashrate, best_frequency, best_voltage, critical_temp_reached
    if not set_system_settings(frequency, core_voltage):
        print(RED + f"Skipping run {run_number} at {frequency} MHz, {core_voltage} mV" + RESET)
        return None

    print(GREEN + f"Run {run_number}: {frequency} MHz, {core_voltage} mV for {CONFIG['run_duration']}s" + RESET)
    start_time = time.time()
    last_log_time = start_time
    reading_count = 0
    total_readings = int(CONFIG["run_duration"] / CONFIG["status_interval"])  # e.g., 600 / 10 = 60
    run_min_values = {key: float('inf') for key in system_info}
    run_max_values = {key: float('-inf') for key in system_info}
    run_sum_values = {key: 0.0 for key in system_info}
    run_count_values = {key: 0 for key in system_info}
    hashrate_readings = []  # For reboot tracking only
    last_hashrate = None
    identical_hashrate_count = 0

    while (time.time() - start_time < CONFIG["run_duration"]) and not is_interrupted:
        if not fetch_system_info(run_min_values, run_max_values, run_sum_values, run_count_values, hashrate_readings):
            print(ORANGE + "Retrying in 10s..." + RESET)
            time.sleep(10)
            continue

        # Check for identical hashrate readings if reboot_threshold is set
        if reboot_threshold is not None:
            current_hashrate = system_info["hashRate"]
            if current_hashrate == last_hashrate:
                identical_hashrate_count += 1
                if identical_hashrate_count > reboot_threshold:
                    print(ORANGE + f"Detected {identical_hashrate_count} identical hashrate readings ({current_hashrate:.2f} GH/s). Rebooting Bitaxe..." + RESET)
                    log_data(frequency, core_voltage, run_number, note=f"Rebooted due to {identical_hashrate_count} identical hashrate readings")
                    if reboot_bitaxe():
                        time.sleep(30)  # Wait for stabilization
                        identical_hashrate_count = 0  # Reset counter
                        last_hashrate = None
                    else:
                        print(RED + "Reboot failed. Continuing run..." + RESET)
            else:
                identical_hashrate_count = 1
                last_hashrate = current_hashrate

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
            # Update best hashrate before stopping
            if run_count_values["hashRate"] > 0:
                avg_hashrate = run_sum_values["hashRate"] / run_count_values["hashRate"]
                if avg_hashrate > best_hashrate:
                    best_hashrate = avg_hashrate
                    best_frequency = frequency
                    best_voltage = core_voltage
            csv_filename = log_data(frequency, core_voltage, run_number,
                                   min_values=run_min_values, max_values=run_max_values,
                                   sum_values=run_sum_values, count_values=run_count_values)
            # Set best settings
            if best_frequency is not None and best_voltage is not None:
                print(GREEN + f"Setting system to best hashrate settings: {best_frequency} MHz, {best_voltage} mV" + RESET)
                if not set_system_settings(best_frequency, best_voltage):
                    print(RED + f"Failed to set best hashrate settings. Reverting to initial settings." + RESET)
                    set_system_settings(initial_frequency, initial_core_voltage)
            else:
                print(ORANGE + "No valid runs completed. Setting to initial settings." + RESET)
                set_system_settings(initial_frequency, initial_core_voltage)
            return csv_filename

        reading_count += 1
        display_status(reading_count, total_readings)

        if time.time() - last_log_time >= CONFIG["log_interval"]:
            csv_filename = log_data(frequency, core_voltage, run_number)
            last_log_time = time.time()

        time.sleep(CONFIG["status_interval"])

    # Update best hashrate at run completion
    if run_count_values["hashRate"] > 0:
        avg_hashrate = run_sum_values["hashRate"] / run_count_values["hashRate"]
        if avg_hashrate > best_hashrate:
            best_hashrate = avg_hashrate
            best_frequency = frequency
            best_voltage = core_voltage
    csv_filename = log_data(frequency, core_voltage, run_number,
                           min_values=run_min_values, max_values=run_max_values,
                           sum_values=run_sum_values, count_values=run_count_values)
    return csv_filename

def main():
    """Main loop for frequency tests."""
    global initial_frequency, initial_core_voltage, bitaxe_ip, best_frequency, best_voltage, critical_temp_reached
    global readings_filename, summaries_filename
    initial_core_voltage, initial_frequency, bitaxe_ip, freq_range, freq_step, reboot_threshold = parse_arguments()
    
    # Initialize log filenames with frequency, voltage, and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    readings_filename = f"bitaxe_readings_freq_{initial_frequency}_volt_{initial_core_voltage}_{timestamp}.csv"
    summaries_filename = f"bitaxe_summaries_freq_{initial_frequency}_volt_{initial_core_voltage}_{timestamp}.csv"
    
    # Set initial frequency to initial_frequency - freq_range
    start_frequency = initial_frequency - freq_range
    print(GREEN + f"Requested initial settings: {start_frequency} MHz, {initial_core_voltage} mV" + RESET)
    if not set_system_settings(start_frequency, initial_core_voltage):
        print(RED + "Failed to set initial settings. Exiting." + RESET)
        sys.exit(1)
    
    print(GREEN + f"Initial settings applied: {start_frequency} MHz, {initial_core_voltage} mV, IP: {bitaxe_ip}" + RESET)
    print(GREEN + f"Testing from {start_frequency} MHz to {initial_frequency + freq_range} MHz with step {freq_step} MHz" + RESET)
    csv_files = [readings_filename, summaries_filename]

    for run_number, freq in enumerate(range(start_frequency, initial_frequency + freq_range + 1, freq_step), 1):
        csv_file = run_test(freq, initial_core_voltage, run_number, reboot_threshold)
        if csv_file and csv_file not in csv_files:
            csv_files.append(csv_file)
        if is_interrupted or critical_temp_reached:
            break

    # Set system to best hashrate settings if not already set
    if not critical_temp_reached:
        if best_frequency is not None and best_voltage is not None:
            print(GREEN + f"Setting system to best hashrate settings: {best_frequency} MHz, {best_voltage} mV" + RESET)
            if not set_system_settings(best_frequency, best_voltage):
                print(RED + f"Failed to set best hashrate settings. Reverting to initial settings." + RESET)
                set_system_settings(initial_frequency, initial_core_voltage)
        else:
            print(ORANGE + "No valid runs completed. Reverting to initial settings." + RESET)
            set_system_settings(initial_frequency, initial_core_voltage)

    display_summary(csv_files)

if __name__ == "__main__":
    main()