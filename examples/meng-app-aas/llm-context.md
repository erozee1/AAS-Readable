# AAS LLM Context

This file is optimized for pasting into an LLM as compact, structured context.

## Source

- File: `app_aas.json`
- Format: `json`

## Asset Administration Shells

### DataCollectionApp_AAS

- Identifier: `https://example.com/ids/aas/DataCollectionApp_001`
- Asset Kind: `Instance`
- Global Asset ID: `https://example.com/ids/asset/DataCollectionApp_001`
- Referenced Submodels: `4`
  - `https://example.com/ids/sm/StaticData_001`
  - `https://example.com/ids/sm/FunctionalData_001`
  - `https://example.com/ids/sm/OperationalData_001`
  - `https://example.com/ids/sm/LifecycleData_001`


## Submodel Summaries

### StaticData

- Identifier: `https://example.com/ids/sm/StaticData_001`
- Description: Static data and identification information for the Vibration Analysis Application
- Semantic ID: `https://admin-shell.io/zvei/nameplate/1/0/Nameplate`

#### Key Elements

- `AppName`: type=Property, value=Data Collection App
- `AppID`: type=Property, value=APP-VA-PRO-2024-001
- `AppVersion`: type=Property, value=3.2.1
- `Developer`: type=Property, value=Omnifactory
- `LicenseKey`: type=Property, value=VA-PRO-8F7D-4C2E-9A1B-3E5F6D8C9B2A
- `DatePublished`: type=Property, value=2024-03-15T10:30:00Z
- `SupportedSensors`: type=MultiLanguageProperty, value=SICK-VS-100, SICK-VS-200, SICK-AE-300, SICK-Acoustic-500
- `UserAccessLevel`: type=Property, value=Administrator

### FunctionalData

- Identifier: `https://example.com/ids/sm/FunctionalData_001`
- Description: Functional capabilities and sensor integration data
- Semantic ID: `https://admin-shell.io/idta/TechnicalData/1/1/TechnicalData`

#### Key Elements

- `SICKVibrationSensor`: type=SubmodelElementCollection
  - `SensorModel`: type=Property, value=SICK-VS-200
  - `SensorID`: type=Property, value=VS-200-SNR-45782
  - `MeasurementRange`: type=Property, value=0-50
  - `SamplingRate`: type=Property, value=25600
  - `FrequencyRange`: type=Property, value=10-10000
  - `ConnectionStatus`: type=Property, value=Connected
- `AcousticEmissionSensor`: type=SubmodelElementCollection
  - `SensorModel`: type=Property, value=SICK-AE-300
  - `SensorID`: type=Property, value=AE-300-SNR-12459
  - `FrequencyRange`: type=Property, value=100000-500000
  - `SamplingRate`: type=Property, value=1000000
  - `Sensitivity`: type=Property, value=-65
  - `ConnectionStatus`: type=Property, value=Connected

### OperationalData

- Identifier: `https://example.com/ids/sm/OperationalData_001`
- Description: Real-time operational status and performance metrics
- Semantic ID: `https://admin-shell.io/idta/OperationalData/1/0/OperationalData`

#### Key Elements

- `LastDataReceived`: type=Property, value=2025-11-21T15:09:11Z
- `TotalDataPointsCollectedLastCycle`: type=Property, value=154872
- `ProcessingStatus`: type=Property, value=Processing
- `CycleTime`: type=Property, value=3.47
- `AverageCycleTime`: type=Property, value=3.52
- `CPULoad`: type=Property, value=42.3
- `MemoryUsage`: type=Property, value=2847

### LifecycleData

- Identifier: `https://example.com/ids/sm/LifecycleData_001`
- Description: Lifecycle management and maintenance tracking information
- Semantic ID: `https://admin-shell.io/idta/Lifecycle/1/0/Lifecycle`

#### Key Elements

- `TotalUptime`: type=Property, value=8947.5
- `LastMaintenanceDate`: type=Property, value=2024-10-15T09:00:00Z
- `NextScheduledMaintenance`: type=Property, value=2025-01-15T09:00:00Z
- `MaintenanceInterval`: type=Property, value=2160
- `NumberOfCyclesRun`: type=Property, value=784521
- `ErrorLogs`: type=SubmodelElementCollection
  - `Error_001`: type=SubmodelElementCollection
    - `Timestamp`: type=Property, value=2024-11-18T16:23:45Z
    - `ErrorCode`: type=Property, value=ERR-2047
    - `Severity`: type=Property, value=Warning
    - `Description`: type=Property, value=Sensor communication timeout - Auto-recovered
  - `Error_002`: type=SubmodelElementCollection
    - `Timestamp`: type=Property, value=2024-11-20T10:15:32Z
    - `ErrorCode`: type=Property, value=WRN-1023
    - `Severity`: type=Property, value=Warning
    - `Description`: type=Property, value=High CPU load detected - 87% utilization
- `OperationalStatus`: type=Property, value=Active

