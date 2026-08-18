# Low-Cost Bipedal Robot via Reinforcement Learning

A personal passion project focused on achieving robust bipedal locomotion using highly accessible, 3D-printed hardware, and machine learning control.

## Overview

This project aims to bridge the **Sim-to-Real** gap for low-cost, hobby-grade bipedal robotics. While high-end humanoid robots rely on multi-thousand-dollar custom actuators, this design explores how advanced **Reinforcement Learning (RL)** policies can compensate for physical hardware limitations.

---

## Current Project Status

- [x] **CAD & Structural Design:** Initial physical architecture conceptualized and modeled. <img width="840" height="909" alt="image" src="https://github.com/user-attachments/assets/4043266d-dc18-4a8b-8178-2b396c2104e4" />

- [x] **Hardware Prototyping:** Fabricated and assembled a single-leg testbed to validate software integration, joint range of motion, and motor actuation. Second leg to be fabricated after I receive the funds(hopefully)
- [/] **Simulation Environment Setup:** Porting robot kinematics to **Genesis World**. Simplified model for training: <img width="836" height="730" alt="image" src="https://github.com/user-attachments/assets/25bf723f-2106-4d4b-bbe1-65f3a2082b34" />

  - *In Progress:* Fixing URDF joint limits, collision meshes, and inertia tensors to eliminate mesh explosions during physics step iterations.
- [ ] **RL Policy Training:** Training locomotion policies in simulation using domain randomization.
- [ ] **Sim-to-Real Deployment:** Flashing trained policy weights to hardware for real-world locomotion tests.

## System Architecture

### Hardware Specifications
* **Actuators:** custom BLDC actuators utilizing a high reduction cycloidal drive in order to gear down a cheap drone 360kv BLDC motor from Aliexpress. Each actuator uses odrive mini motor controller clones also from aliexpress.
* **Microcontroller / Brain:** ESP32, depending on how software training goes I may switch to ESP 32 CAM so the robot can see. talks to motors through a CAN wire going to all motor controllers
* **Power Delivery:** 6s 2200 mAH LiPo battery
* **Sensors:** 
  * Inertial Measurement Sensor(IMU) MPU 9250
  * Built in magnetic encoders on motor controllers 

### Software & Training Stack
* **CAD Design:** [Onshape]https://cad.onshape.com/documents/8bf57c6be62972ed6d80fc07/w/9d44f84c666fceecad986cd8/e/5c78cbb988f68fd2f32a2769
* **Simulation Engine:** [Genesis World Sim](https://github.com/Genesis-Embodied-AI/genesis-world)
* **Robot Description:** Custom URDF model using Onshape to URDF tool

## Design Constraints & Engineering Goals

* **Affordable Bill of Materials (BOM):** Target total cost **under $1,200**, utilizing readily available consumer components sourced via Amazon and AliExpress.
* **Accessiblity:** Fully 3D-printable structural components optimized for cheap materials(PC PETG blend) without requiring specialized CNC aluminum parts.
* **"Blind" Locomotion:** Rely exclusively on IMU body orientation and joint state feedback to maintain balance.
* **Dynamic Movement:** Develop policy reward functions capable of transitioning the robot through walking, running, and jumping states while preserving balance.

