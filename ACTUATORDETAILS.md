# Huge thanks to Berkley Humanoid lite for actuator inspiration
Unfortunately their BOM is slightly outdated so I couldn't get my hands on the exact motor they were using. I settled with a much cheaper, higher Kv and smaller motor which I had to redesign the gearbox for. according to my calculations, my version should achieve roughly half of their torque compared to their leg joints(~20 Nm)

| Specification | Value |
|---|---|
| Transmission | Custom 3D-printed cycloidal reducer, **17:1** |
| Manufacturing assumptions | High-resolution print; high wall count; lubrication to mitigate friction |
| Motor | **5010 brushless outrunner, 360 KV** |
| Motor controller | **MKS XDrive Mini**, ODrive copycat field-oriented control |
| Controller working / peak current | **60 A / 120 A** as supplied for the controller; **not motor ratings** |
| conservative operating motor `Iq` limit | **40 A** |
| Battery | **6S LiPo**, 22.2 V nominal / 25.2 V fully charged |
| Gearbox efficiency, design assumption | **85%** |
| Gearbox efficiency, predicted test scenario | **80%** |
| Estimated motor torque constant | **0.02297 N·m/A** (`8.27 / KV`, ODrive current convention) |
| Motor torque at 40 A `Iq` | **0.919 N·m** (theoretical) |
| Gearbox output at 40 A, ideal 100% | **15.62 N·m** |
| Gearbox output at 40 A, 85% design | **13.28 N·m** (estimated) |
| Gearbox output at 40 A, 80% | **12.50 N·m** |
| Ideal no-load joint speed (22.2 V) | **470 RPM**, approximately **49.2 rad/s** |
| Ideal no-load joint speed (25.2 V) | **534 RPM**, approximately **55.9 rad/s** |
| Verified peak / continuous joint torque | **TBD / TBD** |
| Actual efficiency, backlash, weight, stiffness | **TBD** |

Here are some explanations regarding the values:
Motor and joint torque calculation
## Motor and joint torque calculation

Using the approximate ODrive motor-current convention:

Kt = 8.27/kv = 8.27/360 = 0.02297 Nm per Amp

so motor torque becomes:
𝜏 = Kt * I
and joint torque:
𝜏 = n*G*kt*I  where n is approx. efficiency, G is reduction ratio

so at the 40A soft limit and at 80% efficiency, torque should be around:
𝜏(motor) = 0.919(17)(0.80) = 12.5 Nm 

likewise, at 85% would just multiply by 0.85 rather than 0.8
coming out to be around 13.3 Nm

this is very competitive compared to actuators on the market in terms of cost and torque output, HOWEVER
obviously this is under ideal circumstances at a higher motor current than I would like to run, and the robot likely won't need this much torque anyway. in the simulation the robot is configured at 12 Nm of torque per joint and it is plenty enough due to frame being printed out of lightweight polycarbonate. Additionally, there are other factors like heat, differing friction at different speeds, other behaviors underload, etc. My educated guess would be around ~7 Nm of continuous torque(will definitely test soon)

ideal conditions:
| Motor Amperage | Motor torque (N·m) | Ideal gearbox output (N·m) | Design at 85% (N·m) | Predicted test at 80% (N·m) |
|---:|---:|---:|---:|---:|
| 5 | 0.115 | 1.95 | 1.66 | 1.56 |
| 10 | 0.230 | 3.91 | 3.32 | 3.12 |
| 15 | 0.345 | 5.86 | 4.98 | 4.69 |
| 20 | 0.459 | 7.81 | 6.64 | 6.25 |
| 25 | 0.574 | 9.76 | 8.30 | 7.81 |
| 30 | 0.689 | 11.72 | 9.96 | 9.37 |
| 35 | 0.804 | 13.67 | 11.62 | 10.93 |
| **40** | **0.919** | **15.62** | **13.28** | **12.50** |
