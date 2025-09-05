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
import requests
import urllib.parse

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
        # Navigate to Google Translate image translation with explicit parameters
        url = f"https://translate.google.com/?sl={source_lang}&tl={target_lang}&op=images"
        st.info(f"🌐 Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load completely
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Extra wait and check if we're on the right page
        time.sleep(4)
        
        # Verify we're on the image translation page
        current_url = driver.current_url
        page_title = driver.title
        st.info(f"📍 Current page: {page_title}")
        
        if "translate" not in current_url.lower():
            st.error("❌ Failed to navigate to Google Translate properly")
            raise Exception("Not on Google Translate page")
        
        # Check if Images tab is selected
        try:
            images_tab = driver.find_element(By.XPATH, "//div[contains(text(), 'Images') or contains(text(), 'images')]")
            if images_tab:
                st.info("✅ Images tab found - clicking to ensure it's selected")
                driver.execute_script("arguments[0].click();", images_tab)
                time.sleep(2)
        except:
            st.info("ℹ️ Images tab not found or already selected")
        
        # First try to click the "Browse your files" button if it exists
        try:
            browse_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Browse your files') or contains(text(), 'browse')]")
            if browse_button.is_displayed():
                st.info("🔍 Found 'Browse your files' button - clicking it")
                driver.execute_script("arguments[0].click();", browse_button)
                time.sleep(1)
        except:
            st.info("ℹ️ No 'Browse your files' button found")
        
        # Find the file upload input element
        upload_selectors = [
            "input[type='file'][accept*='image']",
            "input[type='file']",
            "[data-test-id='file-upload'] input",
            ".VfPpkd-Bz112c input[type='file']"
        ]
        
        upload_element = None
        for selector in upload_selectors:
            try:
                upload_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in upload_elements:
                    # Make sure it's visible or at least present
                    if element.is_enabled():
                        upload_element = element
                        st.info(f"✅ Found upload element using selector: {selector}")
                        break
                if upload_element:
                    break
            except:
                continue
        
        if not upload_element:
            st.error("❌ Could not find any file upload element")
            # Try to take a screenshot for debugging
            debug_screenshot = f"{image_path}_debug_upload_page.png"
            driver.save_screenshot(debug_screenshot)
            raise Exception("Could not find file upload element")
        
        # Upload the image
        st.info(f"📤 Uploading image: {image_path}")
        upload_element.send_keys(image_path)
        st.info("✅ File upload command sent")
        
        # Wait for upload confirmation and then for translation
        time.sleep(3)  # Wait for upload
        
        # Wait for the page to change after upload - look for actual content changes
        max_wait_for_translation = 25
        translation_completed = False
        
        for attempt in range(max_wait_for_translation):
            try:
                # Look for specific translation UI elements that appear after successful translation
                translation_indicators = [
                    "//button[contains(text(), 'Download translation')]",
                    "//button[contains(text(), 'Copy text')]",
                    "//*[contains(text(), 'Detected language')]",
                    "//*[contains(@aria-label, 'Download')]",
                    "//*[contains(@aria-label, 'Copy')]"
                ]
                
                found_indicator = False
                for indicator_xpath in translation_indicators:
                    try:
                        elements = driver.find_elements(By.XPATH, indicator_xpath)
                        if elements and any(elem.is_displayed() for elem in elements):
                            translation_completed = True
                            found_indicator = True
                            st.success(f"✅ Translation UI detected after {attempt + 1} seconds using: {indicator_xpath}")
                            break
                    except:
                        continue
                
                if found_indicator:
                    break
                
                # Also check if page URL changed (sometimes happens after successful upload)
                current_url = driver.current_url
                if "blob:" in current_url or len(current_url) > 100:
                    st.info(f"📍 Page URL changed - possible translation: {current_url[:100]}...")
                    
                time.sleep(1)
            except Exception as e:
                st.warning(f"Error checking translation status: {str(e)}")
                time.sleep(1)
                
        if not translation_completed:
            # Check if Google Translate shows "No text found" or similar messages
            page_source = driver.page_source.lower()
            
            if "no text found" in page_source or "no text" in page_source:
                st.error("❌ Google Translate reports: 'No text found' in the image")
                st.info("💡 Suggestions to fix this:")
                st.info("• Try an image with clearer, larger text")
                st.info("• Ensure the text has good contrast with the background")
                st.info("• Use images with horizontal text (not rotated)")
                st.info("• Try a different image format or higher resolution")
            elif "not supported" in page_source:
                st.error("❌ Image format not supported by Google Translate")
            else:
                st.error("❌ Translation failed - Google Translate couldn't process this image")
                st.info("🔄 This could mean the image format isn't supported or the text wasn't detected")
        
        # Additional wait for any remaining processing
        time.sleep(3)
        
        # Look for the translated image and download it directly
        translated_image_path = None
        
        try:
            # Look for all images on the page and find the translated one
            all_imgs = driver.find_elements(By.TAG_NAME, "img")
            
            translated_img = None
            original_img_src = None
            
            # First, identify the original image to avoid selecting it
            for img in all_imgs:
                try:
                    src = img.get_attribute('src')
                    # Skip if it's an icon or very small image
                    if img.size['width'] < 100 or img.size['height'] < 100:
                        continue
                    # This might be the original uploaded image
                    if src and ('blob:' in src or 'data:image' in src):
                        # Check if this is in the input area (left side)
                        location = img.location
                        if location['x'] < driver.get_window_size()['width'] / 2:
                            original_img_src = src
                except:
                    continue
            
            # Now find the translated image (should be on the right side or different from original)
            for img in all_imgs:
                try:
                    src = img.get_attribute('src')
                    
                    # Skip small images
                    if img.size['width'] < 100 or img.size['height'] < 100:
                        continue
                    
                    # Skip if it's the same as original
                    if src == original_img_src:
                        continue
                        
                    # Look for images that are likely the translation result
                    location = img.location
                    window_width = driver.get_window_size()['width']
                    
                    # Prefer images on the right side of the screen (translation result area)
                    if location['x'] > window_width / 2:
                        translated_img = img
                        break
                    
                    # Or images with translation-related attributes
                    if (src and ('googleusercontent.com' in src or 'translate' in src) and 
                        src != original_img_src):
                        translated_img = img
                        break
                        
                except:
                    continue
            
            # Fallback: get the last significant image that's not the original
            if not translated_img:
                for img in reversed(all_imgs):
                    try:
                        src = img.get_attribute('src')
                        if (img.size['width'] > 100 and img.size['height'] > 100 and 
                            src != original_img_src and src):
                            translated_img = img
                            break
                    except:
                        continue
            
            if translated_img:
                # Get the source URL of the translated image
                img_src = translated_img.get_attribute('src')
                st.info(f"Found translated image with source: {img_src[:50]}..." if img_src else "No source found")
                
                if img_src:
                    # Handle blob URLs by getting image data directly from browser
                    try:
                        # Always use the canvas method for better quality
                        script = """
                        var img = arguments[0];
                        var canvas = document.createElement('canvas');
                        var ctx = canvas.getContext('2d');
                        canvas.width = img.naturalWidth || img.width;
                        canvas.height = img.naturalHeight || img.height;
                        ctx.drawImage(img, 0, 0);
                        return canvas.toDataURL('image/png');
                        """
                        
                        base64_data = driver.execute_script(script, translated_img)
                        
                        if base64_data and base64_data.startswith('data:image'):
                            # Remove the data URL prefix
                            image_data = base64_data.split(',')[1]
                            
                            # Decode base64 and save
                            import base64
                            translated_image_path = f"{image_path}_translated.png"
                            with open(translated_image_path, 'wb') as f:
                                f.write(base64.b64decode(image_data))
                            
                            st.success("✅ Successfully extracted high-quality translated image using canvas method!")
                        else:
                            raise Exception("Canvas method failed - no valid image data returned")
                        
                    except Exception as download_error:
                        st.error(f"❌ Canvas extraction failed: {str(download_error)}")
                        # Try element screenshot as fallback
                        try:
                            translated_image_path = f"{image_path}_translated.png"
                            translated_img.screenshot(translated_image_path)
                            st.warning("⚠️ Used element screenshot fallback - quality may be reduced")
                        except Exception as screenshot_error:
                            st.error(f"Element screenshot also failed: {str(screenshot_error)}")
                            # Final fallback to full screenshot
                            translated_image_path = f"{image_path}_translated.png"
                            driver.save_screenshot(translated_image_path)
                            st.warning("⚠️ Used full page screenshot as final fallback")
                else:
                    st.error("No image source URL found")
                    # Fallback to full screenshot
                    translated_image_path = f"{image_path}_translated.png"
                    driver.save_screenshot(translated_image_path)
            
            else:
                st.error("❌ No translated image found on the page")
                
        except Exception as e:
            st.error(f"❌ Error during image extraction: {str(e)}")
            
        # Fallback to regular screenshot if everything else failed
        if not translated_image_path:
            st.warning("⚠️ Using full page screenshot as final fallback")
            translated_image_path = f"{image_path}_translated.png"
            driver.save_screenshot(translated_image_path)
        
        return translated_image_path, None
            
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
            translation_results = []
            
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
                        translated_path, translated_text = translate_image_with_google(
                            temp_image_path, source_lang, target_lang
                        )
                        
                        if translated_path or translated_text:
                            translated_files.append(translated_path)
                            translation_results.append({
                                'original_name': uploaded_file.name,
                                'translated_path': translated_path,
                                'translated_text': translated_text
                            })
                        
                    except Exception as e:
                        st.error(f"Failed to translate {uploaded_file.name}: {str(e)}")
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    time.sleep(1)  # Small delay to avoid overwhelming Google Translate
                
                status_text.text("Translation completed!")
                
                # Display results
                if translation_results:
                    st.subheader("🎯 Translation Results")
                    
                    for i, result in enumerate(translation_results):
                        st.markdown(f"### 📄 {result['original_name']}")
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.markdown("**Original Image:**")
                            original_image = Image.open(uploaded_files[i])
                            st.image(original_image, width=300)
                        
                        with col2:
                            st.markdown("**Translated Image:**")
                            if result['translated_path'] and os.path.exists(result['translated_path']):
                                st.image(result['translated_path'], width=300)
                            else:
                                st.error("Translation failed for this image")
                        
                        st.markdown("---")
                    
                    # Download translated images
                    if any(result['translated_path'] for result in translation_results):
                        valid_files = [result['translated_path'] for result in translation_results if result['translated_path'] and os.path.exists(result['translated_path'])]
                        if valid_files:
                            zip_data = create_download_link(valid_files)
                            st.download_button(
                                label="📥 Download All Translated Images",
                                data=zip_data,
                                file_name="translated_images.zip",
                                mime="application/zip",
                                type="primary"
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