---
name: Vision artifact handoff
about: Vision upstream, model weights, media and protocol integration checklist
title: "[vision] upstream / model artifact update"
labels: vision, handoff
assignees: ''
---

## Upstream

- [ ] Repository URL recorded
- [ ] Archive commit SHA recorded
- [ ] Contributor attribution preserved
- [ ] README / launch / config verified

## Runtime artifacts

- [ ] `retail_best1.pt`
- [ ] `box1.pt`
- [ ] dedicated hand model if required
- [ ] OpenVINO Re-ID XML/BIN
- [ ] class mapping recorded
- [ ] SHA-256 manifest recorded
- [ ] source and redistribution license recorded
- [ ] Git LFS or external artifact location selected

## Protocols

- [ ] customer-state `retail {JSON}` on 5555 verified
- [ ] final `state=POS` / `state=EXIT` semantics verified
- [ ] Emergency REQ/REP 5556 verified
- [ ] Fusion adapter/replay test updated

## Reproduction

- [ ] dependencies/environment
- [ ] camera topic names
- [ ] final ROI/homography config
- [ ] execution order
- [ ] sample logs
- [ ] result images/video
