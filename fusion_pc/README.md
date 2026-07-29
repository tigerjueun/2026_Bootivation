# Fusion PC

Windows 중앙 상태머신. POS COM5, Rider COM10, RPi 5562/5563, Vision 5555, 운영 UI 8088을 통합합니다.

```powershell
py -m pip install -r requirements.txt
Copy-Item .\config\system.example.json .\config\system.json
py .\main.py --config .\config\system.json --rpi-endpoint tcp://10.77.0.2:5562 --rpi-command-endpoint tcp://10.77.0.2:5563
```
