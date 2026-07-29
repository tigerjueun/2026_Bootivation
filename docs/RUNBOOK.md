
# Final runbook

## Raspberry Pi

```bash
cd ~/Bootivation/rpi_tray_single
python3 single_slot_counter_zmq_audio.py \
  --bind 'tcp://*:5562' \
  --command-bind 'tcp://*:5563'
```

## Ubuntu Vision PC

```bash
cd /home/kuzdx/bootivation
./webUI/run_model_test.sh
```

별도 터미널:

```bash
source /opt/ros/humble/setup.bash
PYTHONPATH="$PWD/perception/src/retail_perception${PYTHONPATH:+:$PYTHONPATH}" \
python3 -c 'from retail_perception.zmq_transmitter_node import main; main()' \
  --ros-args \
  --params-file "$PWD/perception/src/retail_perception/config/pipeline.yaml"
```

## Fusion PC

```powershell
cd C:\Project\2026\Bootivation\Bootivation_v2\fusion_pc
py .\main.py `
  --config .\config\system.json `
  --rpi-endpoint tcp://10.77.0.2:5562 `
  --rpi-command-endpoint tcp://10.77.0.2:5563
```

Dashboard: `http://127.0.0.1:8088`
