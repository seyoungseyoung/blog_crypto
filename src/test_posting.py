import yaml
import logging
import os
from data_collector import CryptoDataCollector
from market_analyzer import CryptoAnalyzer
from blog_poster import BlogPoster
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_posting():
    logger = setup_logging()
    logger.info("Starting test posting process...")

    try:
        # 현재 스크립트의 디렉토리 경로를 기준으로 설정 파일 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '..', 'config', 'config.yaml')
        
        logger.info(f"Loading configuration from: {config_path}")
        
        # 설정 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info("Configuration loaded successfully")

        # 데이터 수집
        collector = CryptoDataCollector(config)
        logger.info("Collecting crypto data...")
        crypto_data, news = collector.collect_data()
        
        if not crypto_data:
            logger.error("Failed to collect crypto data")
            return
            
        logger.info("Collecting crypto news...")

        if not news:
            logger.error("Failed to collect news")
            return

        # 시장 분석
        logger.info("Analyzing market data...")
        analyzer = CryptoAnalyzer(config)
        analysis = analyzer.analyze_crypto_trend(crypto_data, news)

        if not analysis:
            logger.error("Failed to analyze data")
            return

        # 블로그 포스팅
        logger.info("Starting blog posting process...")
        poster = BlogPoster(config)
        poster._setup_driver()
        
        if poster.login():
            logger.info("Successfully logged in to Naver Blog")
            
            title = f"[테스트] 오늘의 암호화폐 시장 동향 분석 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            content = analysis['analysis']
            tags = ["암호화폐", "비트코인", "이더리움", "블록체인", "디지털자산", "테스트"]
            
            success = poster.create_post(title, content, tags)
            if success:
                logger.info("Test post created successfully")
            else:
                logger.error("Failed to create test post")
        else:
            logger.error("Failed to login to Naver Blog")
        
        poster.close()
        logger.info("Test posting process completed")
        
    except Exception as e:
        logger.error(f"Error in test posting process: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_posting() 