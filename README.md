# WARNING: This code overclocks your BitAxe and could damage it. I take no responsibility for damage to your BitAxe. Use at your own risk!!!

My bitaxe has upgraded thermal paste, a low-profile pro heatsink, 2 Noctua NF-A6x25 fans, a 100W Mean Well power supply, and 2 additional fan blowing on it (See Image). Be careful with the settings inside the code and the values.csv file to ensure they meet your requirements and your bitaxe capabilities.

![Image 1](https://github.com/andelorean/bitaxe_frequency_sweeper/blob/main/bitaxe1.png "BitAxe Image 1")
![Image 2](https://github.com/andelorean/bitaxe_frequency_sweeper/blob/main/bitaxe2.png "BitAxe Image 2")

# Bitaxe Frequency Sweeper and Status Logger

The **Bitaxe Status Logger** is a Python script for monitoring and optimizing the performance of a Bitaxe Bitcoin mining device. It tracks key metrics such as hashrate, temperature, voltage regulator temperature, power consumption, and Joules per Terahash (J/TH), logging them to CSV files for analysis. The script supports both testing across a frequency range and continuous monitoring with dynamic adjustments based on a provided list of known good voltage/frequency pairs.

The idea is that you already know from this or other tuning scripts and efforts approximately how hard you can drive your BitAxe in terms of Voltage without going over the Power, Temperature, or Voltage Regulator Temperatures. I know my voltage limit is 1362mV. This code helps find the optimal frequency for a given voltage or a range of voltages.

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
>python bitaxe_status_logger.py -f 650 -v 1136 -range 5 -step 1 -ip [your bitaxe ip] -reboot 5
```
This will test the frequencies from 645 to 655 in increments of 1 (step), run for 10 minutes each (configurable in the code), find the maximum hashrate, and set the Bitaxe at the end to the voltage and frequency that produces the highest hashrate. All while logging and displaying updates. If any temp, VR temp, or power exceed critical thresholds it will fall back. If the bitaxe hangs and produces 5 same hashrate readings, it will reboot the Bitaxe.

Then, once you have a list of optimal frequencies and voltages, you place them in a CSV (values.csv) and run your system. The code will keep climbing as high as possible without going over the critical temp, vr temp, or power settings defined in the CONFIG section of the code. There is a "critical_advance_margin" value, meaning the code will not advance if the critical temp, VR temp, or Power is within this margin of safety. Thus, if your critical_advance_margin=2, you are running at 43W, and your max_power_critical=44, the system will not advance. If you want to push the limits, these values will need to be modified.

```
>python bitaxe_status_logger.py -v 1290 -f 992 -m -values values.csv -ip [your bitaxe ip] -reboot 5

values.csv
#Voltage,Frequency
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
```
>python bitaxe_status_loger.py -start 1290 -stop 1302 -range 3 -step 1 -values values.csv -reboot 5 -ip [your bitaxe ip]
```
This will use the frequencies from the values.csv file as the starting point for each test. This will test +/- 3 MHz around each frequency in the values.csv file to find the max hashrate for the voltage in increments of 1 (step size). It will test voltages from 1290 to 1302 in steps of 1 (not configurable). If there is no entry in the values.csv file for a voltage, it will attempt to calculate it using the equation in bm1370_voltage_calculator.py


# Bitaxe Status Logger

The Bitaxe Status Logger is a Python script for monitoring and testing the performance of a Bitaxe mining device. It collects metrics such as hashrate, temperature, power consumption, and efficiency (J/TH) across specified voltage and frequency ranges, or in continuous monitor mode. The script supports automated testing, dynamic adjustments based on predefined settings, and detailed logging for analysis.

## Features

- **Voltage and Frequency Sweeps**: Test a range of core voltages (`-start` and `-stop`) and frequencies (`-range` and `-step`) to identify optimal performance settings.
- **Monitor Mode**: Continuously monitor the Bitaxe at a specified voltage and frequency, with optional dynamic adjustments using a `values.csv` file.
- **CSV-Based Frequency Selection**: Use a `values.csv` file to specify center frequencies for voltage sweeps or monitor mode, overriding calculated frequencies.
- **Comprehensive Logging**:
  - `readings_*.csv`: Time-series data for hashrate, temperature, power, and more.
  - `summaries_*.csv`: Per-test summaries with min, max, and average metrics.
  - `values-found_*.csv`: Best hashrate per voltage, including frequency range and average J/TH.
- **Safety Thresholds**: Configurable critical and warning thresholds for chip temperature, voltage regulator temperature, and power consumption to protect the device.
- **Best Hashrate Configuration**: Automatically sets the Bitaxe to the voltage and frequency yielding the highest hashrate after a sweep.
- **Status Timers**: Displays multiple timers in the console: current test time remaining, current voltage time remaining, total time required, and all tests time remaining.
- **Reboot Handling**: Optional reboot trigger after a specified number of identical hashrate readings to recover from potential stalls.
- **Robust CSV Parsing**: Handles UTF-8 BOM and skips invalid rows or comments in `values.csv`.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/bitaxe-status-logger.git
   cd bitaxe-status-logger
   ```

2. **Install Dependencies**:
   Requires Python 3.6+ and the `requests` library. Install it using pip:
   ```bash
   pip install requests
   ```

3. **Prepare `values.csv` (Optional)**:
   If using the `-values` option, create a `values.csv` file with voltage-frequency pairs. Example:
   ```csv
   # Voltage(mV),Frequency(MHz),Hashrate(GH/s)
   1280,972,1617.74
   1325,1089,2348.37
   ```
   Save it in the project directory or specify its path with `-values`.

## Usage

Run the script with `python3 bitaxe_status_logger.py` followed by the required and optional arguments. Use `-h` for help:

```bash
python3 bitaxe_status_logger.py -h
```

### Examples

1. **Voltage and Frequency Sweep**:
   Test voltages from 1280 mV to 1325 mV, sweeping frequencies from `values.csv` or calculated values ±3 MHz with 1 MHz steps:
   ```bash
   python3 bitaxe_status_logger.py -start 1280 -stop 1325 -ip 192.168.2.205 -range 3 -step 1 -reboot 5 -values values.csv
   ```

2. **Monitor Mode**:
   Monitor at 1325 mV, using frequency from `values.csv` for the closest voltage, with reboot after 5 identical hashrates:
   ```bash
   python3 bitaxe_status_logger.py -m -v 1325 -ip 192.168.2.205 -values values.csv -reboot 5
   ```

3. **Single Voltage Test**:
   Test a single voltage (1320 mV) with frequency sweep ±10 MHz, step 2 MHz:
   ```bash
   python3 bitaxe_status_logger.py -v 1320 -f 1055 -ip 192.168.2.205 -range 10 -step 2
   ```

### Configuration

The script uses a `CONFIG` dictionary for key parameters, defined at the top of `bitaxe_status_logger.py`. Key settings include:

- **run_duration**: Duration of each test run (default: 600s = 10 minutes).
- **log_interval**: Interval for logging to readings.csv (default: 10s).
- **status_interval**: Interval for console status updates (default: 10s).
- **max_temp_critical**: Critical chip temperature threshold (default: 67°C).
- **max_vrtemp_critical**: Critical voltage regulator temperature threshold (default: 90°C).
- **max_power_critical**: Critical power consumption threshold (default: 44W).
- **min_frequency**: Minimum allowable frequency (default: 400 MHz).
- **min_core_voltage**: Minimum allowable core voltage (default: 1000 mV).
- **range**: Frequency sweep range (default: 10 MHz).
- **step**: Frequency step size (default: 2 MHz).
- **reboot**: Number of identical hashrate readings for reboot (default: None).

See the script’s `CONFIG` comments for detailed descriptions. Modify these values directly in the script to adjust behavior.

### Output Files

- **readings_volt_start_X_stop_Y_TIMESTAMP.csv** or **readings_volt_X_freq_Y_TIMESTAMP.csv**:
  Time-series data with columns: `Timestamp`, `Hashrate(GH/s)`, `Frequency(MHz)`, `Temp(°C)`, `VRTemp(°C)`, `CoreVoltage(mV)`, `CoreVoltageActual(mV)`, `Power(W)`, `Current(mA)`, `Voltage(mV)`, `J/TH`, `Note`.

- **summaries_volt_start_X_stop_Y_TIMESTAMP.csv** or **summaries_volt_X_freq_Y_TIMESTAMP.csv**:
  Per-test summaries with min, max, and average metrics, plus best hashrate per voltage (single-line format).

- **values-found_volt_start_X_stop_Y_TIMESTAMP.csv**:
  Best hashrate per voltage with columns: `Voltage(mV)`, `Frequency(MHz)`, `Hashrate(GH/s)`, `MinFreqTested(MHz)`, `MaxFreqTested(MHz)`, `AvgJTH(J/TH)`.

### Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -am 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please include tests and documentation updates with your changes.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- This code was 100% written by Grok from my prompting! Grok Rocks!
- Built for the Bitaxe Bitcoin mining device.
- Inspired by the need for automated performance optimization and monitoring in cryptocurrency mining.

## Inspirational Shoutouts
- Starficient: https://github.com/kha1n3vol3/BitaxePID
- Hurllz: https://github.com/Hurllz/bitaxe-temp-monitor/
- WhiteyCookie: https://github.com/WhiteyCookie/Bitaxe-Hashrate-Benchmark
- mrv777: https://github.com/mrv777/bitaxe-hashrate-benchmark


---
*Generated on May 31, 2025*
