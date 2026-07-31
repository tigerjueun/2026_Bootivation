# Final Runbook

이 문서는 Bootivation 전체 장치를 다시 실행하는 순서를 정리합니다. 실제 IP와 COM 포트는 현장 환경에 맞게 수정하고, 비밀번호·개인 계정 정보는 저장소에 커밋하지 않습니다.

## 0. Startup order

```text
1. POS 및 Rider 전원·포트 확인
2. Raspberry Pi tray 실행
3. Fusion PC 실행
4. Vision camera/model/WebUI 실행
5. Vision 5555 transmitter 실행
6. 각 채널 수신 확인
7. 고객 또는 Rider 시나리오 시작
```

Vision 5555는 POS/EXIT를 한 번만 발행하므로 Fusion SUB를 transmitter보다 먼저 실행하는 것이 안전합니다.

---

## 1. Repository checkout

통합 저장소:

```bash
git clone https://github.com/tigerjueun/2026_Bootivation.git
cd 2026_Bootivation
```

Vision upstream:

```bash
git clone https://github.com/Kuz-DX/ssg-ssac-cctv.git vision/ssg-ssac-cctv
cd vision/ssg-ssac-cctv
git checkout 3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef
```

최신 upstream을 사용하려면 checkout 줄을 생략할 수 있지만, 이 아카이브 문서는 위 커밋을 기준으로 작성했습니다.

---

## 2. Serial devices on Fusion PC

PowerShell:

```powershell
Get-CimInstance Win32_SerialPort |
  Select-Object DeviceID, Name
```

Expected:

```text
COM5   ATmega128 POS UART
COM10  BOOTI_RIDER Bluetooth SPP
```

Before Fusion starts, close:

```text
Arduino Serial Monitor
Microchip Studio terminal
App Inventor Bluetooth connection
rider_serial_test.py
other COM5/COM10 readers
```

---

## 3. Raspberry Pi tray

### Network

```bash
ip -br address show eth0
ping -c 3 10.77.0.1
```

Expected Ethernet address:

```text
10.77.0.2/24
```

### Camera and audio

```bash
rpicam-hello --list-cameras
pw-play ~/Bootivation/rpi_tray/audio/wav/system_ready.wav
```

### Runtime

```bash
cd ~/Bootivation/rpi_tray_single
python3 single_slot_counter_zmq_audio.py \
  --bind 'tcp://*:5562' \
  --command-bind 'tcp://*:5563'
```

Expected logs:

```text
[rpi-zmq] PUB counts: tcp://*:5562
[rpi-zmq] PULL commands: tcp://*:5563
[audio] directory: .../audio/wav
```

Startup audio:

```text
system_ready.wav
place_before.wav
```

Check listeners:

```bash
ss -ltnp | grep -E ':5562|:5563'
```

---

## 4. Fusion PC

### Config

```powershell
cd C:\Project\2026\Bootivation\Bootivation_v2\fusion_pc
Copy-Item .\config\system.example.json .\config\system.json
notepad .\config\system.json
```

Set:

```json
{
  "pos": {
    "enabled": true,
    "port": "COM5",
    "baud": 57600,
    "timeout_sec": 0.2
  },
  "rider": {
    "enabled": true,
    "port": "COM10",
    "baud": 9600,
    "timeout_sec": 0.2,
    "pick_source": "vision"
  },
  "vision": {
    "enabled": true,
    "subscriber_endpoint": "tcp://VISION_PC_IP:5555",
    "topic": "retail"
  }
}
```

### Install and run

```powershell
py -m pip install -r .\requirements.txt

py .\main.py `
  --config .\config\system.json `
  --rpi-endpoint tcp://10.77.0.2:5562 `
  --rpi-command-endpoint tcp://10.77.0.2:5563
```

Expected:

```text
[pos] connected COM5 @ 57600
[rider] connected COM10 @ 9600
[rpi] SUB tcp://10.77.0.2:5562
[vision] SUB tcp://VISION_PC_IP:5555
[ui] http://127.0.0.1:8088
```

Dashboard:

```text
http://127.0.0.1:8088
```

Check the RPi port from Windows:

```powershell
Test-NetConnection 10.77.0.2 -Port 5562
Test-NetConnection 10.77.0.2 -Port 5563
```

---

## 5. Ubuntu Vision PC

Vision source: [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)

### Dependencies

```bash
cd /home/kuzdx/bootivation
source /opt/ros/humble/setup.bash
python3 -m pip install -r perception/requirements.txt
```

Required model files are described in [`models/README.md`](../models/README.md). Confirm camera devices, model paths and ROI values in:

```text
perception/src/retail_perception/config/pipeline.yaml
```

### Camera/model/WebUI

```bash
cd /home/kuzdx/bootivation
./webUI/run_model_test.sh
```

Open:

```text
http://VISION_PC_IP:8080
```

Check camera topics:

```bash
ros2 topic hz /camera1/image_raw/compressed
ros2 topic hz /camera2/image_raw/compressed
```

### Customer-state transmitter — separate terminal

The final upstream `run_model_test.sh` does not automatically start the 5555 transmitter.

```bash
cd /home/kuzdx/bootivation
source /opt/ros/humble/setup.bash

PYTHONPATH="$PWD/perception/src/retail_perception${PYTHONPATH:+:$PYTHONPATH}" \
python3 -c 'from retail_perception.zmq_transmitter_node import main; main()' \
  --ros-args \
  --params-file "$PWD/perception/src/retail_perception/config/pipeline.yaml"
```

Expected:

```text
Publishing customer states on tcp://*:5555
```

Check ports:

```bash
ss -ltnp | grep -E ':5555|:5556'
```

From Fusion PC:

```powershell
Test-NetConnection VISION_PC_IP -Port 5555
Test-NetConnection VISION_PC_IP -Port 5556
```

---

## 6. Emergency channel test

Run the Vision WebUI first, then send a request from Fusion PC or any trusted host with pyzmq.

```python
import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.LINGER, 0)
socket.setsockopt(zmq.RCVTIMEO, 3000)
socket.connect("tcp://VISION_PC_IP:5556")

socket.send_json({
    "Emergency": True,
    "customer_id": 100,
})

print(socket.recv_json())
socket.close()
context.term()
```

Expected response:

```json
{
  "ok": true,
  "customer_id": 100,
  "snapshot_available": true
}
```

The Vision WebUI should show a red theft alert and the customer's Camera 1 entry snapshot. The default snapshot directory is:

```text
/tmp/bootivation_customer_captures
```

---

## 7. Customer scenario

```text
1. Customer enters through Camera 1 entrance ROI.
2. Vision assigns customer_id.
3. Customer picks A/B/C items.
4. Customer reaches the POS ROI.
5. Vision sends state=POS on 5555.
6. POS CUSTOMER scans items and presses DONE.
7. Fusion sends PAYMENT_CONFIRMED to RPi.
8. Customer transfers items from BEFORE to AFTER tray.
9. RPi compares AFTER with expected counts.
10. Vision sends state=EXIT on customer exit.
11. Fusion compares final picked count with paid count.
```

Expected normal result:

```text
picked == paid
AFTER == expected
no RED / no emergency
```

Unpaid result:

```text
picked > paid
→ Rider RED
→ RPi tray_mismatch.wav
→ Vision Emergency :5556
→ WebUI theft alert + entry snapshot
```

---

## 8. Rider scenario

Fusion console:

```text
order A=1,B=1,C=1
```

Expected sequence:

```text
BLUE + SERVO:A
Vision A removal → SERVO:B
Vision B removal → SERVO:C
Vision C removal → HOME, wait for Rider POS
Rider POS A/B/C + DONE
order == removed == checked
→ GREEN + PICKUP_COMPLETE
```

Error checks:

```text
order A=1,B=1
Vision removes C
→ WRONG_PICKUP:C / RED
```

---

## 9. Shutdown

1. Stop Fusion with `quit` or `Ctrl+C`.
2. Stop Vision transmitter and WebUI.
3. Stop RPi with `Q` or `Ctrl+C`.
4. Close serial ports before unplugging boards.
5. Use `sudo poweroff` before touching CSI camera cables.

---

## 10. Troubleshooting checklist

| Symptom | Check |
|---|---|
| Vision log absent | separate 5555 transmitter, `topic=retail`, firewall, Fusion started first |
| Emergency no response | WebUI running, 5556 listener, REQ/REP timeout, customer snapshot exists |
| RPi values absent | 10.77.0.2, 5562 listener, previous mock publisher stopped |
| WAV absent | `pw-play`, Bluetooth speaker default sink, audio file path |
| Rider LED works but servo misses | external servo power, common GND, D9, command gap |
| POS boot repeats | power/USB instability, 5V-GND short, soldering |
| Duplicate payment | detailed `PAY_DONE` must reconcile rather than add another batch |
