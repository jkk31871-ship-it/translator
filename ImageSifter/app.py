import streamlit as st
import os
import time
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
import zipfile
from io import BytesIO

def setup_chrome_driver():
    """Set up Chrome driver with headless options for Replit environment"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Use new headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--force-color-profile=srgb")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    
    # Set up binary locations
    import subprocess
    
    try:
        # Get chromium path
        result = subprocess.run(['which', 'chromium'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            chrome_options.binary_location = result.stdout.strip()
    except:
        pass
    
    # Use system chromedriver directly
    chromedriver_path = "/nix/store/8zj50jw4w0hby47167kqqsaqw4mm5bkd-chromedriver-unwrapped-138.0.7204.100/bin/chromedriver"
    
    try:
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set timeouts to prevent session issues
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        
        return driver
    except Exception as e:
        raise Exception(f"Failed to start ChromeDriver: {str(e)}")

def translate_image_with_google(image_path, source_lang="auto", target_lang="en"):
    """
    Translate an image using Google Translate's image translation feature
    """
    try:
        driver = setup_chrome_driver()
    except Exception as e:
        import traceback
        error_msg = f"Failed to start browser: {str(e)}"
        full_traceback = traceback.format_exc()
        st.error(error_msg)
        st.error(f"Browser setup error details: {full_traceback}")
        return None, None
    
    try:
        # Navigate to Google Translate
        url = f"https://translate.google.com/?sl={source_lang}&tl={target_lang}&op=images"
        driver.get(url)
        
        # Wait for page to load and check if we're connected
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)  # Additional wait for dynamic content
        
        # Try multiple selectors for the file upload input
        upload_selectors = [
            "input[type='file']",
            "input[accept*='image']",
            "[data-test-id='file-upload'] input",
            ".VfPpkd-Bz112c input[type='file']"
        ]
        
        upload_button = None
        for selector in upload_selectors:
            try:
                upload_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                break
            except:
                continue
        
        if not upload_button:
            # If we can't find upload button, take a screenshot for debugging
            debug_screenshot = f"{image_path}_debug_page.png"
            driver.save_screenshot(debug_screenshot)
            raise Exception("Could not find file upload button on Google Translate page")
        
        # Upload the image
        upload_button.send_keys(image_path)
        
        # Wait for upload and translation to complete
        time.sleep(3)  # Initial wait for upload
        
        # Wait for any loading indicators to disappear
        try:
            WebDriverWait(driver, 10).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, [data-test-id='loading'], .spinner"))
            )
        except:
            pass  # Loading indicator might not be present
        
        # Additional wait for translation processing
        time.sleep(5)
        
        # Take a screenshot of the result area
        screenshot_path = f"{image_path}_translated.png"
        driver.save_screenshot(screenshot_path)
        
        return screenshot_path, None
            
    except Exception as e:
        import traceback
        error_msg = f"Error translating image: {str(e)}"
        full_traceback = traceback.format_exc()
        st.error(error_msg)
        st.error(f"Full error details: {full_traceback}")
        return None, None
    finally:
        try:
            driver.quit()
        except:
            pass

def create_download_link(file_paths, filename="translated_images.zip"):
    """Create a download link for multiple files as a zip"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, file_path in enumerate(file_paths):
            if file_path and os.path.exists(file_path):
                zip_file.write(file_path, f"translated_image_{i+1}.png")
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def main():
    st.set_page_config(
        page_title="Image Translator",
        page_icon="🌐",
        layout="wide"
    )
    
    st.title("🌐 Image Translator using Google Translate")
    st.markdown("Upload images to translate text within them using Google Translate's image translation feature.")
    
    # Language selection
    col1, col2 = st.columns(2)
    
    with col1:
        source_lang = st.selectbox(
            "Source Language",
            options=[
                ("auto", "Auto-detect"),
                ("en", "English"),
                ("es", "Spanish"),
                ("fr", "French"),
                ("de", "German"),
                ("it", "Italian"),
                ("pt", "Portuguese"),
                ("ru", "Russian"),
                ("ja", "Japanese"),
                ("ko", "Korean"),
                ("zh", "Chinese"),
                ("ar", "Arabic"),
                ("hi", "Hindi")
            ],
            format_func=lambda x: x[1],
            index=0
        )[0]
    
    with col2:
        target_lang = st.selectbox(
            "Target Language",
            options=[
                ("en", "English"),
                ("es", "Spanish"),
                ("fr", "French"),
                ("de", "German"),
                ("it", "Italian"),
                ("pt", "Portuguese"),
                ("ru", "Russian"),
                ("ja", "Japanese"),
                ("ko", "Korean"),
                ("zh", "Chinese"),
                ("ar", "Arabic"),
                ("hi", "Hindi")
            ],
            format_func=lambda x: x[1],
            index=0
        )[0]
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose image files to translate",
        type=['png', 'jpg', 'jpeg', 'jfif', 'gif', 'bmp', 'webp'],
        accept_multiple_files=True,
        help="Upload one or more images containing text you want to translate"
    )
    
    if uploaded_files:
        st.subheader(f"📁 {len(uploaded_files)} image(s) uploaded")
        
        # Show uploaded images
        cols = st.columns(min(len(uploaded_files), 3))
        for i, uploaded_file in enumerate(uploaded_files):
            with cols[i % 3]:
                image = Image.open(uploaded_file)
                st.image(image, caption=uploaded_file.name, width='stretch')
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 Translate All Images", type="primary"):
                st.session_state.start_translation = True
        with col2:
            if st.button("🧪 Test Browser Setup", type="secondary"):
                st.session_state.test_browser = True
        
        # Test browser functionality
        if st.session_state.get("test_browser", False):
            st.session_state.test_browser = False
            with st.spinner("Testing browser setup..."):
                try:
                    driver = setup_chrome_driver()
                    driver.get("https://www.google.com")
                    st.success("✅ Browser setup is working correctly!")
                    driver.quit()
                except Exception as e:
                    import traceback
                    st.error(f"❌ Browser test failed: {str(e)}")
                    st.error(f"Details: {traceback.format_exc()}")
        
        if st.session_state.get("start_translation", False):
            st.session_state.start_translation = False
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            translated_files = []
            
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {uploaded_file.name}... ({i+1}/{len(uploaded_files)})")
                    
                    # Save uploaded file to temporary location
                    temp_image_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_image_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Translate the image
                    try:
                        translated_path, img_url = translate_image_with_google(
                            temp_image_path, source_lang, target_lang
                        )
                        
                        if translated_path:
                            translated_files.append(translated_path)
                        
                    except Exception as e:
                        st.error(f"Failed to translate {uploaded_file.name}: {str(e)}")
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    time.sleep(1)  # Small delay to avoid overwhelming Google Translate
                
                status_text.text("Translation completed!")
                
                # Display results
                if translated_files:
                    st.subheader("🎯 Translation Results")
                    
                    result_cols = st.columns(min(len(translated_files), 3))
                    for i, translated_file in enumerate(translated_files):
                        with result_cols[i % 3]:
                            if os.path.exists(translated_file):
                                st.image(translated_file, 
                                        caption=f"Translated: {uploaded_files[i].name}",
                                        width='stretch')
                    
                    # Create download link
                    zip_data = create_download_link(translated_files)
                    st.download_button(
                        label="📥 Download All Translated Images",
                        data=zip_data,
                        file_name="translated_images.zip",
                        mime="application/zip"
                    )
                else:
                    st.warning("No images were successfully translated. Please try again.")
    
    # Instructions
    with st.expander("ℹ️ How to use this app"):
        st.markdown("""
        1. **Select Languages**: Choose your source language (or auto-detect) and target language
        2. **Upload Images**: Select one or more images containing text you want to translate
        3. **Translate**: Click the "Translate All Images" button to process your images
        4. **Download**: Once translation is complete, download your translated images as a zip file
        
        **Note**: This app uses Google Translate's image translation feature through web automation. 
        The process may take a few moments per image, so please be patient.
        
        **Supported formats**: PNG, JPG, JPEG, JFIF, GIF, BMP, WebP
        """)

if __name__ == "__main__":
    main()