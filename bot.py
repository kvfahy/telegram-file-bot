"""
Simple Telegram File Sharing Bot
No database required - uses message IDs for file tracking
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os
import base64

# Configuration from environment variables
API_ID = int(os.environ.get("APP_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Initialize bot
app = Client(
    "file_sharing_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4
)

def encode_id(msg_id):
    """Encode message ID to base64 for shareable links"""
    return base64.urlsafe_b64encode(str(msg_id).encode()).decode().strip("=")

def decode_id(encoded_id):
    """Decode base64 to message ID"""
    try:
        # Add padding if needed
        padding = 4 - (len(encoded_id) % 4)
        if padding != 4:
            encoded_id += "=" * padding
        return int(base64.urlsafe_b64decode(encoded_id).decode())
    except:
        return None

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    """Handle /start command and file retrieval"""
    
    # Check if this is a file retrieval request
    if len(message.text.split()) > 1:
        encoded_id = message.text.split()[1]
        msg_id = decode_id(encoded_id)
        
        if msg_id:
            try:
                # Get file from channel
                file_msg = await client.get_messages(CHANNEL_ID, msg_id)
                
                if file_msg and file_msg.media:
                    # Send file to user
                    await file_msg.copy(message.chat.id)
                    await message.reply_text("✅ Here's your file!")
                else:
                    await message.reply_text("❌ File not found or expired.")
            except Exception as e:
                print(f"Error retrieving file: {e}")
                await message.reply_text("❌ Error retrieving file. Please try again.")
        else:
            await message.reply_text("❌ Invalid link!")
    else:
        # Welcome message
        await message.reply_text(
            f"👋 Hello {message.from_user.first_name}!\n\n"
            "📤 **How to use:**\n"
            "1. Send me any file\n"
            "2. I'll give you a shareable link\n"
            "3. Share the link with anyone\n"
            "4. They can download the file instantly!\n\n"
            "⚡ Fast, simple, and free!"
        )

@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def handle_file(client, message: Message):
    """Handle incoming files and generate shareable links"""
    
    # Check if user is owner (optional - remove this to allow all users)
    # if message.from_user.id != OWNER_ID:
    #     await message.reply_text("❌ Only bot owner can upload files!")
    #     return
    
    try:
        # Forward file to storage channel
        status_msg = await message.reply_text("⏳ Processing your file...")
        
        forwarded = await message.copy(CHANNEL_ID)
        
        # Generate shareable link
        encoded_id = encode_id(forwarded.id)
        bot_username = (await client.get_me()).username
        share_link = f"https://t.me/{bot_username}?start={encoded_id}"
        
        # Get file info
        file_name = "File"
        file_size = 0
        
        if message.document:
            file_name = message.document.file_name or "Document"
            file_size = message.document.file_size
        elif message.video:
            file_name = message.video.file_name or "Video"
            file_size = message.video.file_size
        elif message.audio:
            file_name = message.audio.file_name or "Audio"
            file_size = message.audio.file_size
        elif message.photo:
            file_name = "Photo"
            file_size = message.photo.file_size
        
        # Format file size
        size_mb = file_size / (1024 * 1024)
        if size_mb < 1:
            size_str = f"{file_size / 1024:.2f} KB"
        elif size_mb < 1024:
            size_str = f"{size_mb:.2f} MB"
        else:
            size_str = f"{size_mb / 1024:.2f} GB"
        
        # Send response with link
        await status_msg.edit_text(
            f"✅ **File Ready!**\n\n"
            f"📄 **Name:** `{file_name}`\n"
            f"📦 **Size:** {size_str}\n\n"
            f"🔗 **Shareable Link:**\n`{share_link}`\n\n"
            f"👆 Click the link above or share it with others!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Download", url=share_link)]
            ])
        )
        
        print(f"File shared: {file_name} ({size_str}) - ID: {forwarded.id}")
        
    except Exception as e:
        print(f"Error handling file: {e}")
        await message.reply_text(f"❌ Error processing file: {str(e)}")

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_command(client, message: Message):
    """Show bot statistics (owner only)"""
    try:
        me = await client.get_me()
        await message.reply_text(
            f"📊 **Bot Statistics**\n\n"
            f"🤖 **Bot:** @{me.username}\n"
            f"💾 **Storage Channel:** `{CHANNEL_ID}`\n"
            f"👤 **Owner:** `{OWNER_ID}`\n\n"
            f"✅ Bot is running smoothly!"
        )
    except Exception as e:
        await message.reply_text(f"Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting File Sharing Bot...")
    print(f"📱 Bot Token: {BOT_TOKEN[:20]}...")
    print(f"💾 Storage Channel: {CHANNEL_ID}")
    print(f"👤 Owner: {OWNER_ID}")
    print("🔄 Starting polling mode...")
    
    try:
        app.run()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
