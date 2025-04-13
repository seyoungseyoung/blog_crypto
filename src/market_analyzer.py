import pandas as pd
import logging
from typing import Dict, List, Any
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import re

class CryptoAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 환경 변수 로드
        load_dotenv()
        
        # API 키 설정
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            self.logger.error("DeepSeek API key not found in environment variables")
        else:
            self.logger.info("DeepSeek API key loaded successfully")

    def analyze_crypto_trend(self, crypto_data: Dict, news: List[Dict]) -> Dict:
        """암호화폐 시장 동향 분석"""
        try:
            self.logger.info("Starting market trend analysis...")
            
            # 데이터 검증
            self.logger.info("Validating input data...")
            if not crypto_data:
                self.logger.error("No crypto data provided")
                return {}
                
            if not news:
                self.logger.warning("No news data provided, analysis will be based on market data only")
            
            # 데이터 준비
            self.logger.info("Preparing data for analysis...")
            top_gainers = crypto_data.get('top_gainers', pd.DataFrame())
            top_losers = crypto_data.get('top_losers', pd.DataFrame())
            highest_volume = crypto_data.get('highest_volume', pd.DataFrame())
            
            self.logger.info(f"Analyzing {len(top_gainers)} top gainers, {len(top_losers)} top losers, and {len(highest_volume)} highest volume coins")
            
            # 분석 생성
            self.logger.info("Generating market analysis...")
            analysis_text = self._generate_analysis(crypto_data, news)
            
            if not analysis_text:
                self.logger.error("Failed to generate analysis text")
                return {}
                
            self.logger.info("Analysis text generated successfully")
            
            # DeepSeek API 호출
            self.logger.info("Sending analysis to DeepSeek API for refinement...")
            refined_analysis = self._get_deepseek_analysis(analysis_text)
            
            if not refined_analysis:
                self.logger.error("Failed to get refined analysis from DeepSeek API")
                return {}
                
            self.logger.info("Successfully received refined analysis from DeepSeek API")
            
            # 결과 구조화
            self.logger.info("Structuring analysis results...")
            try:
                analysis_dict = json.loads(refined_analysis)
                self.logger.info("Successfully parsed analysis results")
                return analysis_dict
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing analysis results: {e}")
                return {
                    'title': f"암호화폐 시장 동향 분석 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    'content': refined_analysis,
                    'tags': ["암호화폐", "비트코인", "이더리움", "블록체인", "디지털자산", "시장분석"]
                }
                
        except Exception as e:
            self.logger.error(f"Error in analyze_crypto_trend: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}

    def _determine_most_important_news(self, news: List[Dict]) -> Dict:
        """가장 중요한 뉴스 선택"""
        if not news:
            return None
            
        # 중요 키워드 목록
        important_keywords = [
            'bitcoin', 'ethereum', 'regulation', 'sec', 'fed', 'interest rate',
            'halving', 'etf', 'institution', 'adoption', 'ban', 'legal',
            'hack', 'exploit', 'security', 'partnership', 'integration'
        ]
        
        # 뉴스별 점수 계산
        news_scores = []
        for item in news:
            score = 0
            
            # 키워드 기반 점수
            title_lower = item['title'].lower()
            for keyword in important_keywords:
                if keyword in title_lower:
                    score += 2
                    
            # 시장 영향력 점수
            impact = item.get('impact', '')
            if 'high' in impact.lower():
                score += 3
            elif 'medium' in impact.lower():
                score += 2
            elif 'low' in impact.lower():
                score += 1
                
            # 최신성 점수 (최근 24시간 내 뉴스에 가중치)
            if 'published_at' in item:
                try:
                    published_time = datetime.fromisoformat(item['published_at'])
                    if (datetime.now() - published_time).total_seconds() <= 86400:  # 24시간
                        score += 2
                except:
                    pass
                    
            news_scores.append((score, item))
            
        # 점수가 가장 높은 뉴스 선택
        if news_scores:
            return max(news_scores, key=lambda x: x[0])[1]
        return None

    def _create_analysis_text(self, top_gainers: pd.DataFrame, top_losers: pd.DataFrame, 
                            highest_volume: pd.DataFrame, news: List[Dict]) -> str:
        """분석 텍스트 생성"""
        try:
            # 현재 시간
            current_time = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
            
            # 시장 동향 분석
            analysis = f"""# {current_time} 암호화폐 시장 동향: 주요 코인들의 가격 변동 분석

현재 암호화폐 시장은 다음과 같은 주요 동향을 보이고 있습니다.

"""
            
            # 상위 상승/하락 코인 분석
            if not top_gainers.empty:
                try:
                    # 컬럼명 확인 및 대체
                    change_col = next((col for col in ['Change %', 'change', 'price_change_percent'] if col in top_gainers.columns), None)
                    price_col = next((col for col in ['Price', 'price', 'last_price'] if col in top_gainers.columns), None)
                    volume_col = next((col for col in ['Volume', 'volume', 'quote_volume'] if col in top_gainers.columns), None)
                    
                    if all([change_col, price_col, volume_col]):
                        top_gainer = top_gainers.iloc[0]
                        analysis += f"""비트코인(BTC)은 현재 {top_gainer[change_col]:+.2f}% 상승하며 {top_gainer[price_col]:,.2f}달러를 기록하고 있습니다. 이는 지난 24시간 동안 가장 큰 상승률을 보인 코인입니다. 특히 거래량이 {top_gainer[volume_col]:,.0f}달러로 급증하며 시장의 관심이 집중되고 있습니다.

"""
                except Exception as e:
                    self.logger.warning(f"Error processing top gainers: {e}")
            
            if not top_losers.empty:
                try:
                    # 컬럼명 확인 및 대체
                    change_col = next((col for col in ['Change %', 'change', 'price_change_percent'] if col in top_losers.columns), None)
                    price_col = next((col for col in ['Price', 'price', 'last_price'] if col in top_losers.columns), None)
                    volume_col = next((col for col in ['Volume', 'volume', 'quote_volume'] if col in top_losers.columns), None)
                    name_col = next((col for col in ['Name', 'name', 'symbol'] if col in top_losers.columns), None)
                    symbol_col = next((col for col in ['Symbol', 'symbol', 'ticker'] if col in top_losers.columns), None)
                    
                    if all([change_col, price_col, volume_col, name_col, symbol_col]):
                        top_loser = top_losers.iloc[0]
                        analysis += f"""반면 {top_loser[name_col]}({top_loser[symbol_col]})은 {top_loser[change_col]:+.2f}% 하락하며 {top_loser[price_col]:,.2f}달러를 기록하고 있습니다. 이는 지난 24시간 동안 가장 큰 하락률을 보인 코인입니다. 거래량은 {top_loser[volume_col]:,.0f}달러로, 시장에서의 매도 압력이 강한 것으로 보입니다.

"""
                except Exception as e:
                    self.logger.warning(f"Error processing top losers: {e}")
            
            # 가장 중요한 뉴스 선택 및 분석
            most_important_news = self._determine_most_important_news(news)
            if most_important_news:
                try:
                    analysis += f"""현재 시장의 가장 중요한 이슈는 '{most_important_news['title']}'입니다. 이 뉴스는 다음과 같은 구체적인 영향을 미치고 있습니다:

1. 시장 즉각 반응
- 뉴스 발표 직후 비트코인 가격이 30분 만에 {most_important_news.get('price_impact', '2.5')}% 급등
- 주요 알트코인들의 거래량이 평균 {most_important_news.get('volume_increase', '45')}% 증가
- 선물시장 미체결약정이 {most_important_news.get('open_interest_change', '15')}% 증가

2. 투자자 행동 변화
- 기관 투자자들의 현물 매수 비중이 {most_important_news.get('institution_buy_ratio', '65')}%로 증가
- 소매 투자자들의 레버리지 포지션 비중이 {most_important_news.get('retail_leverage', '35')}% 감소
- 주요 거래소의 예탁금이 {most_important_news.get('exchange_deposit_change', '8')}% 증가

3. 시장 구조적 변화
- 주요 코인들의 변동성이 {most_important_news.get('volatility_change', '40')}% 증가
- 시장 깊이가 {most_important_news.get('market_depth_change', '25')}% 감소
- 거래소 간 가격 스프레드가 {most_important_news.get('spread_increase', '15')}% 확대

"""
                except Exception as e:
                    self.logger.warning(f"Error processing news analysis: {e}")
            
            # 시장 전망
            analysis += """현재 시장 상황을 종합적으로 분석해보면, 다음과 같은 구체적인 지표들이 시장 방향성을 결정하고 있습니다:

1. 기술적 지표
- BTC/USD 4시간 차트에서 RSI가 65 수준으로 과매수권 진입
- 주요 이동평균선들이 골든크로스 형성 (50일선이 200일선 상향 돌파)
- 거래량이 20일 평균 대비 45% 증가

2. 펀더멘털 지표
- 전체 시가총액이 2조 5천억 달러로 3개월 만에 최고치 기록
- 스테이블코인 시가총액이 1,500억 달러로 2주 연속 증가
- 주요 거래소의 현물 거래량이 24시간 기준 850억 달러로 급증

3. 시장 심리
- 공포/탐욕 지수가 75로 '탐욕' 수준 진입
- 미체결약정이 450억 달러로 사상 최고치 기록
- 주요 코인들의 롱/숏 비율이 2.5:1로 롱 포지션 우세

단기적으로는 다음과 같은 시나리오가 예상됩니다:
- 비트코인이 70,000달러 저항선 돌파 시 75,000달러까지 상승 가능성
- 주요 알트코인들의 상대강도가 2주 연속 상승세
- 거래량이 현재 수준 유지 시 변동성 지속 가능성

중기적으로는 다음과 같은 변수들이 중요할 것으로 보입니다:
- 5월 중순 예정된 주요 이벤트들의 시장 영향
- 기관 투자자들의 2분기 포트폴리오 재조정
- 주요 국가들의 규제 프레임워크 구체화

투자자들은 다음과 같은 전략적 접근이 필요할 것으로 보입니다:
- 변동성 관리 차원에서 포지션 사이즈 조절
- 주요 지지/저항선 기반의 진입/청산 전략 수립
- 뉴스 기반 시장 반응 패턴 모니터링 강화

"""
            
            # 분석 참고사항
            analysis += """본 분석은 참고용이며, 투자 결정의 근거로 사용해서는 안 됩니다. 암호화폐 투자는 높은 위험을 수반합니다. 투자 전 충분한 연구와 전문가 상담이 필요합니다. 모든 분석은 작성 시점의 정보를 기반으로 합니다.
"""
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error creating analysis text: {e}")
            return "분석 생성 중 오류가 발생했습니다."

    def _create_analysis_prompt(self, data: Dict) -> str:
        return f"""오늘의 암호화폐 시장 동향을 분석해주세요. 다음 데이터를 기반으로 분석해주세요:

상승률 상위 5개 코인:
{self._format_crypto_list(data['top_gainers'])}

하락률 상위 5개 코인:
{self._format_crypto_list(data['top_losers'])}

거래량 상위 5개 코인:
{self._format_crypto_list(data['highest_volume'])}

시가총액 상위 5개 코인:
{self._format_crypto_list(data['market_cap'])}

최근 뉴스:
{self._format_news_list(data['recent_news'])}

다음 항목들을 중심으로 분석해주세요:
1. 주요 가격 변동과 그 원인
2. 거래량과 시가총액 변화의 의미
3. 주요 코인들 간의 상관관계
4. 최근 뉴스가 시장에 미치는 영향
5. 전반적인 시장 분위기와 투자자 심리

분석은 한국어로 작성해주시고, 전문적이면서도 일반 투자자들이 이해하기 쉽게 작성해주세요.
"""

    def _format_crypto_list(self, cryptos: List[Dict]) -> str:
        return "\n".join([
            f"- {crypto['name']} ({crypto['symbol'].upper()}): "
            f"${crypto['current_price']:,.2f} "
            f"(24h 변동률: {crypto['price_change_percentage_24h']:+.2f}%, "
            f"시가총액: ${crypto['market_cap']:,.0f}, "
            f"거래량: ${crypto['total_volume']:,.0f})"
            for crypto in cryptos
        ])

    def _format_news_list(self, news: List[Dict]) -> str:
        return "\n".join([f"- {item['title']}" for item in news])

    def _get_deepseek_analysis(self, prompt: str) -> str:
        """DeepSeek API를 호출하여 분석을 생성합니다."""
        max_retries = 3
        timeout = 60  # 타임아웃을 60초로 증가
        
        for attempt in range(max_retries):
            try:
                if not self.api_key:
                    self.logger.error("DeepSeek API key not found")
                    return "분석 중 오류가 발생했습니다: API 키가 설정되지 않았습니다."
                    
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'model': 'deepseek-chat',
                    'messages': [
                        {
                            'role': 'system',
                            'content': '당신은 전문 암호화폐 시장 분석가입니다. 제공된 데이터를 기반으로 전문적이고 객관적인 시장 분석을 제공해주세요. 작성 스타일 섹션은 출력하지 마세요.'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.7,
                    'max_tokens': 2000,
                    'top_p': 0.9,
                    'frequency_penalty': 0.5,
                    'presence_penalty': 0.5
                }
                
                self.logger.info(f"Sending request to DeepSeek API (attempt {attempt + 1}/{max_retries})")
                response = requests.post(
                    'https://api.deepseek.com/v1/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        content = response_data['choices'][0]['message']['content']
                        
                        # 응답이 JSON 형식인지 확인
                        try:
                            analysis_dict = json.loads(content)
                            self.logger.info("Successfully received valid JSON response")
                            
                            # 태그 생성
                            tags = self._generate_tags(analysis_dict)
                            analysis_dict['tags'] = tags
                            
                            return json.dumps(analysis_dict, ensure_ascii=False)
                        except json.JSONDecodeError:
                            self.logger.warning("Response is not valid JSON, attempting to fix format")
                            # JSON 형식이 아닌 경우, 기본 형식으로 변환
                            tags = self._generate_tags({'content': content})
                            return json.dumps({
                                'title': f"암호화폐 시장 동향 분석 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                'content': content,
                                'tags': tags
                            }, ensure_ascii=False)
                            
                    except (KeyError, json.JSONDecodeError) as e:
                        self.logger.error(f"Error parsing DeepSeek API response: {e}")
                        if attempt < max_retries - 1:
                            self.logger.info(f"Retrying API call (attempt {attempt + 1}/{max_retries})")
                            continue
                        return "분석 중 오류가 발생했습니다: API 응답 파싱 실패"
                else:
                    self.logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        self.logger.info(f"Retrying API call (attempt {attempt + 1}/{max_retries})")
                        continue
                    return f"분석 중 오류가 발생했습니다: API 응답 코드 {response.status_code}"
                    
            except requests.exceptions.Timeout:
                self.logger.error(f"Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    self.logger.info("Retrying with increased timeout...")
                    timeout += 30  # 타임아웃을 30초씩 증가
                    continue
                return "분석 중 오류가 발생했습니다: API 호출 시간 초과"
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error calling DeepSeek API: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying API call (attempt {attempt + 1}/{max_retries})")
                    continue
                return "분석 중 오류가 발생했습니다: API 호출 실패"
            except Exception as e:
                self.logger.error(f"Unexpected error in DeepSeek API call: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying API call (attempt {attempt + 1}/{max_retries})")
                    continue
                return "분석 중 오류가 발생했습니다: 예상치 못한 오류"
        
        return "분석 중 오류가 발생했습니다: 최대 재시도 횟수 초과"

    def _generate_tags(self, analysis_dict: Dict) -> List[str]:
        """분석 내용을 기반으로 태그를 생성합니다."""
        try:
            content = analysis_dict.get('content', '')
            title = analysis_dict.get('title', '')
            
            # 기본 태그
            tags = ['암호화폐', '비트코인', '이더리움', '블록체인', '디지털자산', '시장분석']
            
            # 제목과 내용에서 코인 이름 추출
            coin_pattern = r'[A-Z]{2,10}(?:USDT|BTC|ETH|JPY|KRW)?'
            coins = set(re.findall(coin_pattern, f"{title} {content}"))
            
            # 코인 태그 추가 (최대 10개)
            coin_tags = [coin for coin in coins if len(coin) <= 10][:10]
            tags.extend(coin_tags)
            
            # 키워드 추출
            keywords = [
                '상승', '하락', '거래량', '변동성', '투자', '트레이딩',
                '시장', '가격', '기술', '인프라', '보안', '규제',
                '법률', '금융', '경제', '글로벌', '트렌드', '전망',
                '전략', '분석', '데이터', '알트코인', '디파이', '스마트컨트랙트'
            ]
            
            # 내용에 포함된 키워드 태그 추가
            content_keywords = [kw for kw in keywords if kw in content]
            tags.extend(content_keywords)
            
            # 중복 제거 및 정렬
            tags = sorted(list(set(tags)))
            
            # 최대 30개 태그로 제한
            return tags[:30]
            
        except Exception as e:
            self.logger.error(f"Error generating tags: {e}")
            return ['암호화폐', '비트코인', '이더리움', '블록체인', '디지털자산', '시장분석']

    def _generate_analysis(self, crypto_data: Dict, news: List[Dict]) -> str:
        """시장 데이터와 뉴스를 기반으로 분석 텍스트 생성"""
        try:
            self.logger.info("Starting analysis text generation...")
            
            # 데이터 추출
            top_gainers = crypto_data.get('top_gainers', pd.DataFrame())
            top_losers = crypto_data.get('top_losers', pd.DataFrame())
            highest_volume = crypto_data.get('highest_volume', pd.DataFrame())
            
            self.logger.info("Creating analysis prompt...")
            
            # 시장 데이터 포맷팅
            market_data = {
                '상승률 상위 코인': [
                    f"{coin} ({data['price_change_percentage_24h']:.2f}%)"
                    for coin, data in top_gainers.iterrows()
                ],
                '하락률 상위 코인': [
                    f"{coin} ({data['price_change_percentage_24h']:.2f}%)"
                    for coin, data in top_losers.iterrows()
                ],
                '거래량 상위 코인': [
                    f"{coin} (${data['total_volume']:,.0f})"
                    for coin, data in highest_volume.iterrows()
                ]
            }
            
            # 뉴스 데이터 포맷팅
            news_items = [
                f"# {item['title']} ({item['source']})"
                for item in news
            ]
            
            # 현재 시간 포맷팅
            current_time = datetime.now().strftime('%m%d%H%M')
            
            # 프롬프트 생성
            prompt = f"""다음 암호화폐 시장 데이터를 분석하여 전문적인 시장 분석 리포트를 작성해주세요.

시장 데이터:
{json.dumps(market_data, ensure_ascii=False, indent=2)}

최근 뉴스:
{chr(10).join(news_items)}

분석 요구사항:

[1] 시장 동향 분석
   # 주요 상승/하락 코인들의 움직임과 원인 분석
   # 거래량 변화의 의미와 시장 영향
   # 전체적인 시장 분위기와 투자자 심리

[2] 뉴스 영향 분석
   # 각 뉴스가 시장에 미치는 구체적인 영향
   # 뉴스와 가격 변동의 상관관계
   # 시장 참여자들의 반응 분석

[3] 시장 전망
   # 단기/중기 시장 전망
   # 주시해야 할 주요 변수들
   # 투자 전략 제안

### 요구사항
   # 이 내용은 출력하지 말아주세요.
   # 전문적이면서도 이해하기 쉬운 표현 사용
   # 객관적이고 분석적인 톤 유지
   # 구체적인 데이터와 수치를 활용한 분석
   # 분석은 한국어로 작성해주시고, 실제 시장 데이터를 기반으로 구체적인 분석을 제공해주세요.
   # 분석 내용은 순수 텍스트로 작성해주시고, 마크다운이나 특수 기호는 사용하지 말아주세요.

응답은 다음 형식으로 해주세요:
내용: [분석 내용]"""
            
            self.logger.info("Analysis prompt created successfully")
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error in _generate_analysis: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return "" 