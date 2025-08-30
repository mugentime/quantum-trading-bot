#!/usr/bin/env python3
"""Debug script for Telegram API"""
import asyncio
import aiohttp
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

async def debug_telegram():
    """Debug Telegram API connection"""
    print("Debug Telegram API")
    print("=" * 30)
    
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN}")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    print()
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Missing Telegram credentials!")
        return
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    # Test 1: Get bot info
    print("Test 1: Getting bot info...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{base_url}/getMe"
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                print(f"Response: {result}")
                
                if result.get('ok'):
                    bot_info = result.get('result', {})
                    print(f"Bot Name: {bot_info.get('first_name')}")
                    print(f"Bot Username: @{bot_info.get('username')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Test 2: Try to send a simple message
    print("Test 2: Sending test message...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{base_url}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": "Test message from debug script"
            }
            
            async with session.post(url, json=payload) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                print(f"Response: {result}")
                
                if not result.get('ok'):
                    error = result.get('description', 'Unknown error')
                    print(f"Error: {error}")
                    
                    # Common fixes
                    if 'chat not found' in error.lower():
                        print("\nSuggestion: The chat ID might be incorrect.")
                        print("Try using a numeric chat ID instead of @username")
                    elif 'bot was blocked' in error.lower():
                        print("\nSuggestion: The bot was blocked by the user/chat.")
                        print("Unblock the bot and try again.")
                    elif 'not enough rights' in error.lower():
                        print("\nSuggestion: The bot doesn't have permission to send messages.")
                        print("Add the bot as an admin or give it send message permissions.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_telegram())