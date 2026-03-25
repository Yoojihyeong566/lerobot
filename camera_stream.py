#!/usr/bin/env python3
"""
Camera streaming GUI — 3 cameras with FPS overlay.
Usage:
  python camera_stream.py
"""

import time
import cv2
import matplotlib.pyplot as plt
import matplotlib.animation as animation

CAMERAS = {
    "left_wrist": "/dev/lerobot/cam_left_wrist",
    "right_wrist": "/dev/lerobot/cam_right_wrist",
    "right_top": "/dev/lerobot/cam_right_top",
}


def open_camera(device: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(device)
    if not cap.isOpened():
        raise RuntimeError(f"{device} 열기 실패")
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap


def main():
    caps = {}
    for name, dev in CAMERAS.items():
        try:
            caps[name] = open_camera(dev)
            print(f"Connected: {name} ({dev})")
        except RuntimeError as e:
            print(f"SKIP: {e}")

    if not caps:
        print("사용 가능한 카메라 없음")
        return

    names = list(caps.keys())
    fig, axes = plt.subplots(1, len(names), figsize=(6 * len(names), 5))
    if len(names) == 1:
        axes = [axes]

    fig.canvas.manager.set_window_title("Camera Stream")

    img_plots = {}
    fps_texts = {}
    prev_times = {}

    for ax, name in zip(axes, names):
        ret, frame = caps[name].read()
        if not ret:
            frame = cv2.cvtColor(192 * __import__("numpy").ones((480, 640, 3), dtype="uint8"), cv2.COLOR_BGR2RGB)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_plots[name] = ax.imshow(frame)
        ax.axis("off")
        ax.set_title(name)
        fps_texts[name] = ax.text(
            10, 30, "FPS: --", fontsize=14, color="lime",
            fontweight="bold", transform=ax.transData,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.6),
        )
        prev_times[name] = time.monotonic()

    def update(_):
        artists = []
        for name in names:
            ret, frame = caps[name].read()
            now = time.monotonic()
            dt = now - prev_times[name]
            fps = 1.0 / dt if dt > 0 else 0
            prev_times[name] = now

            if ret:
                img_plots[name].set_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            fps_texts[name].set_text(f"FPS: {fps:.1f}")
            artists.append(img_plots[name])
            artists.append(fps_texts[name])
        return artists

    ani = animation.FuncAnimation(fig, update, interval=33, blit=True, cache_frame_data=False)

    plt.tight_layout()
    print("Streaming — 창 닫기로 종료")
    plt.show()

    for cap in caps.values():
        cap.release()


if __name__ == "__main__":
    main()
