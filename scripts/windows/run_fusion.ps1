param(
    [string]$Config = '.\config\system.json',
    [string]$RpiEndpoint = 'tcp://10.77.0.2:5562',
    [string]$RpiCommandEndpoint = 'tcp://10.77.0.2:5563',
    [string]$VisionEmergencyEndpoint = ''
)

$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot\..\..\fusion_pc"

$arguments = @(
    '.\main.py',
    '--config', $Config,
    '--rpi-endpoint', $RpiEndpoint,
    '--rpi-command-endpoint', $RpiCommandEndpoint
)

if ($VisionEmergencyEndpoint) {
    $arguments += @(
        '--vision-emergency-endpoint',
        $VisionEmergencyEndpoint
    )
}

py @arguments
