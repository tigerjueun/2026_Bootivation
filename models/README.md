# Model Artifacts

Bootivation Vision source is available at [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv), but cloning the repository alone may not reproduce inference because the upstream `.gitignore` excludes `*.pt` files.

This directory intentionally documents the runtime artifacts instead of redistributing weights without confirming size, ownership and license.

## 1. Runtime assets referenced by the final Vision configuration

Place model files under the upstream workspace:

```text
ssg-ssac-cctv/perception/weights/
```

| File | Purpose | Class / format information | Included in this archive? |
|---|---|---|---:|
| `retail_best1.pt` | integrated person·hand·A/B/C YOLO | model order `A=0, B=1, C=2, hand=3, person=4` | no |
| `box1.pt` | auxiliary A/B/C product detector | `A=0, B=1, C=2` | no |
| `hand_1(epo100).pt` | dedicated hand detector used by final pipeline config | hand class configured as `[0]` | no |
| `person-reidentification-retail-0288.xml` | OpenVINO Person Re-ID graph | Open Model Zoo IR | no |
| `person-reidentification-retail-0288.bin` | OpenVINO Person Re-ID weights | pair with XML | no |

The exact names above are derived from the final upstream source/configuration. Confirm them against `perception/src/retail_perception/config/pipeline.yaml` before running.

## 2. Expected layout

```text
vision/ssg-ssac-cctv/
└── perception/
    └── weights/
        ├── retail_best1.pt
        ├── box1.pt
        ├── hand_1(epo100).pt
        ├── person-reidentification-retail-0288.xml
        └── person-reidentification-retail-0288.bin
```

## 3. Class mapping

Final integrated-model mapping:

```yaml
integrated_person_class_ids: [4]
integrated_hand_class_ids: [3]
integrated_product_a_class_ids: [0]
integrated_product_b_class_ids: [1]
integrated_product_c_class_ids: [2]
```

Auxiliary product mapping:

```yaml
product_a_class_ids: [0]
product_b_class_ids: [1]
product_c_class_ids: [2]
```

If a model is retrained or replaced, inspect its `names` or training `data.yaml` and update the mapping. Do not assume another `.pt` file uses the same class order.

## 4. Artifact manifest recommendation

For every team-provided model, record:

```yaml
name: retail_best1.pt
owner_or_source: team artifact / source URL
license: confirm before redistribution
sha256: <64 hex characters>
size_bytes: <integer>
framework: Ultralytics YOLO
input_size: <configured image size>
classes:
  0: A
  1: B
  2: C
  3: hand
  4: person
training_dataset: <name or internal reference>
notes: <evaluation and known limits>
```

Generate a hash:

```bash
sha256sum perception/weights/retail_best1.pt
```

PowerShell:

```powershell
Get-FileHash .\retail_best1.pt -Algorithm SHA256
```

## 5. Git LFS policy

Only add a model to this public repository when the team confirms redistribution rights.

```bash
git lfs install
git lfs track "*.pt" "*.onnx" "*.engine" "*.bin"
git add .gitattributes
git add models/ vision/ssg-ssac-cctv/perception/weights/
git commit -m "chore(models): add licensed runtime artifacts with LFS"
```

Git LFS tracks files but does not resolve licensing. Keep upstream attribution and model licenses.

## 6. External artifact alternative

When redistribution is unclear or files are too large:

```text
GitHub repository
→ manifest, hash, download instructions

Team Drive / release asset
→ actual model file with controlled access
```

Never commit expiring private links, API tokens or personal cloud credentials.

## 7. OpenVINO Re-ID source

The `person-reidentification-retail-0288` model belongs to the Open Model Zoo ecosystem. Preserve the applicable Open Model Zoo/OpenVINO license and attribution when obtaining or redistributing it.

## 8. Current archive status

```text
[x] Required filenames documented
[x] Class mappings documented
[x] Runtime locations documented
[ ] Team YOLO weights received into the integrated archive
[ ] Redistribution/license decision recorded
[ ] SHA-256 manifest added
[ ] Optional Git LFS upload completed
```
