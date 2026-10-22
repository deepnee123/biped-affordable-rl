| Specification | Value |
|---|---|
| Transmission | Custom 3D-printed cycloidal reducer, **17:1** |
| Manufacturing assumptions | High-resolution print; high wall count; lubrication to mitigate friction |
| Motor | **5010 brushless outrunner, 360 KV** |
| Motor controller | **MKS XDrive Mini**, ODrive copycat field-oriented control |
| Controller working / peak current | **60 A / 120 A** as supplied for the controller; **not motor ratings** |
| Proposed operating motor `Iq` limit | **40 A** |
| Battery | **6S LiPo**, 22.2 V nominal / 25.2 V fully charged |
| Gearbox efficiency, design assumption | **85%** (not measured) |
| Gearbox efficiency, predicted test scenario | **80%** (not measured) |
| Estimated motor torque constant | **0.02297 N·m/A** (`8.27 / KV`, ODrive current convention) |
| Motor torque at 40 A `Iq` | **0.919 N·m** (theoretical) |
| Gearbox output at 40 A, ideal 100% | **15.62 N·m** |
| Gearbox output at 40 A, 85% design | **13.28 N·m** (estimated) |
| Gearbox output at 40 A, 80% | **12.50 N·m** |
| Ideal no-load joint speed (22.2 V) | **470 RPM**, approximately **49.2 rad/s** |
| Ideal no-load joint speed (25.2 V) | **534 RPM**, approximately **55.9 rad/s** |
| Verified peak / continuous joint torque | **TBD / TBD** |
| Actual efficiency, backlash, weight, stiffness | **TBD** |
