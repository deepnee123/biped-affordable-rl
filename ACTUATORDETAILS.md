# Huge thanks to Berkley Humanoid lite for actuator inspiration
Unfortunately their BOM is slightly outdated so I couldn't get my hands on the exact motor they were using. I settled with a much cheaper, higher Kv and smaller motor which I had to redesign the gearbox for.

| Specification | Value |
|---|---|
| Transmission | Custom 3D-printed cycloidal reducer, **17:1** |
| Manufacturing assumptions | High-resolution print; high wall count; lubrication to mitigate friction |
| Motor | **5010 brushless outrunner, 360 KV** |
| Motor controller | **MKS XDrive Mini**, ODrive copycat field-oriented control |
| Controller working / peak current | **60 A / 120 A** as supplied for the controller; **not motor ratings** |
| conservative operating motor `Iq` limit | **30 A** |
| Battery | **6S LiPo**, 22.2 V nominal / 25.2 V fully charged |
| Gearbox efficiency, design assumption | **85%** |
| Gearbox efficiency, predicted test scenario | **80%** |
| Estimated motor torque constant | **0.02297 N·m/A** (`8.27 / KV`, ODrive current convention) |
| Motor torque at 30 A `Iq` | **0.6891 N·m** (theoretical) |
| Gearbox output at 30 A, ideal 100% | **11.715 N·m** |
| Gearbox output at 30 A, 85% design | **9.95 N·m** (estimated) |
| Gearbox output at 30 A, 80% | **9.37 N·m** |
| Ideal no-load joint speed (22.2 V) | **470 RPM**, approximately **49.2 rad/s** |
| Ideal no-load joint speed (25.2 V) | **534 RPM**, approximately **55.9 rad/s** |
| Verified peak / continuous joint torque | **6.13** |
| Actual efficiency, backlash, weight, stiffness | **52%** explained below|

Here are some explanations regarding the values:
Motor and joint torque calculation
## Motor and joint torque calculation

Using the approximate ODrive motor-current convention:

Kt = 8.27/kv = 8.27/360 = 0.02297 Nm per Amp

so motor torque becomes:
𝜏 = Kt * I
and joint torque:
𝜏 = n*G*kt*I  where n is approx. efficiency, G is reduction ratio

so at the 30A soft limit and at 80% efficiency, torque should be around:
𝜏(motor) = 0.02297(30)(17)(0.80) = 9.95 Nm 

likewise, at 85% would just multiply by 0.85 rather than 0.8
coming out to be around 11.715 Nm

## testing setup(improvised)
Unfortunately I do not have a scale, so I used household items with known masses(roughly) to measure from lever arm. 
the lever arm was 190 mm long and parallel with the floor. other side was clamped down onto table for stability. A plastic bag(assumed weightless) was attached to the end of the arm, and items were placed inside, progressively adding weight.
holding torque went up to 3287 grams. could hold more after but motor started getting really warm, so I decided to put a safe limit here.

torque(holding) = r * F
𝜏max = 0.19m * 3.287 * 9.81 = **6.13 Nm**

I set max torque of actuators in simulator to 7 Nm, so this is around that mark, legs should still function.

## discussion of confounding variables and performance gap
now, to the elephant in the room, why is there such a massive discrepancy in calculated and tested performance? 
compared to actuators on the market, it's actually not bad especially at the $70 price point and fully 3d printed parts. However, the gap between theoretical and actual performance is too large to ignore. There are many reasons for this that I could think of:
1. my biggest suspicion is that the motor isn't actually running at the maximum current. Cheap motors from aliexpress may not be able to actually output with 20+ amps of current and that the motor is probably not running at the current limit, in that case the calculations(at ~12A at 80% efficiency) match very closely with tested values. Next test will involve current graph to test this theory.
2. motor temperature increases winding resistance, reducing available torque when motor starts to work: For example, at 30 A, winding resistive heating is four times the heating at 15 A, assuming the same winding resistance and current convention. usually these drone motors are cooled by airflow, but are stationary here.
3. Position tuning errors; unlikely but may cause slow response, lag, or position droop even when more torque is available.
4. experiment was pretty botched, will retest when I can get a scale. The weights written on my testing weights(yogurt bottle lol) may not be fully accurate
5. lower efficiency than predicted(perhaps closer to 75%), if that's the case may need to adjust printer tolerances and CAD
6. friction may increase when gearbox is under load
7. 3d printed components may flex, introducing backlash and additional friction
8. Voltage drop underload/low charge in battery
9. by luck this test had multiple conditions occuring at once

### The actuator's theoretical torque has not yet been fully experimentally verified, and the present testing method cannot identify the dominant source of the discrepancy. 

Though the current torque should be able to support the weight and walk with the light frame + battery, I would like to get slightly more performance out of the actuators. Here are some improvements I want to make in the future without increasing cost:

1. increase gear reduction in gearbox
2. use different materials/print settings
3. decrease leg length to reduce required torque

