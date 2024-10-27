# Project car-ogna
### Amberlab - 2024

This project involves creating a Raspberry Pi-controlled RC car, built for First-Person View (FPV) driving. The car is controlled through a web browser, using either the arrow keys on your PC keyboard or (coming soon) a joystick for enhanced control. 
<img src="PXL_20241018_162341279.jpg" width="600"/>

### Electronics and Hardware

The main components include a Raspberry Pi Zero 2 for central control, paired with a brushless motor A2212 and Electronic Speed Controller (ESC) to serve as the car’s engine, and a micro servo motor for steering.

### FPV Vision

For FPV vision, the car is equipped with a Raspberry Pi camera and a USB WiFi adapter (using the Tenda U2, though any compatible adapter can work) or the Pi’s built-in WiFi. 

### Chassis
The car’s chassis is based on the <a href="https://www.thingiverse.com/thing:4233353">Carduino V2</a> with minor adjustments and includes a modified case <a href="https://www.thingiverse.com/thing:1639568"> Pi Zero camera housing</a>, and <a href="https://makerworld.com/it/models/212433?from=search">custom wheels</a>. Everything can be 99% 3D printed, as the only non printed components are M3 screws and four bearrings.

### Power System

Power is provided by 2S Li-ion batteries** with a USB-C charging port built into the car for easy recharging, and a Battery Elimination Circuit (BEC) regulates power for the Raspberry Pi. The car also features bright LED headlights at the front and a red LED at the back for visibility.
