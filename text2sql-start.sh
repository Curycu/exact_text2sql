#!/bin/bash

# 이 스크립트 파일이 있는 디렉토리를 기준으로 경로를 설정합니다.
# realpath나 `cd ... && pwd`를 사용하여 절대 경로를 얻습니다.
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
UI_FILE="$SCRIPT_DIR/text2sql-ui/index.html"

# API 디렉토리로 이동합니다.
cd "$SCRIPT_DIR/text2sql-api"

echo "8000번 포트에서 실행 중인 기존 프로세스를 확인하고 종료합니다..."
PID=$(lsof -t -i:8000)
if [ -n "$PID" ]; then
  echo "기존 프로세스(PID: $PID)를 종료합니다."
  kill -9 "$PID"
  sleep 1 # 포트가 해제될 때까지 잠시 대기
else
  echo "기존에 실행 중인 프로세스가 없습니다."
fi

# 가상 환경 내의 python 실행 파일을 직접 지정합니다.
VENV_PYTHON="venv/bin/python"

echo "FastAPI 서버를 백그라운드에서 시작합니다 (http://0.0.0.0:8000)..."
# uvicorn 서버를 백그라운드로 실행하고 PID를 저장합니다.
$VENV_PYTHON -m uvicorn main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

echo "서버가 시작될 때까지 대기 중입니다..."

# 서버가 응답할 때까지 최대 60초간 1초마다 확인합니다.
# lsof로 포트가 열렸는지 확인하는 것이 HTTP 요청보다 더 안정적입니다.
for i in {1..60}; do
    if lsof -i :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo "서버가 시작되었습니다."
        
        # UI 파일이 존재하는지 확인합니다.
        if [ -f "$UI_FILE" ]; then
            echo "$UI_FILE 을(를) 기본 브라우저에서 엽니다."
            # macOS에서는 open 명령어를 사용합니다.
            open "$UI_FILE"
        else
            echo "경고: UI 파일($UI_FILE)을 찾을 수 없습니다."
        fi
        
        # 대기 루프를 탈출합니다.
        break
    fi
    sleep 1
    # 60초 후에도 서버가 시작되지 않은 경우
    if [ $i -eq 60 ]; then
        echo "오류: 60초 내에 서버 시작에 실패했습니다."
        # 백그라운드 프로세스가 남아있을 수 있으므로 종료합니다.
        kill $SERVER_PID
        exit 1
    fi
done

# 서버 프로세스가 종료될 때까지 스크립트가 대기하도록 합니다.
# 이렇게 하면 사용자가 Ctrl+C로 서버를 종료할 때 스크립트도 함께 종료됩니다.
wait $SERVER_PID

echo "서버가 종료되었습니다."
