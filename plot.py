import pandas as pd
import matplotlib.pyplot as plt
import os

# Load CSV file
motion_data = pd.read_csv("motion_data.csv", skiprows=5)

# Separate by sensor type
acc_data = motion_data[motion_data["TYPE"] == "ACC"]
gyro_data = motion_data[motion_data["TYPE"] == "GYRO"]
mag_data = motion_data[motion_data["TYPE"] == "MAG"]
motion_compass = motion_data[motion_data["TYPE"] == "MOTION"]

# Create figure
plt.figure(figsize=(24, 8.5))

# Accelerometer
plt.subplot(4, 1, 1)
plt.plot(acc_data["TIMESTAMP"], acc_data["X"], label="X")
plt.plot(acc_data["TIMESTAMP"], acc_data["Y"], label="Y")
plt.plot(acc_data["TIMESTAMP"], acc_data["Z"], label="Z")
plt.title("Accelerometer (ACC)")
plt.xlabel("Timestamp")
plt.ylabel("Acceleration")
plt.legend()

# Gyroscope
plt.subplot(4, 1, 2)
plt.plot(gyro_data["TIMESTAMP"], gyro_data["X"], label="X")
plt.plot(gyro_data["TIMESTAMP"], gyro_data["Y"], label="Y")
plt.plot(gyro_data["TIMESTAMP"], gyro_data["Z"], label="Z")
plt.title("Gyroscope (GYRO)")
plt.xlabel("Timestamp")
plt.ylabel("Angular Velocity")
plt.legend()

# Magnetometer
plt.subplot(4, 1, 3)
plt.plot(mag_data["TIMESTAMP"], mag_data["X"], label="X")
plt.plot(mag_data["TIMESTAMP"], mag_data["Y"], label="Y")
plt.plot(mag_data["TIMESTAMP"], mag_data["Z"], label="Z")
plt.title("Magnetometer (MAG)")
plt.xlabel("Timestamp")
plt.ylabel("Magnetic Field")
plt.legend()

# Motion/Compass (MOTION)
plt.subplot(4, 1, 4)
if not motion_compass.empty:
    if "HEADING" in motion_compass.columns:
        plt.plot(motion_compass["TIMESTAMP"], motion_compass["HEADING"], label="Heading")
        plt.ylabel("Heading")
        plt.legend()
    else:
        plt.plot(motion_compass["TIMESTAMP"], motion_compass["X"], label="X")
        plt.plot(motion_compass["TIMESTAMP"], motion_compass["Y"], label="Y")
        plt.plot(motion_compass["TIMESTAMP"], motion_compass["Z"], label="Z")
        plt.ylabel("Compass")
        plt.legend()
    plt.title("Motion/Compass (MOTION)")
    plt.xlabel("Timestamp")
else:
    plt.title("Motion/Compass (MOTION) - no data")
    plt.xlabel("Timestamp")

# Adjust layout
plt.tight_layout()

# Save figure
os.makedirs("figures", exist_ok=True)
plt.savefig("figures/motion_plot.svg", bbox_inches="tight")

plt.show()
