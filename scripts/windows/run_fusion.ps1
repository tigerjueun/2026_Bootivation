param([string]$Config='.\config\system.json',[string]$RpiEndpoint='tcp://10.77.0.2:5562',[string]$RpiCommandEndpoint='tcp://10.77.0.2:5563')
Set-Location "$PSScriptRoot\..\..\fusion_pc"
py .\main.py --config $Config --rpi-endpoint $RpiEndpoint --rpi-command-endpoint $RpiCommandEndpoint
