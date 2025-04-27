
# WARNING: This code overclocks your BitAxe and could damage it. I take no responsibility for damage to your BitAxe. Use at your own risk!!!

# Bitaxe Frequency Sweeper and Status Logger

The `bitaxe_status_logger.py` is a Python script designed to monitor and log the performance of a Bitaxe Bitcoin mining device. It tests the device across a range of frequencies, collecting metrics such as hashrate, power consumption, temperature, and efficiency (J/TH). The script supports automated testing, critical threshold monitoring, and rebooting the device if performance stalls. It generates detailed logs for analysis, making it ideal for optimizing Bitaxe performance.

The idea is that you already know from other tuning scripts and efforts approximately how hard you can drive your BitAxe in terms of Voltage without going over the Power, Temperature, or Voltage Regulator Temperatures. I have Kryonaut thermal paste, a low-profile pro heat sink with a 60mm Noctua fan on the front and back. I know my voltage limit is 1295mV. This code helps find the optimal frequency for the set voltage.

Use the bm1370_voltage_hashrate_calculator.py to get some estimates on frequency, voltage, and expected hash rates. Then use bitaxe_status_logger.py to test various frequencies around that voltage to find the maximum hash rate.
```
Frequency (MHz) | Voltage (mV) | Est. Hashrate (GH/s)
------------------------------------------------
            400 | 900.0       | 843.4
            410 | 913.3       | 864.5
            420 | 926.7       | 885.6
            430 | 940.0       | 906.7
            440 | 953.3       | 927.7
            450 | 966.7       | 948.8
            460 | 980.0       | 969.9
            470 | 993.3       | 991.0
            480 | 1006.7       | 1012.1
            490 | 1020.0       | 1033.2
            500 | 1033.3       | 1054.2
            510 | 1046.7       | 1075.3
            520 | 1060.0       | 1096.4
            530 | 1073.3       | 1117.5
            540 | 1086.7       | 1138.6
            550 | 1100.0       | 1159.7
            560 | 1104.4       | 1180.8
            570 | 1108.8       | 1201.8
            580 | 1113.1       | 1222.9
            590 | 1117.5       | 1244.0
            600 | 1121.9       | 1265.1
            610 | 1126.3       | 1286.2
            620 | 1130.6       | 1307.3
            630 | 1135.0       | 1328.4
            640 | 1139.4       | 1349.4
            650 | 1143.8       | 1370.5
            660 | 1148.2       | 1391.6
            670 | 1152.5       | 1412.7
            680 | 1156.9       | 1433.8
            690 | 1161.3       | 1454.9
            700 | 1165.7       | 1475.9
            710 | 1170.0       | 1497.0
            720 | 1174.4       | 1518.1
            730 | 1178.8       | 1539.2
            740 | 1183.2       | 1560.3
            750 | 1187.6       | 1581.4
            760 | 1191.9       | 1602.5
            770 | 1196.3       | 1623.5
            780 | 1200.7       | 1644.6
            790 | 1205.1       | 1665.7
            800 | 1209.4       | 1686.8
            810 | 1213.8       | 1707.9
            820 | 1218.2       | 1729.0
            830 | 1222.6       | 1750.1
            840 | 1227.0       | 1771.1
            850 | 1231.3       | 1792.2
            860 | 1235.7       | 1813.3
            870 | 1240.1       | 1834.4
            880 | 1244.5       | 1855.5
            890 | 1248.8       | 1876.6
            900 | 1253.2       | 1897.6
            910 | 1257.6       | 1918.7
            920 | 1262.0       | 1939.8
            930 | 1266.4       | 1960.9
            940 | 1270.7       | 1982.0
            950 | 1275.1       | 2003.1
            960 | 1279.5       | 2024.2
            970 | 1283.9       | 2045.2
            980 | 1288.2       | 2066.3
            990 | 1292.6       | 2087.4
           1000 | 1297.0       | 2108.5
           1010 | 1301.0       | 2129.6
           1020 | 1305.0       | 2150.7
           1030 | 1309.0       | 2171.8
           1040 | 1313.0       | 2192.8
           1050 | 1317.0       | 2213.9
           1060 | 1321.0       | 2235.0
           1070 | 1325.0       | 2256.1
           1080 | 1329.0       | 2277.2
           1090 | 1333.0       | 2298.3
           1100 | 1337.0       | 2319.3
           1110 | 1341.0       | 2340.4
           1120 | 1345.0       | 2361.5
           1130 | 1349.0       | 2382.6
           1140 | 1353.0       | 2403.7
           1150 | 1357.0       | 2424.8
           1160 | 1361.0       | 2445.9
           1170 | 1365.0       | 2466.9
           1180 | 1369.0       | 2488.0
           1190 | 1373.0       | 2509.1
           1200 | 1377.0       | 2530.2
           1210 | 1381.0       | 2551.3
           1220 | 1385.0       | 2572.4
           1230 | 1389.0       | 2593.5
           1240 | 1393.0       | 2614.5
           1250 | 1397.0       | 2635.6
           1260 | 1401.0       | 2656.7
           1270 | 1405.0       | 2677.8
           1280 | 1409.0       | 2698.9
           1290 | 1413.0       | 2720.0
           1300 | 1417.0       | 2741.0
```
## Features
- **Frequency Range Testing**: Tests the Bitaxe across a user-defined frequency range (e.g., 490–510 MHz) with configurable steps.
- **Metric Logging**: Records hashrate, power, voltage, current, chip temperature, VR temperature, J/TH, and core voltage.
- **Critical Threshold Monitoring**:
  - Stops testing if power ≥ 27W, chip temperature ≥ 67°C, or VR temperature ≥ 90°C. (Configurable in the code)
  - Warns (orange console output) if power ≥ 23 W, chip temperature ≥ 63°C, or VR temperature ≥ 80°C. (Configurable in the code)
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

## Ambient Air Temperature Changes
The ambient air temperatures will fluctuate from night to day. This is why you should not push your bitaxe to the limit as temperatures can change throughout the day. Best to keep below maximum limits to allow for ambient air temperature changes.

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
