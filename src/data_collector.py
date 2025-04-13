import pandas as pd
import requests
import logging
import os
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

class CryptoDataCollector:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 환경 변수 로드
        load_dotenv()
        
        # Binance API 자격 증명 설정
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            self.logger.warning("Binance API credentials not found in environment variables")
        else:
            self.logger.info("Binance API credentials loaded successfully")
            
        # 뉴스 API 설정
        self.news_api_key = os.getenv('NEWS_API_KEY')
        if not self.news_api_key:
            self.logger.warning("News API key not found in environment variables")
        else:
            self.logger.info("News API key loaded successfully")
        
        self.base_url = "https://api.binance.com/api/v3"

    def collect_data(self) -> Tuple[Dict[str, pd.DataFrame], List[Dict]]:
        try:
            self.logger.info("Starting data collection process...")
            
            # 티커 데이터 수집
            self.logger.info("Fetching ticker data from Binance...")
            ticker_data = self._get_ticker_data()
            
            if not ticker_data.empty:
                self.logger.info(f"Successfully collected ticker data for {len(ticker_data)} coins")
                
                # 상위 코인 필터링
                self.logger.info("Filtering top gainers, losers, and highest volume coins...")
                top_gainers = ticker_data.nlargest(5, 'price_change_percentage_24h')
                top_losers = ticker_data.nsmallest(5, 'price_change_percentage_24h')
                highest_volume = ticker_data.nlargest(5, 'total_volume')
                
                self.logger.info(f"Top gainers: {', '.join(top_gainers.index)}")
                self.logger.info(f"Top losers: {', '.join(top_losers.index)}")
                self.logger.info(f"Highest volume: {', '.join(highest_volume.index)}")

                # 뉴스 데이터 수집
                self.logger.info("Fetching crypto news from CryptoCompare...")
                news = self._get_crypto_news()
                self.logger.info(f"Collected {len(news)} news articles")

                return {
                    'top_gainers': top_gainers,
                    'top_losers': top_losers,
                    'highest_volume': highest_volume,
                    'all_data': ticker_data
                }, news
            else:
                self.logger.error("Failed to collect ticker data - empty DataFrame returned")
                return {}, []
        except Exception as e:
            self.logger.error(f"Error collecting data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}, []

    def _get_ticker_data(self) -> pd.DataFrame:
        """Binance API에서 티커 데이터 수집"""
        try:
            self.logger.info("Making request to Binance API...")
            response = requests.get(f"{self.base_url}/ticker/24hr", timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Successfully received response from Binance API")
                data = response.json()
                df = pd.DataFrame(data)
                
                # 필요한 컬럼만 선택
                df = df[['symbol', 'lastPrice', 'priceChangePercent', 'volume', 'quoteVolume']]
                
                # 컬럼명 변경
                df.columns = ['symbol', 'price', 'price_change_percentage_24h', 'volume', 'total_volume']
                
                # 숫자형 데이터로 변환
                numeric_columns = ['price', 'price_change_percentage_24h', 'volume', 'total_volume']
                df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
                
                # 인덱스 설정
                df.set_index('symbol', inplace=True)
                
                self.logger.info(f"Processed ticker data for {len(df)} coins")
                return df
            else:
                self.logger.error(f"Binance API error: {response.status_code} - {response.text}")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error in _get_ticker_data: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return pd.DataFrame()

    def _get_crypto_news(self) -> List[Dict]:
        """암호화폐 관련 뉴스 수집"""
        try:
            self.logger.info("Making request to CryptoCompare API...")
            url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("Successfully received response from CryptoCompare API")
                news_data = response.json()
                if news_data.get('Data'):
                    news_list = [
                        {
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': item.get('source', ''),
                            'published_at': datetime.fromtimestamp(item.get('published_on', 0)).isoformat(),
                            'impact': 'medium'
                        }
                        for item in news_data['Data'][:10]
                    ]
                    self.logger.info(f"Processed {len(news_list)} news articles")
                    return news_list
                else:
                    self.logger.warning("No news data found in response")
                    return []
            else:
                self.logger.error(f"CryptoCompare API error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            self.logger.error(f"Error in _get_crypto_news: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return [] 