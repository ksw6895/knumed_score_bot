import time
import os
import requests
import traceback
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv  # .env 라이브러리 import

# --- 1. [필수] .env 파일 로드 ---
load_dotenv()

# --- 2. [필수] 사용자 설정 (환경 변수에서 값 읽어오기) ---
YOUR_ID = os.environ.get("KNU_ID")
YOUR_PW = os.environ.get("KNU_PW")
YOUR_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
YOUR_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# [안전 장치] .env 파일이 제대로 로드되었는지 확인
if not YOUR_ID or not YOUR_PW or not YOUR_BOT_TOKEN or not YOUR_CHAT_ID:
    print("=" * 50)
    print("!!! [치명적 오류] .env 파일 설정을 확인하세요 !!!")
    print("KNU_ID, KNU_PW, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID")
    print("4가지 값이 .env 파일에 모두 올바르게 입력되어야 합니다.")
    print("=" * 50)
    exit() # 봇 종료


# --- 3. 봇 내부 설정 (수정 X) ---
LOGIN_URL = "https://med.knu.ac.kr/pages/sub.htm?nav_code=knu1670415116"
GRADE_PAGE_URL = "https://med.knu.ac.kr/pages/sub.htm?nav_code=knu1672121844"
LAST_GRADE_FILE = "last_grade.txt"


# --- 4. 텔레그램 메시지 발송 함수 ---
def send_telegram_message(message):
    """(수정 X) 텔레그램으로 메시지를 보냅니다."""
    try:
        url = f"https://api.telegram.org/bot{YOUR_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': YOUR_CHAT_ID,
            'text': message
        }
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("텔레그램 메시지 발송 성공!")
        else:
            print(f"텔레그램 발송 실패: {response.text}")
    except Exception as e:
        print(f"텔레그램 발송 중 오류: {e}")

# --- 5. 로그인 및 성적 페이지 이동 함수 ---
def login_and_go_to_grades():
    """(수정 X) 봇이 켜지거나, 세션 만료 시 '로그인'만 담당하는 함수."""
    driver = None
    print("Selenium 드라이버를 (재)시작합니다...")
    try:
        # --- 안티봇 우회 옵션 ---
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # --- [중요] Headless 모드 ---
        # 봇을 화면에 안 띄우고 백그라운드에서 실행하려면 아래 줄의 #을 지우세요.
        # (로컬 테스트 시에는 #을 남겨두는 게 좋습니다.)
        # options.add_argument("--headless") 
        # -----------------------------
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10) 

        # --- 로그인 ---
        print(f"로그인 페이지로 이동합니다: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        time.sleep(1)
        
        print("로그인 (엔터 키) 시도...")
        driver.find_element(By.ID, "userid").send_keys(YOUR_ID)
        pw_box = driver.find_element(By.ID, "passwd")
        pw_box.send_keys(YOUR_PW)
        time.sleep(0.5)
        pw_box.send_keys(Keys.ENTER)
        
        print("로그인 대기 중... (5초)")
        time.sleep(5)

        # --- 성적 페이지로 이동 ---
        print(f"성적 페이지로 직접 이동합니다: {GRADE_PAGE_URL}")
        driver.get(GRADE_PAGE_URL)
        time.sleep(2)
        
        print("로그인 및 페이지 이동 성공!")
        return driver

    except Exception as e:
        print(f"\n---!!! 로그인 또는 페이지 이동 중 오류 발생 !!!---\n{e}")
        traceback.print_exc() 
        if driver:
            driver.quit()
        return None

# --- 6. 현재 페이지 텍스트 긁어오기 함수 ---
def scrape_grade_text(driver):
    """(수정 X) 현재 페이지에서 '성적표' 텍스트만 긁어옵니다."""
    print("현재 페이지에서 성적표(record-list) 텍스트를 긁어옵니다...")
    grade_table = driver.find_element(By.CLASS_NAME, "record-list")
    return grade_table.text

# --- 7. 파일 읽기/쓰기 함수 ---
def read_last_grade():
    """(수정 X) 파일에 저장된 '지난번' 성적을 읽어옵니다."""
    if not os.path.exists(LAST_GRADE_FILE):
        return "" 
    try:
        with open(LAST_GRADE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"지난 성적 파일 읽기 오류: {e}")
        return ""

def write_last_grade(text):
    """(수정 X) '새로운' 성적을 파일에 덮어씁니다."""
    try:
        with open(LAST_GRADE_FILE, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{LAST_GRADE_FILE}에 새 성적 기록 완료.")
    except Exception as e:
        print(f"새 성적 파일 쓰기 오류: {e}")

# --- 8. 메인 실행 함수 (!!! 여기가 바뀜: 스마트 리포트 기능 !!!) ---
def main_loop():
    print("=" * 40)
    print("경북대 의대 성적 봇 (최종 진화형 / 스마트 리포트)을 시작합니다.")
    print("로직: 1회 로그인 -> 무한 새로고침 -> 30분마다 상태 보고")
    print("=" * 40)
    
    send_telegram_message("🤖 경북대 의대 성적 알림 봇 (스마트 리포트)이 시작되었습니다.")
    
    last_grade = read_last_grade()
    if last_grade:
        print("지난 성적 기록을 불러왔습니다.")
    else:
        print("지난 성적 기록이 없습니다. (첫 실행)")
    
    # 1. 최초 1회 로그인
    driver = login_and_go_to_grades()
    if not driver:
        print("!!! 치명적 오류: 봇 시작 실패 (로그인 불가) !!!")
        send_telegram_message("!!! 🤖 봇 시작 실패 !!!\n로그인에 실패했습니다. ID/PW나 사이트 구조를 확인하세요.")
        return # 봇 종료

    # --- [새 변수] 30분 상태 보고용 타이머 ---
    refresh_count = 0           # 30분간 몇 번 새로고침 했는지 카운트
    last_status_report_time = time.time() # 마지막으로 '상태 보고'한 시간
    STATUS_REPORT_INTERVAL = 1800 # 30분 (1800초)
    # ----------------------------------------

    # 2. 무한 감시 루프 시작
    while True:
        try:
            # --- [A] 성적 긁어오기 시도 ---
            current_grade = scrape_grade_text(driver)

            # --- [B] 성공 시 (로그인 유지 중) ---
            if current_grade != last_grade:
                print("!!! 🚨 성적 변동 감지! 🚨 !!!")
                send_telegram_message(f"🔔 [경북대 의대] 성적 변동이 감지되었습니다!\n\n(새로운 성적표 내용 일부)\n{current_grade[:1000]}...")
                last_grade = current_grade
                write_last_grade(current_grade)
                
                # 성적이 변동되었으니, 카운터 리셋
                refresh_count = 0 
                last_status_report_time = time.time()
                
            else:
                # [변경] 성적 변동 없음 (카운트만 증가)
                refresh_count += 1
                print(f"성적 변동 없음. (현재 {refresh_count}회 새로고침 완료)")
                
                # --- [새 기능] 30분이 지났는지 확인 ---
                current_time = time.time()
                if (current_time - last_status_report_time) > STATUS_REPORT_INTERVAL:
                    print("30분이 경과하여 '상태 보고' 알림을 보냅니다.")
                    send_telegram_message(f"🤖 (현재 {time.strftime('%H:%M:%S')}) 봇 정상 작동 중.\n"
                                          f"지난 30분간 {refresh_count}회 새로고침 완료. (성적 변동 없음)")
                    
                    # '상태 보고'를 했으니 카운터와 시간 리셋
                    refresh_count = 0
                    last_status_report_time = current_time
                # ------------------------------------

            # --- [C] 랜덤 시간 대기 (1분 30초 ~ 2분 30초) ---
            random_wait = random.randint(90, 150) 
            print(f"약 {random_wait//60}분 {random_wait%60}초 후 새로고침합니다...")
            time.sleep(random_wait)
            
            # --- [D] 새로고침 ---
            print("페이지를 새로고침(Refresh)합니다...")
            driver.refresh()
            time.sleep(2) # 새로고침 로딩 대기

        except KeyboardInterrupt:
            # Ctrl+C로 종료 시
            print("\n봇을 수동으로 종료합니다.")
            send_telegram_message("🤖 성적 알림 봇이 수동으로 종료되었습니다.")
            break # 루프 탈출
            
        except Exception as e:
            # --- [E] 오류 발생! (세션 만료 또는 기타 문제) ---
            print(f"\n---!!! 감시 루프 중 오류 발생 (세션 만료 추정) !!!---\n{e}")
            traceback.print_exc()
            send_telegram_message(f"🤖 [알림] 봇 세션이 만료되었거나 오류가 발생했습니다.\n\n오류: {e}\n\n자동 재로그인을 시도합니다...")

            # [F] 기존 드라이버 정리 및 재로그인 시도
            if driver:
                driver.quit()
            
            driver = login_and_go_to_grades() # 재로그인
            
            if not driver:
                # 재로그인마저 실패하면 10분 후 재시도
                print("!!! 재로그인 실패. 10분 후 다시 시도합니다.")
                send_telegram_message("!!! 🤖 재로그인 실패. 10분 후 재시도합니다.")
                time.sleep(600)

    # 루프가 끝나면 (Ctrl+C) 드라이버 최종 종료
    if driver:
        driver.quit()
    print("봇이 완전히 종료되었습니다.")

# --- 9. 프로그램 시작 ---
if __name__ == "__main__":
    main_loop()