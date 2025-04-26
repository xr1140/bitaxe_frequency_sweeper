# Bitaxe Frequency Sweeper and Status Logger

The `bitaxe_status_logger.py` is a Python script designed to monitor and log the performance of a Bitaxe Bitcoin mining device. It tests the device across a range of frequencies, collecting metrics such as hashrate, power consumption, temperature, and efficiency (J/TH). The script supports automated testing, critical threshold monitoring, and rebooting the device if performance stalls. It generates detailed logs for analysis, making it ideal for optimizing Bitaxe performance.

The idea is that you already know from other tuning scripts and efforts approximately how hard you can drive your BitAxe in terms of Voltage without going over the Power, Temperature, or Voltage Regulator Temperatures. I have Kryonaut thermal paste, a low-profile pro heat sink with a 60mm Noctua fan on the front and back. I know my voltage limit is 1295mV. This code helps find the optimal frequency for the set voltage.

Use the bm1370_voltage_calculator.py to get some estimates on frequency, voltage, and expected hash rates. Then use bitaxe_status_logger.py to test various frequencies around that voltage to find the maximum hash rate.
```
Frequency: 400 MHz, Voltage: 0.9000 V, Estimated Hashrate: 816.0 GH/s
Frequency: 550 MHz, Voltage: 1.1000 V, Estimated Hashrate: 1122.0 GH/s
Frequency: 650 MHz, Voltage: 1.1404 V, Estimated Hashrate: 1326.0 GH/s
Frequency: 700 MHz, Voltage: 1.1607 V, Estimated Hashrate: 1428.0 GH/s
Frequency: 750 MHz, Voltage: 1.1809 V, Estimated Hashrate: 1530.0 GH/s
Frequency: 800 MHz, Voltage: 1.2011 V, Estimated Hashrate: 1632.0 GH/s
Frequency: 850 MHz, Voltage: 1.2213 V, Estimated Hashrate: 1734.0 GH/s
Frequency: 900 MHz, Voltage: 1.2416 V, Estimated Hashrate: 1836.0 GH/s
Frequency: 950 MHz, Voltage: 1.2618 V, Estimated Hashrate: 1938.0 GH/s
Frequency: 1000 MHz, Voltage: 1.2820 V, Estimated Hashrate: 2040.0 GH/s
Frequency: 1005 MHz, Voltage: 1.2950 V, Estimated Hashrate: 2050.2 GH/s
Frequency: 1050 MHz, Voltage: 1.4120 V, Estimated Hashrate: 2142.0 GH/s
Frequency: 1075 MHz, Voltage: 1.4770 V, Estimated Hashrate: 2193.0 GH/s
```
## Features
- **Frequency Range Testing**: Tests the Bitaxe across a user-defined frequency range (e.g., 490–510 MHz) with configurable steps.
- **Metric Logging**: Records hashrate, power, voltage, current, chip temperature, VR temperature, J/TH, and core voltage.
- **Critical Threshold Monitoring**:
  - Stops testing if power ≥ 39 W, chip temperature ≥ 67°C, or VR temperature ≥ 90°C.
  - Warns (orange console output) if power ≥ 35 W, chip temperature ≥ 63°C, or VR temperature ≥ 80°C.
- **Reboot Capability**: Reboots the Bitaxe if a specified number of consecutive identical hashrate readings are detected, indicating potential stalls.
- **Dual Log Files**:
  - **Readings Log**: Time-series data with timestamped metrics.
  - **Summaries Log**: Per-run min/max/avg metrics and global summary.
- **Console Output**: Real-time status updates with reading progress (x/y) and color-coded warnings.
- **Safety Features**: Ensures minimum frequency (400 MHz) and voltage (1000 mV), with automatic fallback to best or initial settings.

## Requirements
- Python 3.11 or higher
- `requests` library: Install with `pip install requests`
- A Bitaxe device with API access (e.g., ESP-Miner firmware v2.6.5 or compatible)
- Network access to the Bitaxe's IP address (e.g., `192.168.2.205`)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bitaxe-status-logger.git
   cd bitaxe-status-logger
   ```
2. Install dependencies:
   ```bash
   pip install requests
   ```
3. Ensure your Bitaxe is powered on and accessible via its IP address.

## Usage
Run the script with the required command-line parameters:

```bash
python bitaxe_status_logger.py -v VOLTAGE -f FREQUENCY -ip IP_ADDRESS [-range RANGE] [-step STEP] [-reboot COUNT]
```

### Command-Line Parameters
| Parameter | Description | Required | Default | Example |
|-----------|-------------|----------|---------|---------|
| `-v`, `--voltage` | Core voltage in mV (minimum 1000 mV) | Yes | N/A | `-v 1295` |
| `-f`, `--frequency` | Initial frequency in MHz (minimum 400 MHz) | Yes | N/A | `-f 500` |
| `-ip`, `--ip_address` | Bitaxe IP address | Yes | N/A | `-ip 192.168.2.205` |
| `-range` | Frequency range in MHz to test above and below the initial frequency | No | 10 | `-range 10` |
| `-step` | Frequency step size in MHz | No | 2 | `-step 2` |
| `-reboot` | Number of consecutive identical hashrate readings to trigger a reboot | No | None | `-reboot 5` |

### Example Command
Test the Bitaxe from 490 MHz to 510 MHz (500 ± 10 MHz) with 2 MHz steps, 1295 mV, and reboot after 5 identical hashrate readings:

```bash
python bitaxe_status_logger.py -v 1295 -f 500 -ip 192.168.2.205 -range 10 -step 2 -reboot 5
```

## How It Works
1. **Initialization**:
   - Parses command-line arguments and validates inputs.
   - Sets the initial frequency to `frequency - range` (e.g., 500 - 10 = 490 MHz) and voltage.
   - Initializes two log files: `bitaxe_readings_freq_<frequency>_volt_<voltage>_<timestamp>.csv` and `bitaxe_summaries_freq_<frequency>_volt_<voltage>_<timestamp>.csv`.

2. **Testing Loop**:
   - Iterates through frequencies from `frequency - range` to `frequency + range` in `step` increments (e.g., 490, 492, ..., 510 MHz).
   - Each run lasts 10 minutes (600 seconds), collecting metrics every 10 seconds (`status_interval`).
   - Logs time-series data every 60 seconds (`log_interval`) to the readings log.

3. **Critical Threshold Monitoring**:
   - Stops the test if:
     - Power ≥ 39 W
     - Chip temperature ≥ 67°C
     - VR temperature ≥ 90°C
   - Reduces frequency by 10 MHz and voltage by 10 mV, logs the event, sets the best hashrate settings, and exits.
   - Displays warnings in orange if power ≥ 35 W, chip temperature ≥ 63°C, or VR temperature ≥ 80°C.

4. **Reboot Logic**:
   - If `-reboot X` is specified, monitors consecutive identical hashrate readings.
   - Triggers a reboot via `POST /api/system/restart` if more than `X` identical readings occur, waits 30 seconds, and resumes the run.
   - Logs reboots in the readings log.

5. **Output**:
   - **Console**: Real-time status updates every 10 seconds, showing reading progress (x/60), hashrate, J/TH, temperatures, power, frequency, and core voltage.
   - **Readings Log**: CSV with timestamped metrics and notes (e.g., reboots, critical stops).
   - **Summaries Log**: CSV with per-run min/max/avg metrics, followed by a global summary and best average hashrate.

## Output Files
- **Readings Log** (`bitaxe_readings_freq_<frequency>_volt_<voltage>_<timestamp>.csv`):
  - Columns: `Timestamp`, `Frequency(MHz)`, `Power(W)`, `Voltage(mV)`, `Current(mA)`, `Temp(°C)`, `VRTemp(°C)`, `Hashrate(GH/s)`, `J/TH`, `CoreVoltage(mV)`, `CoreVoltageActual(mV)`, `Note`
  - Example:
    ```
    Timestamp,Frequency(MHz),Power(W),Voltage(mV),Current(mA),Temp(°C),VRTemp(°C),Hashrate(GH/s),J/TH,CoreVoltage(mV),CoreVoltageActual(mV),Note
    2025-04-24_210200,490,37.32,4984.38,25000.00,63.75,83.00,2031.25,18.38,1295,1295,
    2025-04-24_210300,490,37.40,4985.00,25010.00,64.50,83.50,2031.25,18.41,1295,1295,Rebooted due to 6 identical hashrate readings
    ```

- **Summaries Log** (`bitaxe_summaries_freq_<frequency>_volt_<voltage>_<timestamp>.csv`):
  - Per-run summaries with min/max/avg metrics, followed by a global summary.
  - Example:
    ```
    Run 1 Summary: Frequency 490 MHz, Voltage 1295 mV, Avg Hashrate 2032.08 GH/s
    Metric,Min,Max,Avg
    frequency,490.00 MHz,490.00 MHz,490.00 MHz
    power,37.32 W,37.40 W,37.36 W
    ...
    hashRate,2031.25 GH/s,2033.00 GH/s,2032.08 GH/s
    ...

    === Global Summary ===
    Min Values:
    Frequency: 490.00 MHz
    Power: 37.32 W
    ...
    Best Average Hashrate: 2032.08 GH/s at 490 MHz, 1295 mV
    ```

## Troubleshooting
- **API Errors**: If the script fails to set frequency/voltage or reboot, check the Bitaxe's API:
  - Test manually:
    ```bash
    curl -X PATCH http://192.168.2.205/api/system -H "Content-Type: application/json" -d '{"frequency": 500, "coreVoltage": 1295}'
    curl -X POST http://192.168.2.205/api/system/restart
    ```
  - Ensure the Bitaxe is running compatible firmware (e.g., ESP-Miner v2.6.5).
- **Temperature Issues**: If tests stop due to high temperatures (≥ 67°C), improve cooling (e.g., add a Noctua 40mm fan or apply Thermal Grizzly Kryonaut).
- **Hashrate Issues**: If identical hashrate readings trigger frequent reboots, adjust `-reboot X` to a higher value or check the Bitaxe's mining pool connection.
- **Log Analysis**: Review the readings log for reboot or critical stop notes, and the summaries log for performance metrics.

## Contributing
Contributions are welcome! Please submit issues or pull requests to the GitHub repository. For major changes, open an issue first to discuss the proposed changes.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments
- Built for the Bitaxe community to optimize Bitcoin mining performance.
- Thanks to the ESP-Miner project for providing the Bitaxe API.
