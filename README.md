# WARNING: This code overclocks your BitAxe and could damage it. I take no responsibility for damage to your BitAxe. Use at your own risk!!!

My bitaxe has upgraded thermal paste, a low-profile pro heatsink, 2 Noctua NF-A6x25 fanes, a 100W Mean Well power supply, and an additional fan blowing on it. Be careful with the settings inside the code and the values.csv file to ensure they meet your requirements.

# Bitaxe Frequency Sweeper and Status Logger

The **Bitaxe Status Logger** is a Python script for monitoring and optimizing the performance of a Bitaxe Bitcoin mining device. It tracks key metrics such as hashrate, temperature, voltage regulator temperature, power consumption, and Joules per Terahash (J/TH), logging them to CSV files for analysis. The script supports both testing across a frequency range and continuous monitoring with dynamic adjustments based on a provided list of known good voltage/frequency pairs.

The idea is that you already know from other tuning scripts and efforts approximately how hard you can drive your BitAxe in terms of Voltage without going over the Power, Temperature, or Voltage Regulator Temperatures. I have Kryonaut thermal paste, a low-profile pro heat sink with a 60mmx25mm Noctua fan on the front and back. I know my voltage limit is 1307mV. This code helps find the optimal frequency for the set voltage.

Use the bm1370_voltage_calculator.py to get some estimates on frequency, voltage, and expected hash rates. Then use bitaxe_status_logger.py to test various frequencies around that voltage to find the maximum hashrate.

```
Frequency: 650 MHz, Voltage: 1135.9 mV, Estimated Hashrate: 1397.5 GH/s
Frequency: 670 MHz, Voltage: 1144.9 mV, Estimated Hashrate: 1440.5 GH/s
Frequency: 690 MHz, Voltage: 1153.9 mV, Estimated Hashrate: 1483.5 GH/s
Frequency: 710 MHz, Voltage: 1162.9 mV, Estimated Hashrate: 1526.5 GH/s
Frequency: 730 MHz, Voltage: 1171.9 mV, Estimated Hashrate: 1569.5 GH/s
Frequency: 750 MHz, Voltage: 1180.9 mV, Estimated Hashrate: 1612.5 GH/s
Frequency: 770 MHz, Voltage: 1189.9 mV, Estimated Hashrate: 1655.5 GH/s
Frequency: 790 MHz, Voltage: 1198.9 mV, Estimated Hashrate: 1698.5 GH/s
Frequency: 810 MHz, Voltage: 1208.0 mV, Estimated Hashrate: 1741.5 GH/s
Frequency: 830 MHz, Voltage: 1217.0 mV, Estimated Hashrate: 1784.5 GH/s
Frequency: 850 MHz, Voltage: 1226.0 mV, Estimated Hashrate: 1827.5 GH/s
Frequency: 870 MHz, Voltage: 1235.0 mV, Estimated Hashrate: 1870.5 GH/s
Frequency: 890 MHz, Voltage: 1244.0 mV, Estimated Hashrate: 1913.5 GH/s
Frequency: 910 MHz, Voltage: 1253.0 mV, Estimated Hashrate: 1956.5 GH/s
Frequency: 930 MHz, Voltage: 1262.0 mV, Estimated Hashrate: 1999.5 GH/s
Frequency: 950 MHz, Voltage: 1271.0 mV, Estimated Hashrate: 2042.5 GH/s
Frequency: 970 MHz, Voltage: 1280.1 mV, Estimated Hashrate: 2085.5 GH/s
Frequency: 990 MHz, Voltage: 1289.1 mV, Estimated Hashrate: 2128.5 GH/s
Frequency: 1010 MHz, Voltage: 1298.1 mV, Estimated Hashrate: 2171.5 GH/s
Frequency: 1030 MHz, Voltage: 1307.1 mV, Estimated Hashrate: 2214.5 GH/s
Frequency: 1050 MHz, Voltage: 1316.1 mV, Estimated Hashrate: 2257.5 GH/s
Frequency: 1070 MHz, Voltage: 1325.1 mV, Estimated Hashrate: 2300.5 GH/s
```

#Examples

```
>python bitaxe_status_logger.py -f 650 -v 1135 -range 5 -step 1 -ip [your bitaxe ip] -reboot 5
```
This will test the frequencies from 645 to 655 in increments of 1, run for 10 minutes each, find the maximum hashrate, set the bitaxe at the end. All while logging and displaying updates. If any temp, vr temp, or power exceed critical thresholds it will fall back. If the bitaxe hangs and produces 5 same hashrate readings, it will reboot the bitaxe.

Then, once you have a list of optimal frequencies and voltages, you place them in a CSV (values.csv) and run your system. The code will keep climbing as high as possible without going over the critical temp, vr temp, or power settings defined in the CONFIG section of the code.

```
>python bitaxe_status_logger.py -f 1290 -v 992 -m -values values.csv -ip [your bitaxe ip] -reboot 5

values.csv
Voltage,Frequency
1290,992
1299,1015
1300,1018
1301,1019
1302,1019
1303,1023
1304,1025
1305,1023
1306,1027
1310,1033
1311,1035
1313,1037
1314,1037
1315,1043
1316,1045
1320,1055
1325,1065
```

This will sequentially keep increasing through the given values until we are 'critical_advance_margin' (2) away from the critical values for temp, vr temp, and power. This allows us to drive the bitaxe as hard as possible while allowing for ambient air temperature changes throughout the day. If critical values are exceeded, step back down to the next lowest value and do not attempt to advance again for 'advance_delay' (3 hours) to allow the ambient temperature to cool down. 

## Features

- **Real-Time Monitoring**: Fetches and displays system metrics (hashrate, temperature, power, etc.) at regular intervals.
- **Frequency Range Testing**: Tests the Bitaxe across a specified frequency range to find optimal settings for hashrate.
- **Monitor Mode**: Continuously monitors at a fixed frequency or dynamically adjusts settings using a `values.csv` file to maximize throughput while avoiding critical thresholds.
- **Dynamic Adjustments**: In monitor mode with `values.csv`, automatically increases or decreases voltage/frequency to optimize performance, with a configurable delay (`advance_delay`) to prevent rapid reattempts of high settings after a critical condition.
- **Critical Condition Handling**: Reduces settings to safer values when critical temperature, VR temperature, or power thresholds are reached, without rebooting in monitor mode.
- **CSV Logging**: Logs detailed time-series data and run summaries to CSV files for post-analysis.
- **Reboot on Stale Hashrate**: Optionally reboots the Bitaxe if the hashrate remains unchanged for a specified number of readings.
- **Color-Coded Console Output**: Uses ANSI colors to highlight warnings and critical conditions.

## Installation

1. **Prerequisites**:
   - Python 3.6 or higher
   - Required Python packages: `requests`, `argparse`, `csv`
   - A Bitaxe device accessible via its API (HTTP)

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/bitaxe-status-logger.git
   cd bitaxe-status-logger
   ```

3. **Install Dependencies**:
   ```bash
   pip install requests
   ```

4. **Prepare `values.csv` (Optional)**:
   - For monitor mode with dynamic adjustments, create a `values.csv` file with known good voltage and frequency pairs. Example format:
     ```csv
     Voltage,Frequency
     1000,400
     1100,450
     1200,500
     1300,550
     ```
   - Place `values.csv` in the same directory as the script or specify its path using the `--values` flag.

## Usage

Run the script using the command line with required and optional arguments. Below are the main modes of operation:

### Frequency Range Testing
Test the Bitaxe across a range of frequencies to find the best hashrate:
```bash
python bitaxe_status_logger.py -v 1200 -f 500 -ip 192.168.2.205 -range 10 -step 2
```
- `-v 1200`: Core voltage in mV (minimum 1000 mV)
- `-f 500`: Initial frequency in MHz (minimum 400 MHz)
- `-ip 192.168.2.205`: Bitaxe IP address
- `-range 10`: Test ±10 MHz around the initial frequency
- `-step 2`: Increment frequency by 2 MHz per test

### Monitor Mode
Monitor the Bitaxe indefinitely at a fixed frequency:
```bash
python bitaxe_status_logger.py -v 1200 -f 500 -ip 192.168.2.205 -m
```
- `-m`: Enables monitor mode (runs indefinitely at the specified frequency)

### Monitor Mode with Dynamic Adjustments
Monitor and dynamically adjust settings using `values.csv`:
```bash
python bitaxe_status_logger.py -v 1200 -f 500 -ip 192.168.2.205 -m -values values.csv
```
- `-values values.csv`: Path to the CSV file with voltage/frequency pairs
- The script will increase settings when safe (metrics are below critical thresholds by `critical_advance_margin`) and decrease settings if critical thresholds are hit, with a 120-minute delay (`advance_delay`) before reattempting higher settings.

### Optional Reboot on Stale Hashrate
Trigger a reboot if the hashrate remains unchanged for a specified number of readings:
```bash
python bitaxe_status_logger.py -v 1200 -f 500 -ip 192.168.2.205 -m -reboot 5
```
- `-reboot 5`: Reboot after 5 consecutive identical hashrate readings

### Full Command-Line Options
```bash
python bitaxe_status_logger.py -h
```
- `-v, --voltage`: Core voltage in mV (required, minimum 1000)
- `-f, --frequency`: Initial frequency in MHz (required, minimum 400)
- `-ip, --ip_address`: Bitaxe IP address (required, e.g., 192.168.2.205)
- `-range`: Frequency range ±N MHz (default 10, ignored in monitor mode)
- `-step`: Frequency step size in MHz (default 2, ignored in monitor mode)
- `-reboot`: Number of identical hashrate readings to trigger a reboot (optional)
- `-m, --monitor`: Run in monitor mode indefinitely
- `-values`: Path to `values.csv` for dynamic adjustments (monitor mode only)

## Configuration

The script includes a `CONFIG` dictionary with tunable parameters:

- `run_duration`: Duration of each test run in seconds (default: 600, 10 minutes)
- `log_interval`: Time between CSV log entries in seconds (default: 10)
- `status_interval`: Time between status updates in seconds (default: 10)
- `max_temp_warning`: Chip temperature warning threshold in °C (default: 65)
- `max_temp_critical`: Chip temperature critical threshold in °C (default: 67)
- `max_vrtemp_warning`: Voltage regulator temperature warning threshold in °C (default: 80)
- `max_vrtemp_critical`: Voltage regulator temperature critical threshold in °C (default: 90)
- `max_power_warning`: Power warning threshold in watts (default: 38)
- `max_power_critical`: Power critical threshold in watts (default: 44)
- `min_frequency`: Minimum safe frequency in MHz (default: 400)
- `min_core_voltage`: Minimum safe core voltage in mV (default: 1000)
- `critical_advance_margin`: Margin below critical thresholds to advance settings in monitor mode (default: 2)
- `readings_to_advance`: Number of readings to take before allowing another settings adjustment (default: 3)
- `advance_delay`: Delay in seconds before advancing to higher settings after a critical fallback (default: 7200, 120 minutes)

Modify these values in the `CONFIG` dictionary at the top of `bitaxe_status_logger.py` to suit your needs.

## Output

The script generates two CSV files:

1. **Readings File** (`bitaxe_readings_volt_X_freq_Y_TIMESTAMP.csv`):
   - Contains time-series data for each reading.
   - Columns: `Timestamp`, `Hashrate(GH/s)`, `Frequency(MHz)`, `Temp(°C)`, `VRTemp(°C)`, `CoreVoltage(mV)`, `CoreVoltageActual(mV)`, `Power(W)`, `Current(mA)`, `Voltage(mV)`, `J/TH`, `Note`
   - Example:
     ```
     Timestamp,Hashrate(GH/s),Frequency(MHz),Temp(°C),VRTemp(°C),CoreVoltage(mV),CoreVoltageActual(mV),Power(W),Current(mA),Voltage(mV),J/TH,Note
     20250511_120000,500.25,500,60.50,75.20,1200,1198,35.00,2916.67,12000.00,70.00,Adjusted to 500 MHz, 1200 mV
     ```

2. **Summaries File** (`bitaxe_summaries_volt_X_freq_Y_TIMESTAMP.csv`, non-monitor mode only):
   - Contains min, max, and average values for each metric per test run.
   - Format:
     ```
     Run 1 Summary: Frequency 500 MHz, Voltage 1200 mV, Avg Hashrate 500.25 GH/s
     Metric,Min,Max,Avg
     frequency,500.00 MHz,500.00 MHz,500.00 MHz
     power,34.50 W,35.20 W,35.00 W
     ...
     ```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes and commit (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request with a detailed description of your changes.

Please ensure your code follows PEP 8 style guidelines and includes appropriate documentation.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the Bitaxe Bitcoin mining device.
- Inspired by the need for automated performance optimization and monitoring in cryptocurrency mining.

## Inspirational Shoutouts
- Starficient: https://github.com/kha1n3vol3/BitaxePID
- Hurllz: https://github.com/Hurllz/bitaxe-temp-monitor/
- WhiteyCookie: https://github.com/WhiteyCookie/Bitaxe-Hashrate-Benchmark
- mrv777: https://github.com/mrv777/bitaxe-hashrate-benchmark
