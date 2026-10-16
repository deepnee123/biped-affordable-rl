# Low-Cost Bipedal Robot via Reinforcement Learning, Raptor08

A personal passion project focused on achieving robust bipedal locomotion using highly accessible, 3D-printed hardware, and machine learning control.

## Overview

This project aims to bridge the **Sim-to-Real** gap for low-cost, hobby-grade bipedal robotics. While high-end humanoid robots rely on multi-thousand-dollar custom actuators, this design explores how advanced **Reinforcement Learning (RL)** policies can compensate for physical hardware limitations. Uses digitigrade locomotion(fun fact: animals like ostriches don't actually have inverted knees, it's their ankle). 

---

## Current Project Status

- [x] **CAD & Structural Design:** Initial physical architecture conceptualized and modeled. <img width="840" height="909" alt="image" src="https://github.com/user-attachments/assets/4043266d-dc18-4a8b-8178-2b396c2104e4" />

- [x] **Hardware Prototyping:** Fabricated and assembled a single-leg testbed to validate software integration, joint range of motion, and motor actuation. Second leg to be fabricated after I receive the funds(hopefully)
- [x] **Simulation Environment Setup:** Porting robot kinematics to **Genesis World**. Simplified model for training: <img width="836" height="730" alt="image" src="https://github.com/user-attachments/assets/25bf723f-2106-4d4b-bbe1-65f3a2082b34" />

  - ~~*In Progress:* Fixing URDF joint limits, collision meshes, and inertia tensors to eliminate mesh explosions during physics step iterations.~~
  - ~~*In Progress:* URDF was too hard to deal with so switched over to MJCF successfully, now loads in MuJoCo visualizer perfectly. adjusted all parameters for motors, friction, weight etc for accuracy~~
<img width="2292" height="996" alt="Screenshot from 2026-09-06 18-59-11" src="https://github.com/user-attachments/assets/f0a52dac-c5fc-4d15-9eb6-18477723a25c" />

- [/] **RL Policy Training:** Training locomotion policies in simulation using domain randomization.
  - currently training all movesets, planning on deploying into robot after I am able to fund and finish the hardware build.
  - implementing domain randomization such as variable COM and actuator friction
  - working on training model for unpredictable terrain
- [ ] **Sim-to-Real Deployment:** Flashing trained policy weights to hardware for real-world locomotion tests. What I want to add: since I will be offloading the neural network to run on my computer, I will communicate wirelessly with the esp32 onboard. This will introduce some lag so I will account for this using domain randomization:
During training, randomly vary the action delay for each environment between 0 and 2 time steps (e.g., 0 ms to 20 ms at a 100 Hz control loop). The resulting policy will be robust to fluctuating Wi-Fi packet delivery times.
Pass historical observations (e.g., joint states and IMU readings from the last 2–3 time steps) into your observation vector. This gives the neural network temporal context, allowing it to implicitly estimate the state velocity and adapt to input lag.
To better match a real Wi-Fi/Serial link, convert this to an explicit n-step action history buffer. Instead of applying the current action instantly, store actions in a queue and apply the action from 1 or 2 control steps ago

some early tensor graphs:

these ones show that the robot makes some initial progress but finds a way to "reward hack", mainly due to poorly balanced reward functions, and faulty robot structure, robot effectively stops learning and resorts to "face planting" to avoid further penalties. 
Mean episode length(time stayed standing) didn't increase while mean reward increased:
<img width="1999" height="794" alt="image6" src="https://github.com/user-attachments/assets/7a3480ac-f786-4137-806b-a90753c6e6f4" />
<img width="1522" height="480" alt="image5" src="https://github.com/user-attachments/assets/915c712b-a59a-433a-9692-ab9fdc863e31" />

Recent graphs:
training goes much better after reconfiguring simulation and the MJCF file, turns out the simulation thought the right foot was the base of the robot which made for incorrect rewards, encouraging "faceplanting" behavior
<img width="1999" height="811" alt="image2" src="https://github.com/user-attachments/assets/f2dc384e-2bce-485e-ae1d-803a3a6b1503" />


please check these out! 
current training progress videos here!:

[here:](https://www.youtube.com/watch?v=r23alA2GN7E)
[randomized vector commands for full moveset here](https://www.youtube.com/watch?v=8FQqMWRTSfI)

## System Architecture

Hardware schematic:
<img width="3508" height="2480" alt="image" src="https://github.com/user-attachments/assets/c05b1425-4499-4b77-ab22-b231c4601df1" />

### Hardware Specifications
* **Actuators:** custom BLDC actuators utilizing a high reduction 17:1 cycloidal drive in order to gear down a cheap drone 360kv BLDC motor from Aliexpress. Each actuator uses odrive mini motor controller clones also from aliexpress. Each motor controller uses Odrive 3.6 firmware uploaded using Odrive tool. [Click here for great motor controller setup tutorial](https://github.com/justlovescience/MKS-XDRIVE-MINI), make sure to setup in accordance to the motor you are using. In the future I may consider creating custom pcb's for motor controls, hopefully decreasing cost even more, but that is a project in it of itself.
* **Microcontroller / Brain:** ESP32, depending on how software training goes I may switch to ESP 32 CAM so the robot can see. talks to motors through a CAN wire going to all motor controllers. No custom PCBs
* **Power Delivery:** 6s 2200 mAH LiPo battery
* **Sensors:** 
  * Inertial Measurement Sensor(IMU) MPU 9250
  * Built in magnetic encoders on motor controllers 

### Software & Training Stack
* **CAD Design:** [Onshape]https://cad.onshape.com/documents/8bf57c6be62972ed6d80fc07/w/9d44f84c666fceecad986cd8/e/5c78cbb988f68fd2f32a2769
* **Simulation Engine:** [Genesis World Sim](https://github.com/Genesis-Embodied-AI/genesis-world)
* **Robot Description:** ~~Custom URDF model using Onshape to URDF tool~~ changed to using MJCF file since it supports parallel linkages without hassle and is also supported by Genesis world.

## Design Constraints & Engineering Goals

* **Affordable Bill of Materials (BOM):** Target total cost **under $1,200**, utilizing readily available consumer components sourced via Amazon and AliExpress.
* **Accessiblity:** Fully 3D-printable structural components optimized for cheap materials(PC PETG blend) without requiring specialized CNC aluminum parts.
* **"Blind" Locomotion:** Rely exclusively on IMU body orientation and joint state feedback to maintain balance.
* **Dynamic Movement:** Develop policy reward functions capable of transitioning the robot through walking, running, and jumping states while preserving balance.

