import os
import requests
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from downloader.file_manager import save_clip
from downloader.twitch_parser import get_clip_download_url
from utils.logger import setup_logger

# Set up logging
logger = setup_logger()

def download_clip(clip_info, output_dir, logger):
    """
    Download a single Twitch clip and save it.
    
    :param clip_info: Dictionary containing clip name and link
    :param output_dir: Directory to save the file
    :param logger: Logger object
    """
    clip_url = clip_info['url']
    clip_name = clip_info['name']
    
    download_url = get_clip_download_url(clip_url)
    if download_url:
        save_clip(download_url, clip_name, output_dir)
        logger.info(f"Download completed: {clip_name}")
    else:
        logger.error(f"Failed to get download URL for {clip_name}")

def download_clips(clips_info, output_dir, max_workers=5, logger=None):
    """
    Download multiple Twitch clips in parallel.
    
    :param clips_info: List containing all clip information (name and url).
    :param output_dir: Directory to save the files.
    :param max_workers: Maximum number of concurrent threads.
    :param logger: Logger object
    """
    if logger is None:
        from utils.logger import setup_logger
        logger = setup_logger()

    logger.info(f"Starting download of {len(clips_info)} clips to {output_dir}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) as driver:
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(download_single_clip, clip, output_dir, logger, driver) for clip in clips_info]
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error downloading clip: {str(e)}")
        except Exception as e:
            logger.error(f"Error in download process: {str(e)}")
        finally:
            logger.info("Download process completed")

def download_single_clip(clip, output_dir, logger, driver):
    clip_url = clip['url']
    clip_name = clip['name']
    
    logger.info(f"Processing clip: {clip_name}")
    
    try:
        download_url = get_clip_download_url(clip_url, driver)
        if download_url:
            save_clip(download_url, clip_name, output_dir)
            logger.info(f"Download completed: {clip_name}")
        else:
            logger.error(f"Failed to get download URL for clip: {clip_name}")
    except Exception as e:
        logger.error(f"Error processing clip {clip_name}: {str(e)}")
