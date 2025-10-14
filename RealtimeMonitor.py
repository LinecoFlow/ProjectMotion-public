import flask
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from threading import Thread, Lock
from collections import deque

# Config
MAX_POINTS = 2000
WINDOW_SECONDS = 15.0  # seconds

# Per-sensor Y limits (tweak as needed)
Y_LIMS = {
    "ACC": (-4.0, 4.0),       # g
    "GYRO": (-50.0, 50.0),# deg/s
    "MAG": (-200.0, 200.0),   # uT
    "MOTION": (-2.0, 2.0),    # g or normalized
}

SENSOR_TYPES = ["ACC", "GYRO", "MAG", "MOTION"]

# Data buffers
sensor_data = {
    s: {
        "t": deque(maxlen=MAX_POINTS),
        "X": deque(maxlen=MAX_POINTS),
        "Y": deque(maxlen=MAX_POINTS),
        "Z": deque(maxlen=MAX_POINTS),
    }
    for s in SENSOR_TYPES
}
data_lock = Lock()
origin_ts = None
last_ts = {s: None for s in SENSOR_TYPES}

app = flask.Flask(__name__)

@app.route('/api', methods=['POST'])
def receive_motion_data():
    global origin_ts, last_ts
    data = flask.request.get_json(silent=True) or {}

    if data.get("event") == "data":
        sensor_type = data.get("type")
        ts = data.get("timestamp")
        vals = data.get("values") or []

        if sensor_type in SENSOR_TYPES:
            if ts is None or len(vals) < 3:
                return {"status": f"bad {sensor_type} payload"}, 200
            if origin_ts is None:
                origin_ts = ts
            # Keep time monotonic per sensor
            if last_ts[sensor_type] is not None and ts < last_ts[sensor_type]:
                return {"status": f"skipped out-of-order {sensor_type}"}, 200

            rel_t = ts - origin_ts
            with data_lock:
                sensor_data[sensor_type]["t"].append(rel_t)
                sensor_data[sensor_type]["X"].append(vals[0])
                sensor_data[sensor_type]["Y"].append(vals[1])
                sensor_data[sensor_type]["Z"].append(vals[2])
            last_ts[sensor_type] = ts
        else:
            # Unknown sensor type; ignore
            pass

    elif data.get("event") == "start":
        with data_lock:
            for s in SENSOR_TYPES:
                sensor_data[s]["t"].clear()
                sensor_data[s]["X"].clear()
                sensor_data[s]["Y"].clear()
                sensor_data[s]["Z"].clear()
        origin_ts = None
        last_ts = {s: None for s in SENSOR_TYPES}

    return {"status": "success"}, 200

# Matplotlib setup: one subplot per sensor type
sensor_titles = {
    "ACC": "Realtime Accelerometer (ACC)",
    "GYRO": "Realtime Gyroscope (GYRO)",
    "MAG": "Realtime Magnetometer (MAG)",
    "MOTION": "Realtime Motion (MOTION)",
}

fig, axes = plt.subplots(len(SENSOR_TYPES), 1, sharex=True, figsize=(12, 9))
if len(SENSOR_TYPES) == 1:
    axes = [axes]

# Create lines per sensor
sensor_lines = {}
for ax, s in zip(axes, SENSOR_TYPES):
    (lx,) = ax.plot([], [], label="X")
    (ly,) = ax.plot([], [], label="Y")
    (lz,) = ax.plot([], [], label="Z")
    ax.set_ylabel(s)
    ax.set_title(sensor_titles.get(s, s))
    ax.set_ylim(*Y_LIMS.get(s, (-1.0, 1.0)))
    ax.legend(loc="upper right")
    sensor_lines[s] = (lx, ly, lz)

axes[-1].set_xlabel("Seconds")

def animate(_):
    # Snapshot data
    with data_lock:
        snap = {
            s: (
                list(sensor_data[s]["t"]),
                list(sensor_data[s]["X"]),
                list(sensor_data[s]["Y"]),
                list(sensor_data[s]["Z"]),
            )
            for s in SENSOR_TYPES
        }

    # Update each subplot
    for ax, s in zip(axes, SENSOR_TYPES):
        t, x, y, z = snap[s]
        if not t:
            # No data yet; leave lines empty
            sensor_lines[s][0].set_data([], [])
            sensor_lines[s][1].set_data([], [])
            sensor_lines[s][2].set_data([], [])
            continue

        tmax = t[-1]
        tmin = max(0.0, tmax - WINDOW_SECONDS)

        # find first index within window
        i0 = 0
        for i in range(len(t) - 1, -1, -1):
            if t[i] < tmin:
                i0 = i + 1
                break

        tv = t[i0:]
        sensor_lines[s][0].set_data(tv, x[i0:])
        sensor_lines[s][1].set_data(tv, y[i0:])
        sensor_lines[s][2].set_data(tv, z[i0:])
        ax.set_xlim(tmin, max(tmin + 1.0, tmax))  # keep width positive

if __name__ == '__main__':
    ani = animation.FuncAnimation(fig, animate, interval=100)
    server = Thread(
        target=lambda: app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False),
        daemon=True
    )
    server.start()
    plt.show()
