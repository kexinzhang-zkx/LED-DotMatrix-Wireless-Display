# LED-DotMatrix-Wireless-Display
Design and Implementation of a 16×16 LED Dot-Matrix Hourglass Display System for IoT Practice

---

## Project Overview
This project is a practical IoT hardware development task: the design and implementation of a **16×16 full-color LED dot-matrix hourglass display device**. It integrates hardware soldering, PCB design, embedded programming, and wireless control based on ESP32, and realizes a dynamic hourglass animation with a 15-second countdown function.

The system uses **four 8×8 WS2812B LED panels** soldered into a 16×16 matrix, driven by the **ESP32-WROOM-32** microcontroller. The software is developed in **MicroPython**, using serpentine pixel mapping, physical sand-falling simulation, and mirrored 4×6 digit display to achieve a complete visual effect.

This project is completed for the course assessment report:
**Comprehensive Practice of IoT Hardware Basics**

---

## Key Features
- 16×16 full-color WS2812B LED matrix display
- Serpentine scanning algorithm to correct pixel misalignment
- Simulated physical hourglass animation (random falling + gravity stacking)
- 15-second cycle countdown with mirrored 4×6 digits
- Blue outline (0,0,255) and yellow sand (255,255,0)
- WiFi wireless control via web page (Start / Pause / Reset)
- Stable power supply design using SCT9336STER
- Automatic operation on power-up

---

## Hardware Design
### Main Components
| Component | Model | Function |
|-----------|-------|----------|
| Main Controller | ESP32-WROOM-32D | WiFi communication and LED control |
| LED Display | WS2812B 16×16 Matrix | Full-color dynamic display |
| Power IC | SCT9336STER | Step-down regulated power supply |
| Driver Interface | GPIO18 | NeoPixel data output |

### Hardware Structure
- 4× 8×8 LED panels soldered into a 2×2 16×16 matrix
- Single-wire cascade connection
- Custom PCB power module layout
- Stable 5V power supply circuit

### Hardware Files
- Schematic diagram: `/hardware/schematic.png`
- PCB layout: `/hardware/pcb_layout.png`

---

## Software Design
### Development Environment
- Language: MicroPython
- IDE: Thonny
- Driver: NeoPixel library
- Core: Machine, Time, Random, Network, Socket

### Software Modules
1. **Hardware Interface Layer**: Drives GPIO18 to control WS2812B
2. **Display Control Layer**:
   - Serpentine pixel mapping algorithm
   - Hourglass outline generation
   - Sand physical simulation
   - 4×6 mirrored digit display
3. **Logic Control Layer**: 15-second countdown loop
4. **Wireless Control Layer**: WiFi AP + web control server

---

## System Structure
```text
LED-DotMatrix-Wireless-Display/
├── README.md          # Project description
├── main.py            # Main program (MicroPython)
└── hardware/
    ├── schematic.png  # Schematic
    └── pcb_layout.png # PCB layout
```

---

## Wiring Instructions
| LED Matrix Pin | ESP32 Pin |
|----------------|-----------|
| DIN | GPIO18 |
| VCC | 5V |
| GND | GND |

---

## Wireless Control
1. The ESP32 automatically creates a WiFi hotspot:  
   **ESP32_Hourglass** / Password: **12345678**
2. Open a browser and visit: **192.168.4.1**
3. Control functions:
   - Start
   - Pause
   - Reset

---

## System Test Results
- All 256 pixels light up normally
- Hourglass outline is symmetrical and stable
- Sand animation is smooth and synchronized
- Countdown error < 0.1s
- Mirrored digits display correctly
- Wireless control responds in real time

---

## Conclusion
This project realizes a complete LED dot-matrix hourglass display system, including hardware soldering, PCB design, embedded programming, and wireless control. It fully reflects the modular design idea of IoT hardware and has high practical and demonstration value for IoT engineering practice.

---

## License
For educational and course assessment use only.
