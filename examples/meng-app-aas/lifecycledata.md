# LifecycleData

## Metadata

- Identifier: `https://example.com/ids/sm/LifecycleData_001`
- Id Short: `LifecycleData`
- Kind: `Instance`
- Semantic ID: `https://admin-shell.io/idta/Lifecycle/1/0/Lifecycle`
- Description: Lifecycle management and maintenance tracking information

## Elements

### TotalUptime

- Type: `Property`
- Value: `8947.5`
- Value Type: `xs:float`
- Semantic ID: `0173-1#02-AAO738#004`

### LastMaintenanceDate

- Type: `Property`
- Value: `2024-10-15T09:00:00Z`
- Value Type: `xs:dateTime`
- Semantic ID: `0173-1#02-AAO353#002`

### NextScheduledMaintenance

- Type: `Property`
- Value: `2025-01-15T09:00:00Z`
- Value Type: `xs:dateTime`
- Semantic ID: `0173-1#02-AAO354#003`

### MaintenanceInterval

- Type: `Property`
- Value: `2160`
- Value Type: `xs:integer`

### NumberOfCyclesRun

- Type: `Property`
- Value: `784521`
- Value Type: `xs:integer`
- Semantic ID: `0173-1#02-AAO102#005`

### ErrorLogs

- Type: `SubmodelElementCollection`
- Semantic ID: `https://admin-shell.io/idta/ErrorLog/1/0`

#### Children

#### Error_001

- Type: `SubmodelElementCollection`

##### Children

##### Timestamp

- Type: `Property`
- Value: `2024-11-18T16:23:45Z`
- Value Type: `xs:dateTime`

##### ErrorCode

- Type: `Property`
- Value: `ERR-2047`
- Value Type: `xs:string`

##### Severity

- Type: `Property`
- Value: `Warning`
- Value Type: `xs:string`

##### Description

- Type: `Property`
- Value: `Sensor communication timeout - Auto-recovered`
- Value Type: `xs:string`


#### Error_002

- Type: `SubmodelElementCollection`

##### Children

##### Timestamp

- Type: `Property`
- Value: `2024-11-20T10:15:32Z`
- Value Type: `xs:dateTime`

##### ErrorCode

- Type: `Property`
- Value: `WRN-1023`
- Value Type: `xs:string`

##### Severity

- Type: `Property`
- Value: `Warning`
- Value Type: `xs:string`

##### Description

- Type: `Property`
- Value: `High CPU load detected - 87% utilization`
- Value Type: `xs:string`



### OperationalStatus

- Type: `Property`
- Value: `Active`
- Value Type: `xs:string`
- Semantic ID: `https://admin-shell.io/idta/OperationalStatus/1/0`

