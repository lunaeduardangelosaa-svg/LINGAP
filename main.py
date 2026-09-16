from system_handler import SystemHandler

# ============================================================
# START LINGAP
# ============================================================

system = SystemHandler()

system.run()

# ls /dev/ttyAMA* && dmesg | grep -i uart
# espeak -v en-us+f3 -s 150 "your text"
# http://127.0.0.1:5000
