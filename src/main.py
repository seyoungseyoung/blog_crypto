import yaml
import logging
import os
from datetime import datetime, timedelta
import random
import time
from data_collector import CryptoDataCollector
from market_analyzer import CryptoAnalyzer
from blog_poster import BlogPoster

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_next_post_time():
    """다음 포스팅 시간을 계산합니다."""
    now = datetime.now()
    current_hour = now.hour
    
    # 다음 포스팅 시간 계산 (3시간 간격)
    next_hour = ((current_hour // 3) + 1) * 3
    if next_hour >= 24:
        next_hour = 0
    
    # 다음 포스팅 날짜/시간 설정
    next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    if next_hour < current_hour:
        next_time += timedelta(days=1)
    
    # 랜덤 오차 추가 (±15분)
    random_minutes = random.randint(-15, 15)
    next_time += timedelta(minutes=random_minutes)
    
    return next_time

def main():
    logger = setup_logging()
    logger.info("Starting crypto market analysis and blog posting process...")

    try:
        # 설정 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '..', 'config', 'config.yaml')
        
        logger.info(f"Loading configuration from: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info("Configuration loaded successfully")

        while True:
            # 다음 포스팅 시간까지 대기
            next_post_time = get_next_post_time()
            wait_seconds = (next_post_time - datetime.now()).total_seconds()
            
            if wait_seconds > 0:
                logger.info(f"Next post scheduled for: {next_post_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"Waiting for {wait_seconds/60:.1f} minutes...")
                time.sleep(wait_seconds)
            
            # 데이터 수집
            collector = CryptoDataCollector(config)
            logger.info("Collecting crypto market data and news...")
            crypto_data, news = collector.collect_data()
            
            if not crypto_data:
                logger.error("Failed to collect crypto market data")
                continue
                
            if not news:
                logger.error("Failed to collect news")
                continue

            # 시장 분석
            logger.info("Analyzing market trends and news...")
            analyzer = CryptoAnalyzer(config)
            analysis = analyzer.analyze_crypto_trend(crypto_data, news)

            if not analysis:
                logger.error("Failed to analyze market data and news")
                continue

            # 블로그 포스팅
            logger.info("Starting blog posting process...")
            poster = BlogPoster(config)
            poster._setup_driver()
            
            if poster.login():
                logger.info("Successfully logged in to Naver Blog")
                
                # 분석 결과에서 제목, 내용, 태그 추출
                title = analysis.get('title', f"암호화폐 시장 동향 분석 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                content = analysis.get('content', '')
                
                if not content:
                    logger.error("Analysis content is empty")
                    continue
                    
                tags = analysis.get('tags', ["암호화폐", "비트코인", "이더리움", "블록체인", "디지털자산", "시장분석"])
                
                logger.info(f"Posting analysis with title: {title}")
                logger.info(f"Content length: {len(content)} characters")
                logger.info(f"Tags: {tags}")
                
                success = poster.create_post(title, content, tags)
                if success:
                    logger.info("Market analysis post created successfully")
                else:
                    logger.error("Failed to create market analysis post")
            else:
                logger.error("Failed to login to Naver Blog")
            
            poster.close()
            logger.info("Analysis and posting process completed")
            
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 