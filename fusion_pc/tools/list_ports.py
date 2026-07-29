from serial.tools import list_ports
for port in list_ports.comports():print(f'{port.device:8} {port.description} [{port.hwid}]')
