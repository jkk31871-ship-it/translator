# Overview

This is a Streamlit-based web application that provides image translation services using Google Translate's image translation feature. The application leverages Selenium WebDriver to automate browser interactions with Google Translate, allowing users to upload images containing text in various languages and receive translations. The system is designed to run in cloud environments like Replit with proper headless browser configuration.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit for rapid web application development
- **User Interface**: Simple file upload interface for image processing
- **Image Handling**: PIL (Python Imaging Library) for image processing and manipulation

## Backend Architecture
- **Web Automation**: Selenium WebDriver for browser automation
- **Browser Engine**: Chromium/Chrome in headless mode for server compatibility
- **Driver Management**: WebDriverManager for automatic ChromeDriver installation and management
- **File Processing**: Temporary file handling for uploaded images using Python's tempfile module

## Browser Configuration
- **Headless Operation**: Chrome configured for server environments without display
- **Security Settings**: Disabled web security and sandbox mode for cloud deployment
- **Performance Optimization**: Disabled GPU acceleration, extensions, and logging for resource efficiency
- **Replit Compatibility**: Custom binary location pointing to Nix store Chromium installation

## Translation Service Integration
- **Service Provider**: Google Translate web interface automation
- **Language Support**: Automatic source language detection with configurable target languages
- **Image Processing**: Direct image upload to Google Translate's image translation feature

## File Management
- **Upload Handling**: Streamlit's native file upload capabilities
- **Temporary Storage**: Secure temporary file creation for processing
- **Archive Support**: ZIP file handling capabilities for batch processing

# External Dependencies

## Core Libraries
- **streamlit**: Web application framework
- **selenium**: Browser automation for Google Translate interaction
- **PIL (Pillow)**: Image processing and manipulation
- **webdriver-manager**: Automatic ChromeDriver management

## Browser Dependencies
- **Chromium**: Primary browser engine for automation
- **ChromeDriver**: WebDriver for Chrome/Chromium automation

## Google Services
- **Google Translate**: Image translation service accessed via web interface automation
- **translate.google.com**: Primary service endpoint for translation functionality

## System Dependencies
- **Nix Store**: Package management system for Replit environment
- **Chrome/Chromium Binary**: Browser executable for headless operation