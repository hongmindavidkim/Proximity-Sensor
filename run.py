import serial
import time
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=500000,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

plt.ion()
fig = plt.figure(figsize=(14, 8))
gs = gridspec.GridSpec(3, 2, width_ratios=[3, 1])

ax0 = plt.subplot(gs[0, 0])
ax1 = plt.subplot(gs[1, 0])
ax2 = plt.subplot(gs[2, 0])
ax3 = plt.subplot(gs[:, 1])

ax = [ax0, ax1, ax2, ax3]

fig.canvas.draw()
backgrounds = [fig.canvas.copy_from_bbox(a.bbox) for a in ax]

window_size = 200
distance_data = np.zeros(window_size)
yaw_angle_data = np.zeros(window_size)
pitch_angle_data = np.zeros(window_size)

distance_cutoff = [0, 20.5]
yaw_cutoff = [-30, 30]
pitch_cutoff = [-30, 30]

dist_offset = 0  
yaw_offset = 0
pitch_offset = 0

text1 = ax[0].text(0.7, 0.85, '', transform=ax[0].transAxes)
text2 = ax[1].text(0.7, 0.85, '', transform=ax[1].transAxes)
text3 = ax[2].text(0.7, 0.85, '', transform=ax[2].transAxes)

x_data = np.arange(window_size)
line1, = ax[0].plot(x_data, distance_data)
line2, = ax[1].plot(x_data, yaw_angle_data, color='g')
line3, = ax[2].plot(x_data, pitch_angle_data, color='r')

raw_sensor_data = np.zeros(8)
bar_width = 0.5
bar_positions = np.arange(len(raw_sensor_data))
bars = ax[3].bar(bar_positions, raw_sensor_data, width=bar_width)

ax[3].set_ylim(0, 255)  
ax[3].set_xticks(bar_positions)
ax[3].set_xticklabels([f"S{i}" for i in range(len(raw_sensor_data))])

for a in ax[:-1]:
    a.set_xlim(0, window_size)
ax[0].set_ylim(-1, 20 * 1.2)
ax[1].set_ylim(-20 * 1.2, 20 * 1.2)
ax[2].set_ylim(-20 * 1.2, 20 * 1.2)

if ser.isOpen():
    print(f"Serial port {ser.port} is open.")
else:
    print(f"Failed to open serial port {ser.port}.")
    exit()

time_interval = 1 / 200.0

try:
    while True:
        start_time = time.perf_counter()

        hex_message = bytes([0x52, 0x01, 0x00, 0x53])
        ser.write(hex_message)
        received_data = ser.read(14)

        distance_byte = received_data[2]
        yaw_angle_byte = received_data[3]
        pitch_angle_byte = received_data[4]
        distance = distance_byte / 10.0 + dist_offset
        yaw_angle = yaw_angle_byte / 2 - 40.0 + yaw_offset
        pitch_angle = pitch_angle_byte / 2 - 40.0 +pitch_offset

        distance_data = np.roll(distance_data, -1)
        distance_data[-1] = distance if distance_cutoff[0] <= distance <= distance_cutoff[1] else 0
        yaw_angle_data = np.roll(yaw_angle_data, -1)
        yaw_angle_data[-1] = yaw_angle if yaw_cutoff[0] <= yaw_angle <= yaw_cutoff[1] else 0
        pitch_angle_data = np.roll(pitch_angle_data, -1)
        pitch_angle_data[-1] = pitch_angle if pitch_cutoff[0] <= pitch_angle <= pitch_cutoff[1] else 0
        
        line1.set_ydata(distance_data)
        line2.set_ydata(yaw_angle_data)
        line3.set_ydata(pitch_angle_data)

        text1.set_text(f"Distance: {distance:.2f}")
        text2.set_text(f"Yaw Angle: {yaw_angle:.2f}")
        text3.set_text(f"Pitch Angle: {pitch_angle:.2f}")

        raw_sensor_data = np.array([int(b) for b in received_data[5:13]])

        for bar, height in zip(bars, raw_sensor_data):
            bar.set_height(height)

        for a, background in zip(ax, backgrounds):
            fig.canvas.restore_region(background)
            a.draw_artist(a.patch)
            for artist in a.lines + a.patches + a.texts:
                a.draw_artist(artist)

        fig.canvas.blit(fig.bbox)
        fig.canvas.flush_events()

        elapsed_time = time.perf_counter() - start_time
        if elapsed_time < time_interval:
            time.sleep(time_interval - elapsed_time)

except KeyboardInterrupt:
    ser.close()
    print("Serial port closed.")
    plt.ioff()
    plt.show()
