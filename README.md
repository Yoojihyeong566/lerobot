# LeRobot Setup Guide

## 목차
1. [LeRobot 환경 설치](#1-lerobot-환경-설치)
2. [USB 고정 설정](#2-usb-고정-설정)
3. [teleop.py / record.py 실행](#3-teleoppy--recordpy-실행)

---

## 1. LeRobot 환경 설치

### 1-1. Conda 환경 생성

```bash
conda create -y -n lerobot python=3.12
conda activate lerobot
```

### 1-2. ffmpeg 설치

```bash
conda install ffmpeg -c conda-forge
```

### 1-3. LeRobot 설치

로컬 소스에서 설치 (이 repo를 clone한 경우):

```bash
pip install -e .
```

또는 PyPI에서 설치:

```bash
pip install lerobot
```

### 1-4. Feetech 모터 의존성 설치

```bash
pip install -e ".[feetech]"
```

---

## 2. USB 고정 설정

> 자세한 내용은 [LeRobot SO-101 공식 문서](https://huggingface.co/docs/lerobot/so101?example=Linux)를 참고하세요.

매번 USB를 꽂을 때마다 포트 번호(`/dev/ttyACM0`, `/dev/ttyACM1` 등)가 바뀔 수 있습니다.
udev 규칙을 등록하면 장치마다 고정된 심볼릭 링크(예: `/dev/lerobot/left_leader`)를 사용할 수 있습니다.

### 2-1. 각 팔의 포트 확인

MotorBus를 USB로 연결한 뒤 아래 명령어를 실행합니다.
프롬프트가 뜨면 해당 팔의 USB 케이블을 분리하고 Enter를 누릅니다.

```bash
# Linux에서 포트 접근 권한 오류가 나는 경우
sudo chmod 666 /dev/ttyACM0
sudo chmod 666 /dev/ttyACM1
```

```bash
lerobot-find-port
```

실행 예시:

```
Finding all available ports for the MotorBus.
['/dev/ttyACM0', '/dev/ttyACM1']
Remove the usb cable from your MotorsBus and press Enter when done.

[...Disconnect corresponding leader or follower arm and press Enter...]

The port of this MotorsBus is /dev/ttyACM1
Reconnect the USB cable.
```

각 팔(left_leader, left_follower, right_leader, right_follower)에 대해 반복하여 포트를 확인합니다.

### 2-2. udev 규칙 적용

포트를 모두 확인한 뒤 `99-lerobot.rules` 파일에 각 장치의 serial 번호를 기록하고 아래 명령어로 규칙을 등록합니다.

```bash
sudo cp 99-lerobot.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

등록 후에는 USB를 다시 꽂아도 아래와 같은 고정 경로로 접근할 수 있습니다.

| 장치 | 심볼릭 링크 |
|------|------------|
| Left Leader  | `/dev/lerobot/left_leader`   |
| Left Follower | `/dev/lerobot/left_follower` |
| Right Leader | `/dev/lerobot/right_leader`  |
| Right Follower | `/dev/lerobot/right_follower` |
| Left Wrist Camera | `/dev/lerobot/cam_left_wrist` |
| Right Wrist Camera | `/dev/lerobot/cam_right_wrist` |
| Right Top Camera | `/dev/lerobot/cam_right_top` |

---

## 3. teleop.py / record.py 실행

### 3-1. teleop.py — 원격 조작 (녹화 없음)

양팔(Bimanual) SO-101을 원격 조작하는 스크립트입니다. 데이터 녹화 없이 로봇을 움직여볼 때 사용합니다.

```bash
# 기본 실행 (30fps, 무제한)
python teleop.py

# fps와 실행 시간 지정
python teleop.py --fps 30 --duration 120
```

| 인자 | 기본값 | 설명 |
|------|--------|------|
| `--fps` | `30` | 제어 주기 |
| `--duration` | `None` (무제한) | 실행 시간 (초) |

종료하려면 `Ctrl+C`를 누릅니다.

---

### 3-2. record.py — 데이터 녹화

원격 조작하면서 데이터셋을 녹화하는 스크립트입니다.

```bash
# 기본 실행
python record.py

# 옵션 지정
python record.py --dataset local/my_dataset --task "Pick up cube" --episodes 20
```

| 인자 | 기본값 | 설명 |
|------|--------|------|
| `--dataset` | `local/bimanual_so101_demo` | 저장할 데이터셋 이름 |
| `--task` | `Pick and place task` | 태스크 설명 |
| `--episodes` | `20` | 녹화할 에피소드 수 |
| `--episode_s` | `60` | 에피소드당 녹화 시간 (초) |
| `--reset_s` | `30` | 에피소드 사이 리셋 시간 (초) |
| `--fps` | `30` | 제어 주기 |
| `--root` | `~/.cache/huggingface/lerobot/` | 데이터셋 저장 경로 |
| `--no_display` | `False` | Rerun 시각화 비활성화 |

녹화 중 키보드 단축키:

| 키 | 동작 |
|----|------|
| `Space` | 에피소드 조기 종료 |
| `r` | 현재 에피소드 다시 녹화 |
| `q` | 전체 녹화 종료 |

---
