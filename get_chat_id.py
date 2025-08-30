#!/usr/bin/env python3
"""Get Telegram chat ID helper script"""
import asyncio
import aiohttp
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def get_chat_id():
    """Get chat ID from recent updates"""
    print("Getting Telegram Chat ID")
    print("=" * 30)
    
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in .env file!")
        return
    
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN}")
    print()
    
    print("Instructions:")
    print("1. Open Telegram and search for @Pine_fix_bot")
    print("2. Start a conversation with the bot")
    print("3. Send any message (like '/start' or 'hello')")
    print("4. Run this script to get your chat ID")
    print()
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get updates to find chat IDs
            url = f"{base_url}/getUpdates"
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                
                if not result.get('ok'):
                    print(f"Error: {result.get('description')}")
                    return
                
                updates = result.get('result', [])
                
                if not updates:
                    print("No messages found!")
                    print("Please send a message to @Pine_fix_bot on Telegram first.")
                    return
                
                print("Recent chats:")
                print("-" * 20)
                
                chat_ids = set()
                for update in updates[-10:]:  # Show last 10 updates
                    if 'message' in update:
                        message = update['message']
                        chat = message.get('chat', {})
                        user = message.get('from', {})
                        
                        chat_id = chat.get('id')
                        chat_type = chat.get('type', 'unknown')
                        chat_title = chat.get('title', chat.get('first_name', 'Unknown'))
                        username = user.get('username', 'No username')
                        text = message.get('text', 'No text')[:50]
                        
                        chat_ids.add(chat_id)
                        
                        print(f"Chat ID: {chat_id}")
                        print(f"Type: {chat_type}")
                        print(f"Name/Title: {chat_title}")
                        print(f"Username: @{username}")
                        print(f"Message: {text}")
                        print("-" * 20)
                
                if chat_ids:
                    print("\nTo use one of these chat IDs:")
                    print("Update your .env file with:")
                    for chat_id in chat_ids:
                        print(f"TELEGRAM_CHAT_ID={chat_id}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_chat_id())