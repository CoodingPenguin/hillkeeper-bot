# 🐮 hillkeeper-bot

비빌언덕 주간 회고 모임을 위한 Discord 봇입니다.

## 기능

### 📋 출석 체크 (목요일 오전 9시)
- `@회고` 역할 멘션과 함께 출석 체크 메시지 전송
- ✅/❌ 이모지 반응으로 참여 여부 확인
- 음성 채널 링크 포함

### 🔔 회고 리마인더 (목요일 밤 9시 45분)
- 출석 체크한 참여자들에게만 멘션
- 15분 후 시작 안내
- 음성 채널로 바로 이동 가능

### 💾 데이터 저장
- Redis를 활용한 7일간 출석 기록 보관
- 자동 만료 처리 (TTL 기반)

## 기술 스택

- **Python 3.13+**
- **discord.py** - Discord API 라이브러리
- **Redis** - 데이터 저장소 (Render Key-Value Store)
- **Poetry** - 의존성 관리
- **Render** - 배포 플랫폼

## 환경 변수 설정

`.env` 파일에 다음 변수들을 설정하세요:

```bash
# Discord
DISCORD_TOKEN=your_discord_bot_token

# 채널 & 역할 ID
ATTENDANCE_CHANNEL_ID=your_channel_id
RETROSPECTIVE_ROLE_ID=your_role_id
VOICE_CHANNEL_ID=your_voice_channel_id

# Redis (Render Key-Value Store)
REDIS_URL=redis://default:password@host:port

# 테스트
TEST_CHANNEL_ID=test_channel_id
TEST_ROLE_ID=test_role_id
```

## 로컬 개발

### 1. 저장소 클론
```bash
git clone https://github.com/CoodingPenguin/hillkeeper-bot.git
cd hillkeeper-bot
```

### 2. Poetry 설치 및 의존성 설치
```bash
poetry install
```

### 3. 환경 변수 설정
`.env` 파일을 생성하고 위의 환경 변수들을 설정합니다.

### 4. 봇 실행
```bash
poetry run python main.py
```

## 테스트 명령어

봇이 실행되면 다음 슬래시 명령어로 테스트할 수 있습니다:

- `/ping` - 봇 응답 속도 확인
- `/test_morning_check` - 출석 체크 메시지 테스트
- `/test_evening_reminder` - 리마인더 메시지 테스트

## 프로젝트 구조

```
hillkeeper-bot/
├── main.py                      # 엔트리 포인트
├── hillkeeper/
│   ├── config.py               # 설정 및 상수
│   ├── messages.py             # 메시지 템플릿 (Embed)
│   ├── utils.py                # Discord 유틸리티
│   ├── attendance/             # 출석 도메인
│   │   ├── repository.py      # 데이터 접근 (Redis)
│   │   └── service.py         # 비즈니스 로직
│   ├── database/               # 인프라스트럭처
│   │   └── redis.py           # Redis 클라이언트
│   └── bot/                    # Discord 인터페이스
│       ├── commands.py        # 슬래시 명령어
│       ├── events.py          # 이벤트 핸들러
│       └── tasks.py           # 스케줄 작업
├── pyproject.toml
└── poetry.lock
```

## 배포 (Render)

### Redis 설정
1. Render 대시보드에서 Key-Value Store 생성
2. **로컬 개발**: External URL + Valkey Ingress Rules에 `0.0.0.0/0` 추가
3. **배포**: Internal URL 사용 (IP 제한 불필요)

### 봇 배포
1. Render에서 새 Web Service 생성
2. GitHub 저장소 연결
3. 환경 변수 설정
4. 자동 배포 시작