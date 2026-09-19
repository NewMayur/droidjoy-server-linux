#!/bin/bash
echo 'KERNEL=="uinput", SUBSYSTEM=="misc", MODE="0666", OPTIONS+="static_node=uinput"' | tee /etc/udev/rules.d/99-uinput.rules
echo "uinput" | tee /etc/modules-load.d/uinput.conf
modprobe uinput
udevadm control --reload-rules && udevadm trigger
