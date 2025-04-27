# WARNING: This code overclocks your BitAxe and could damage it. I take no responsibility for damage to your BitAxe. Use at your own risk!!!

# Bitaxe Frequency Sweeper and Status Logger

The `bitaxe_status_logger.py` is a Python script designed to monitor and log the performance of a Bitaxe Bitcoin mining device. It supports two modes: **testing mode**, which tests the device across a range of frequencies to optimize performance, and **monitor-only mode**, which continuously logs metrics at a single frequency. The script collects metrics such as hashrate, power consumption, temperature, and efficiency (J/TH), with features for automated reboots, critical threshold monitoring, and detailed logging for analysis.

The idea is that you already know from other tuning scripts and efforts approximately how hard you can drive your BitAxe in terms of Voltage without going over the Power, Temperature, or Voltage Regulator Temperatures. I have Kryonaut thermal paste, a low-profile pro heat sink with a 60mmx25mm Noctua fan on the front and back. I know my voltage limit is 1307mV. This code helps find the optimal frequency for the set voltage.

Use the bm1370_voltage_hashrate_calculator.py to get some estimates on frequency, voltage, and expected hash rates. Then use bitaxe_status_logger.py to test various frequencies around that voltage to find the maximum hash rate.
```
Frequency (MHz) | Voltage (mV) | Est. Hashrate (GH/s)
------------------------------------------------
            630 | 1135.0       | 1328.4
            635 | 1137.2       | 1338.9
            640 | 1139.4       | 1349.4
            645 | 1141.6       | 1360.0
            650 | 1143.8       | 1370.5
            655 | 1146.0       | 1381.1
            660 | 1148.2       | 1391.6
            665 | 1150.3       | 1402.2
            670 | 1152.5       | 1412.7
            675 | 1154.7       | 1423.2
            680 | 1156.9       | 1433.8
            685 | 1159.1       | 1444.3
            690 | 1161.3       | 1454.9
            695 | 1163.5       | 1465.4
            700 | 1165.7       | 1475.9
            705 | 1167.9       | 1486.5
            710 | 1170.0       | 1497.0
            715 | 1172.2       | 1507.6
            720 | 1174.4       | 1518.1
            725 | 1176.6       | 1528.7
            730 | 1178.8       | 1539.2
            735 | 1181.0       | 1549.7
            740 | 1183.2       | 1560.3
            745 | 1185.4       | 1570.8
            750 | 1187.6       | 1581.4
            755 | 1189.7       | 1591.9
            760 | 1191.9       | 1602.5
            765 | 1194.1       | 1613.0
            770 | 1196.3       | 1623.5
            775 | 1198.5       | 1634.1
            780 | 1200.7       | 1644.6
            785 | 1202.9       | 1655.2
            790 | 1205.1       | 1665.7
            795 | 1207.3       | 1676.3
            800 | 1209.4       | 1686.8
            805 | 1211.6       | 1697.3
            810 | 1213.8       | 1707.9
            815 | 1216.0       | 1718.4
            820 | 1218.2       | 1729.0
            825 | 1220.4       | 1739.5
            830 | 1222.6       | 1750.1
            835 | 1224.8       | 1760.6
            840 | 1227.0       | 1771.1
            845 | 1229.1       | 1781.7
            850 | 1231.3       | 1792.2
            855 | 1233.5       | 1802.8
            860 | 1235.7       | 1813.3
            865 | 1237.9       | 1823.9
            870 | 1240.1       | 1834.4
            875 | 1242.3       | 1844.9
            880 | 1244.5       | 1855.5
            885 | 1246.7       | 1866.0
            890 | 1248.8       | 1876.6
            895 | 1251.0       | 1887.1
            900 | 1253.2       | 1897.6
            905 | 1255.4       | 1908.2
            910 | 1257.6       | 1918.7
            915 | 1259.8       | 1929.3
            920 | 1262.0       | 1939.8
            925 | 1264.2       | 1950.4
            930 | 1266.4       | 1960.9
            935 | 1268.5       | 1971.4
            940 | 1270.7       | 1982.0
            945 | 12.9       | 1992.5
            950 | 1275.1       | 2003.1
            955 | 1277.3       | 2013.6
            960 | 1279.5       | 2024.2
            965 | 1281.7       | 2034.7
            970 | 1283.9       | 2045.2
            975 | 1286.1       | 2055.8
            980 | 1288.2       | 2066.3
            985 | 1290.4       | 2076.9
            990 | 1292.6       | 2087.4
            995 | 1294.8       | 2098.0
           1000 | 1297.0       | 2108.5
           1005 | 1299.0       | 2119.0
           1010 | 1301.0       | 2129.6
           1015 | 1303.0       | 2140.1
           1020 | 1305.0       | 2150.7
           1025 | 1307.0       | 2161.2
           1030 | 1309.0       | 2171.8
           1035 | 1311.0       | 2182.3
           1040 | 1313.0       | 2192.8
           1045 | 1315.0       | 2203.4
           1050 | 1317.0       | 2213.9
           1055 | 1319.0       | 2224.5
           1060 | 1321.0       | 2235.0
           1065 | 1323.0       | 2245.6
           1070 | 1325.0       | 2256.1
           1075 | 1327.0       | 2266.6
           1080 | 1329.0       | 2277.2
           1085 | 1331.0       | 2287.7
```

## Features
- **Testing Mode**:
  - Tests the Bitaxe across a user-defined frequency range (e.g., 490–510 MHz) with configurable steps.
  - Logs min/max/avg metrics per run and a global summary.
- **Monitor-Only Mode** (via `-m` flag):
  - Runs indefinitely at a single frequency, logging metrics continuously.
  - Monitors for reboots without generating summaries.
- **Metric Logging**:
  - Records hashrate, frequency, chip temperature, VR temperature, core voltage, power, current, voltage, and J/TH.
  - Readings log with customizable column order: `Timestamp,Hashrate(GH/s),Frequency(MHz),Temp(°C),VRTemp(°C),CoreVoltage(mV),CoreVoltageActual(mV),Power(W),Current(mA),Voltage(mV),J/TH,Note`.
- **Critical Threshold Monitoring**:
  - Stops testing if power ≥ 27 W, chip temperature ≥ 67°C, or VR temperature ≥ 90°C. (Confirgurable in code)
  - Warns (orange console output) if power ≥ 25 W, chip temperature ≥ 63°C, or VR temperature ≥ 80°C. (Configurable in code)
  - Reduces frequency by 10 MHz and voltage by 10 mV on critical events.
- **Reboot Capability**:
  - Reboots the Bitaxe if a specified number of consecutive identical hashrate readings are detected (`-reboot X`).
- **Dual Log Files (Testing Mode)**:
  - **Readings Log**: Time-series data (`bitaxe_readings_volt_<voltage>_freq_<frequency>_<timestamp>.csv`).
  - **Summaries Log**: Per-run and global summaries (`bitaxe_summaries_volt_<voltage>_freq_<frequency>_<timestamp>.csv`).
- **Console Output**:
  - Real-time status updates with test progress, reading count, and estimated time remaining (hours and minutes) in testing mode.
  - Simplified monitor mode output with reading count.
- **Safety Features**:
  - Ensures minimum frequency (400 MHz) and voltage (1000 mV).
  - Automatic fallback to best or initial settings after tests or critical events.

## Requirements
- Python 3.11 or higher
- `requests` library: Install with `pip install requests`
- A Bitaxe device with API access (e.g., ESP-Miner firmware v2.6.5 or compatible)
- Network access to the Bitaxe's IP address (e.g., `192.168.1.100`)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/andelorean/bitaxe-frequency_sweeper.git
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
python bitaxe_status_logger.py -v VOLTAGE -f FREQUENCY -ip IP_ADDRESS [-range RANGE] [-step STEP] [-reboot REBOOT] [-m]
```

### Command-Line Parameters
| Parameter | Description | Required | Default | Example |
|-----------|-------------|----------|---------|---------|
| `-v`, `--voltage` | Core voltage in mV (minimum 1000 mV) | Yes | N/A | `-v 1295` |
| `-f`, `--frequency` | Initial frequency in MHz (minimum 400 MHz) | Yes | N/A | `-f 500` |
| `-ip`, `--ip_address` | Bitaxe IP address | Yes | N/A | `-ip 192.168.1.100` |
| `-range` | Frequency range in MHz to test above and below the initial frequency (ignored in monitor mode) | No | 10 | `-range 10` |
| `-step` | Frequency step size in MHz (ignored in monitor mode) | No | 2 | `-step 2` |
| `-reboot` | Number of consecutive identical hashrate readings to trigger a reboot | No | None | `-reboot 5` |
| `-m`, `--monitor` | Run in monitor-only mode at the specified frequency indefinitely (sets range=0, step=0) | No | False | `-m` |

### Example Commands
**Testing Mode**:
Test from 490 MHz to 510 MHz (500 ± 10 MHz) with 2 MHz steps, 1295 mV, and reboot after 5 identical hashrate readings:
```bash
python bitaxe_status_logger.py -v 1295 -f 500 -ip 192.168.1.100 -range 10 -step 2 -reboot 5
```

**Monitor-Only Mode**:
Monitor at 500 MHz indefinitely with reboots after 5 identical hashrate readings:
```bash
python bitaxe_status_logger.py -v 1295 -f 500 -ip 192.168.1.100 -m -reboot 5
```

## How It Works
### Testing Mode
1. **Initialization**:
   - Parses command-line arguments and validates inputs.
   - Sets the initial frequency to `frequency - range` (e.g., 500 - 10 = 490 MHz) and voltage.
   - Initializes two log files: `bitaxe_readings_volt_<voltage>_freq_<frequency>_<timestamp>.csv` and `bitaxe_summaries_volt_<voltage>_freq_<frequency>_<timestamp>.csv`.

2. **Testing Loop**:
   - Iterates through frequencies from `frequency - range` to `frequency + range` in `step` increments (e.g., 490, 492, ..., 510 MHz).
   - Each test runs for 10 minutes (600 seconds), collecting metrics every 10 seconds (`status_interval`).
   - Logs time-series data every 60 seconds (`log_interval`) to the readings log.

3. **Critical Threshold Monitoring**:
   - Stops the test if:
     - Power ≥ 27 W
     - Chip temperature ≥ 67°C
     - VR temperature ≥ 90°C
   - Reduces frequency by 10 MHz and voltage by 10 mV, logs the event, sets the best hashrate settings, and exits the test.
   - Displays warnings in orange if power ≥ 24 W, chip temperature ≥ 63°C, or VR temperature ≥ 80°C.

4. **Reboot Logic**:
   - If `-reboot X` is specified, monitors consecutive identical hashrate readings.
   - Triggers a reboot via `POST /api/system/restart` if more than `X` identical readings occur, waits 30 seconds, and resumes the test.
   - Logs reboots in the readings log.

5. **Output**:
   - **Console**: Real-time status updates every 10 seconds, showing test number (e.g., `Test 1/11`), reading progress (e.g., `1/60`), estimated time remaining (e.g., `1h 50m`), hashrate, J/TH, temperatures, power, frequency, and core voltage.
   - **Readings Log**: CSV with timestamped metrics and notes (e.g., reboots, critical stops).
   - **Summaries Log**: CSV with per-run min/max/avg metrics and a global summary.

### Monitor-Only Mode
1. **Initialization**:
   - Sets `range = 0` and `step = 0`, running at the specified frequency (`-f`) indefinitely.
   - Initializes only the readings log: `bitaxe_readings_volt_<voltage>_freq_<frequency>_<timestamp>.csv`.

2. **Monitoring Loop**:
   - Collects metrics every 10 seconds (`status_interval`) and logs every 60 seconds (`log_interval`) to the readings log.
   - Monitors for reboots if `-reboot X` is provided, same as testing mode.
   - Continues until interrupted (Ctrl+C) or a critical threshold is reached.

3. **Critical Threshold Monitoring**:
   - Same as testing mode, but only logs to the readings log and reverts to initial settings on critical events.

4. **Output**:
   - **Console**: Simplified status updates showing `Monitor Mode (X/∞)`, hashrate, J/TH, temperatures, power, frequency, and core voltage.
   - **Readings Log**: Same format as testing mode, with continuous metrics and notes.

## Output Files
- **Readings Log** (`bitaxe_readings_volt_<voltage>_freq_<frequency>_<timestamp>.csv`):
  - Columns: `Timestamp,Hashrate(GH/s),Frequency(MHz),Temp(°C),VRTemp(°C),CoreVoltage(mV),CoreVoltageActual(mV),Power(W),Current(mA),Voltage(mV),J/TH,Note`
  - Example:
    ```
    Timestamp,Hashrate(GH/s),Frequency(MHz),Temp(°C),VRTemp(°C),CoreVoltage(mV),CoreVoltageActual(mV),Power(W),Current(mA),Voltage(mV),J/TH,Note
    2025-04-24_210200,2031.25,500,63.75,83.00,1295,1295,37.32,25000.00,4984.38,18.38,
    2025-04-24_210300,2031.25,500,64.50,83.50,1295,1295,37.40,25010.00,4985.00,18.41,Rebooted due to 6 identical hashrate readings
    ```

- **Summaries Log** (`bitaxe_summaries_volt_<voltage>_freq_<frequency>_<timestamp>.csv`, testing mode only):
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
    curl -X PATCH http://192.168.1.100/api/system -H "Content-Type: application/json" -d '{"frequency": 500, "coreVoltage": 1295}'
    curl -X POST http://192.168.1.100/api/system/restart
    ```
  - Ensure the Bitaxe is running compatible firmware (e.g., ESP-Miner v2.6.5).
- **Temperature Issues**: If tests stop due to high temperatures (≥ 67°C), improve cooling (e.g., add a Noctua 40mm fan or apply Thermal Grizzly Kryonaut).
- **Hashrate Issues**: If identical hashrate readings trigger frequent reboots, adjust `-reboot X` to a higher value or check the Bitaxe's mining pool connection.
- **Monitor Mode**: If monitor mode stops unexpectedly, verify critical thresholds or network connectivity.
- **Log Analysis**: Review the readings log for reboot or critical stop notes, and the summaries log (testing mode) for performance metrics.

## Contributing
Contributions are welcome! Please submit issues or pull requests to the GitHub repository. For major changes, open an issue first to discuss the proposed changes.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments
- Built for the Bitaxe community to optimize Bitcoin mining performance.
- Thanks to the ESP-Miner project for providing the Bitaxe API.

## Inspirational Shoutouts
- Starficient: https://github.com/kha1n3vol3/BitaxePID
- Hurllz: https://github.com/Hurllz/bitaxe-temp-monitor/
- WhiteyCookie: https://github.com/WhiteyCookie/Bitaxe-Hashrate-Benchmark
- mrv777: https://github.com/mrv777/bitaxe-hashrate-benchmark

