import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
from dotenv import load_dotenv
from typing import List
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime

class BlogPoster:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.driver = None
        load_dotenv()  # Load environment variables
        self.username = os.getenv('NAVER_USERNAME')
        self.password = os.getenv('NAVER_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("네이버 로그인 정보가 환경 변수에 없습니다. NAVER_USERNAME과 NAVER_PASSWORD를 설정해주세요.")

    def _setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            chrome_options = Options()
            # 헤드리스 모드 제거
            # chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 웹드라이버 자동 감지 방지
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            # 페이지 로드 타임아웃 설정
            self.driver.set_page_load_timeout(30)
            
            print("✓ 크롬 드라이버 설정 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"크롬 드라이버 설정 중 오류 발생: {e}")
            print(f"✗ 크롬 드라이버 설정 실패: {e}")
            return False

    def _login(self):
        """네이버 로그인"""
        try:
            # 네이버 홈페이지 접속
            self.driver.get('https://www.naver.com')
            time.sleep(2)

            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.CLASS_NAME, 'link_login')
            login_button.click()
            time.sleep(2)

            # 아이디 입력
            username = self.driver.find_element(By.ID, 'id')
            username.send_keys(self.config['naver']['username'])
            time.sleep(1)

            # 비밀번호 입력
            password = self.driver.find_element(By.ID, 'pw')
            password.send_keys(self.config['naver']['password'])
            time.sleep(1)

            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.ID, 'log.login')
            login_button.click()
            time.sleep(3)

            # 블로그 메인 페이지로 이동
            self.driver.get('https://blog.naver.com')
            time.sleep(3)

            # 내 블로그로 이동
            my_blog_link = self.driver.find_element(By.CSS_SELECTOR, 'a.link_myblog')
            my_blog_link.click()
            time.sleep(3)

            # 글쓰기 버튼 클릭
            write_button = self.driver.find_element(By.CSS_SELECTOR, 'a.btn_write')
            write_button.click()
            time.sleep(3)

            self.logger.info("Successfully logged in and navigated to blog write page")
        except Exception as e:
            self.logger.error(f"Error during login and navigation: {e}")
            raise

    def post_analysis(self, analysis: dict):
        """분석 결과를 블로그에 포스팅"""
        try:
            self._setup_driver()
            self._login()

            # 제목 입력
            title = self.driver.find_element(By.CSS_SELECTOR, 'input.se-text-input')
            title.send_keys('암호화폐 시장 동향 분석')
            time.sleep(1)

            # 내용 입력
            content = self.driver.find_element(By.CSS_SELECTOR, 'div.se-component-content')
            content.send_keys(analysis['analysis'])
            time.sleep(1)

            # 발행 버튼 클릭
            publish_button = self.driver.find_element(By.CSS_SELECTOR, 'button.publish')
            publish_button.click()
            time.sleep(3)

            self.logger.info("Successfully posted analysis to blog")
        except Exception as e:
            self.logger.error(f"Failed to create post: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()

    def check_login_status(self):
        """현재 로그인 상태를 확인합니다."""
        try:
            # 네이버 블로그 메인 페이지로 이동
            self.driver.get('https://blog.naver.com')
            time.sleep(2)
            
            # 로그인 버튼이 있는지 확인
            try:
                login_button = self.driver.find_element(By.CLASS_NAME, 'link_login')
                return False  # 로그인 버튼이 있으면 로그인되지 않은 상태
            except NoSuchElementException:
                return True  # 로그인 버튼이 없으면 로그인된 상태
                
        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            return False

    def login(self):
        """네이버에 로그인합니다."""
        try:
            print("- 네이버 로그인 시작...")
            
            # 네이버 로그인 페이지로 이동
            self.driver.get('https://nid.naver.com/nidlogin.login')
            time.sleep(2)
            
            # JavaScript를 통한 로그인 정보 입력
            self.driver.execute_script(
                f"document.getElementsByName('id')[0].value='{self.username}'")
            time.sleep(0.5)
            
            self.driver.execute_script(
                f"document.getElementsByName('pw')[0].value='{self.password}'")
            time.sleep(0.5)
            
            # 로그인 버튼 클릭
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'btn_login'))
            )
            login_button.click()
            
            # 로그인 성공 확인
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: 'nid.naver.com/nidlogin.login' not in d.current_url
                )
                print(f"✓ 네이버 로그인 성공. 현재 URL: {self.driver.current_url}")
                return True
            except TimeoutException:
                print("✗ 로그인 실패: 아이디 또는 비밀번호를 확인해주세요.")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {e}", exc_info=True)
            print(f"✗ 로그인 실패: {str(e)}")
            return False

    def create_post(self, title: str, content: str, tags: List[str]) -> bool:
        """네이버 블로그에 글을 포스팅합니다."""
        if not self.driver:
            self.logger.error("WebDriver가 초기화되지 않았습니다.")
            return False

        try:
            # 1. 글쓰기 페이지로 직접 이동
            write_url = f"https://blog.naver.com/{self.username}/postwrite"
            print(f"- 글쓰기 페이지로 직접 이동 시도: {write_url}")
            self.driver.get(write_url)
            print("- 페이지 로딩 대기 (5초)...")
            time.sleep(5)
            current_url = self.driver.current_url
            print(f"- 현재 URL: {current_url}")

            if "postwrite" not in current_url.lower():
                print(f"✗ 글쓰기 페이지로 이동 실패. 예상 URL과 다름: {current_url}")
                return False

            # 2. 이전 글 작성 확인 팝업 처리
            try:
                print("- 이전 글 팝업 확인 중...")
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-button-text'))
                )
                cancel_buttons = self.driver.find_elements(By.CLASS_NAME, 'se-popup-button-text')
                if cancel_buttons:
                    for button in cancel_buttons:
                        if '취소' in button.text or 'cancel' in button.text.lower():
                            button.click()
                            time.sleep(3)
                            print("- 이전 글 '취소' 처리 완료")
                            break
            except TimeoutException:
                print("- 이전 글 팝업 없음 - 계속 진행")
            except Exception as e:
                print(f"- 이전 글 팝업 처리 중 오류 (무시하고 계속): {e}")

            # 3. 도움말 닫기 버튼 처리
            time.sleep(2)
            try:
                print("- 도움말 팝업 확인 중...")
                help_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), '닫기') or contains(@class, 'close')]")
                for button in help_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            print("- 도움말 닫기 버튼 클릭 시도...")
                            button.click()
                            time.sleep(2)
                            print("- 도움말 닫기 완료")
                            break
                    except Exception as inner_e:
                        print(f"-- 도움말 버튼 처리 중 내부 오류 (무시): {inner_e}")
                        continue
            except Exception as e:
                print(f"- 도움말 팝업 처리 중 오류 (무시하고 계속): {e}")

            # 4. 제목 입력
            try:
                print("- 제목 영역 찾는 중...")
                title_area = None
                title_selectors = [
                    'span.se-placeholder.__se_placeholder', 
                    'span.se-ff-nanumgothic.se-fs32.__se-node',
                    '[contenteditable="true"][aria-label*="제목"]'
                ]
                for i, selector in enumerate(title_selectors):
                    try:
                        title_area = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        print(f"- 제목 영역 찾음 (선택자 {i+1}: {selector})")
                        break
                    except TimeoutException:
                        if i == len(title_selectors) - 1:
                            print("✗ 제목 영역을 찾을 수 없습니다.")
                            return False
                        else:
                            print(f"- 제목 영역 선택자 {i+1} 실패, 다음 시도...")
               
                title_area.click()
                time.sleep(0.5)
                if os.name == 'nt': 
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                else: 
                    ActionChains(self.driver).key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).perform()
                time.sleep(0.2)
                ActionChains(self.driver).send_keys(Keys.DELETE).perform()
                time.sleep(0.2)
                actions = ActionChains(self.driver)
                actions.send_keys(title)
                time.sleep(0.5)
                actions.send_keys(Keys.ENTER).perform()
                print("- 제목 입력 및 Enter 완료")
                time.sleep(1.5)
                
                # 본문 영역으로 포커스 이동
                print("- 본문 영역으로 포커스 이동 시도...")
                body_selectors = [
                    'div.se-component-content p.se-text-paragraph',
                    'div.se-main-container .se-component[contenteditable="true"]',
                    '[contenteditable="true"][aria-label*="내용"]'
                ]
                editor_element = None
                clicked_body = False
                for i, selector in enumerate(body_selectors):
                    try:
                        editor_element = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        print(f"- 본문 영역 찾음 (선택자 {i+1}: {selector})")
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", editor_element)
                            print("- 본문 영역 JavaScript 클릭 성공 (포커스 이동)")
                            time.sleep(1.0)
                            clicked_body = True
                            break
                        except Exception as click_e:
                            print(f"- 본문 영역 JavaScript 클릭 실패 (선택자 {i+1}): {click_e}, 다음 시도...")
                            if i == len(body_selectors) - 1:
                                print("✗ 모든 본문 영역 클릭 실패")
                                return False
                    except TimeoutException:
                        if i == len(body_selectors) - 1:
                            print("✗ 본문 영역을 찾을 수 없습니다.")
                            return False
                        else:
                            print(f"- 본문 영역 선택자 {i+1} 실패, 다음 시도...")
                
                if not clicked_body:
                    print("✗ 본문 영역 클릭에 최종 실패했습니다.")
                    return False

            except Exception as e:
                print(f"✗ 제목 입력 또는 본문 포커스 이동 실패: {e}")
                return False

            # 5. 본문 입력
            try:
                print("- 본문 내용 입력 시작...")
                time.sleep(0.5)
                actions = ActionChains(self.driver)
                cleaned_content = content.strip()
                total_chars = len(cleaned_content)
                print(f"- 총 {total_chars} 문자 입력 예정")

                for i, char in enumerate(cleaned_content):
                    if char == '\n':
                        actions.send_keys(Keys.ENTER)
                    else:
                        actions.send_keys(char)
                    actions.perform()
                    time.sleep(0.02)

                    if (i + 1) % 100 == 0 or (i + 1) == total_chars:
                        print(f"  ... {i+1}/{total_chars} 문자 입력 완료")

                print("- 모든 본문 문자 입력 완료.")
                time.sleep(1)

            except Exception as e:
                print(f"✗ 본문 입력 실패: {e}")
                return False

            # 6. 1단계 발행 버튼 클릭
            try:
                print("- 1단계 발행 버튼 클릭 시도...")
                publish_script = "document.querySelector('button.publish_btn__m9KHH').click(); return true;"
                try:
                    self.driver.execute_script(publish_script)
                    print("- 1단계 발행 버튼 클릭 완료 (JavaScript). 발행 설정 창 대기 (5초)...")
                    time.sleep(5)
                except Exception as js_e:
                    print(f"- JavaScript 클릭 실패 ({js_e}), Selenium 클릭 시도...")
                    publish_button_selector = 'button.publish_btn__m9KHH'
                    publish_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, publish_button_selector))
                    )
                    publish_button.click()
                    print("- 1단계 발행 버튼 클릭 완료 (Selenium). 발행 설정 창 대기 (5초)...")
                    time.sleep(5)
            except Exception as e:
                print(f"✗ 1단계 발행 버튼 클릭 실패: {e}")
                return False

            # 7. 카테고리 선택
            try:
                print("- 카테고리 선택 중...")
                category_button_selector = 'button.selectbox_button__jb1Dt'
                category_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, category_button_selector))
                )
                category_button.click()
                time.sleep(1)
                
                category_text_xpath = "//label[contains(., '실시간 암호화폐')]"
                try:
                    category_label = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, category_text_xpath))
                    )
                except TimeoutException:
                    category_label_selector = 'label[for="category-19"]'
                    print(f"- 카테고리 텍스트 선택자 실패, ID({category_label_selector}) 기반 시도...")
                    category_label = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, category_label_selector))
                    )

                category_label.click()
                print("✓ 카테고리 선택 완료")
                time.sleep(1)
            except Exception as e:
                print(f"✗ 카테고리 선택 실패 (무시하고 진행): {e}")

            # 8. 태그 입력
            if tags:
                try:
                    print("- 태그 입력 시작...")
                    tag_input_selector = 'input#tag-input.tag_input__rvUB5'
                    tag_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, tag_input_selector))
                    )
                    for tag in tags:
                        tag_input.clear()
                        time.sleep(0.1)
                        tag_input.send_keys(tag)
                        time.sleep(0.5)
                        tag_input.send_keys(Keys.ENTER)
                        time.sleep(1)
                    print("- 모든 태그 입력 완료")
                except Exception as e:
                    print(f"✗ 태그 입력 실패 (무시하고 진행): {e}")
            else:
                print("- 입력할 태그 없음")

            # 9. 2단계 최종 발행 버튼 클릭
            try:
                print("- 2단계 최종 발행 버튼 클릭 시도...")
                final_publish_script = "document.querySelector('button.confirm_btn__WEaBq[data-testid=\"seOnePublishBtn\"]\').click(); return true;"
                try:
                    self.driver.execute_script(final_publish_script)
                    print("- 2단계 최종 발행 버튼 클릭 완료 (JavaScript). 포스팅 완료 대기 (7초)...")
                    time.sleep(7)
                except Exception as js_e:
                    print(f"- JavaScript 클릭 실패 ({js_e}), Selenium 클릭 시도...")
                    final_publish_button_selector = 'button.confirm_btn__WEaBq[data-testid=\"seOnePublishBtn\"]\''
                    final_publish_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, final_publish_button_selector))
                    )
                    final_publish_button.click()
                    print("- 2단계 최종 발행 버튼 클릭 완료 (Selenium). 포스팅 완료 대기 (7초)...")
                    time.sleep(7)
                
                if "postwrite" not in self.driver.current_url.lower():
                    print("✓ 블로그 포스팅 성공!")
                    return True
                else:
                    print(f"✗ 포스팅 실패 또는 확인 불가: 현재 URL이 여전히 postwrite 페이지입니다 ({self.driver.current_url})")
                    return False

            except Exception as e:
                print(f"✗ 2단계 최종 발행 버튼 클릭 실패: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error creating post: {str(e)}", exc_info=True)
            print(f"✗ 포스팅 생성 중 예외 발생: {e}")
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f'error_screenshot_{timestamp}.png'
                self.driver.save_screenshot(screenshot_path)
                print(f"- 오류 발생 시점 스크린샷 저장: {screenshot_path}")
            except Exception as ss_e:
                print(f"- 스크린샷 저장 실패: {ss_e}")
            return False

    def close(self):
        if self.driver:
            self.driver.quit() 