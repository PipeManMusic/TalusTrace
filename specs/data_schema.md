# Talus Trace Data & Serialization Specification

**Version:** 2.0
**Scope:** File Format, YAML Schema, and Concurrency Rules.

## 1. Project File Structure (`.talus`)
* **Format:** YAML 1.2, UTF-8.
* **Structure:** `catalog` (Definitions) + `layout` (Instances).

### 1.1. Schema Example
```yaml
meta:
  version: "2.0"
  revision_head: 42
catalog:
  components:
    - id: "dt06_2s"
      name: "Deutsch DT 2-Pin"
      pins: ["1", "2"]
      bundle_anchor: [15.0, 0.0] # Physical connection point
layout:
  devices:
    - uuid: "dev_550e"
      revision: 5
      library_id: "dt06_2s"
      pos: [100, 200]
      service_loop_mm: 50 
  connections:
    - uuid: "wire_a1"
      net_id: "net_pwr"
      src: "dev_550e.1"
      dst: "dev_other.A"