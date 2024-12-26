import telebot
import random
import requests
from io import BytesIO
from threading import Thread
import time

# Initialize the bot
BOT_TOKEN = "7899862299:AAFVk2TJVpPaJts0n-vV9ZyJ2uCKzDidoPY"
bot = telebot.TeleBot(BOT_TOKEN)

# Global dictionary to store the quantity per user
user_quantity = {}

# Default image quantity
DEFAULT_QUANTITY = 1

# Function to generate image URL with a random 10-digit seed
def generate_image_url(prompt: str = ""):
    base_url = "https://image.pollinations.ai/prompt/"
    seed = random.randint(1000000000, 9999999999)  # Random 10-digit seed
    full_url = f"{base_url}{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={seed}&nologo=true&model=flux-pro"
    return full_url

# Function to download image from URL with retry logic
def download_image(url, retries=3, timeout=30):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return BytesIO(response.content)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retrying
            else:
                raise e

# Function to handle image generation for multiple images
def process_image_request(chat_id, message_id, prompt, quantity):
    try:
        # Notify the user that images are being generated
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="🖌 Generating your images... Please wait a moment! 😊"
        )
        
        # Generate and download the specified number of images
        images = []
        for _ in range(quantity):
            image_url = generate_image_url(prompt)
            image_data = download_image(image_url)
            images.append(image_data)
        
        # Send the images to the user
        media_group = [telebot.types.InputMediaPhoto(image, caption=f"🌟 Image {_ + 1} for: {prompt}") for _, image in enumerate(images)]
        bot.send_media_group(chat_id, media=media_group)
    except requests.exceptions.Timeout:
        bot.send_message(chat_id, "❌ The image generation service took too long to respond. Please try again later.")
    except requests.exceptions.RequestException as e:
        bot.send_message(chat_id, f"❌ Failed to generate image due to a network error: {e}")
    finally:
        # Delete the "Please wait" message
        bot.delete_message(chat_id, message_id)

# Handler for the /img command
@bot.message_handler(commands=["img"])
def send_images(message):
    # Extract the prompt if provided
    text = message.text.strip()
    if len(text.split(maxsplit=1)) > 1:
        prompt = text.split(maxsplit=1)[1]
    else:
        # Send the Imgur-hosted image when no prompt is provided
        imgur_link = "https://imgur.com/a/2nNhKko"  # Replace with your Imgur link
        bot.send_photo(
            message.chat.id, 
            photo=imgur_link, 
            caption="⚠️ Use a prompt after /img command, noob! 😂\n\nExample: `.img a rolex watch`", 
            parse_mode="Markdown"
        )
        return
    
    # Get the user's preferred quantity or use the default
    quantity = user_quantity.get(message.chat.id, DEFAULT_QUANTITY)
    
    # Notify the user to wait
    wait_message = bot.reply_to(message, "⏳ Please wait while I generate your images...")
    
    # Process the image request in a separate thread to avoid blocking
    Thread(target=process_image_request, args=(message.chat.id, wait_message.message_id, prompt, quantity)).start()

# Handler for .img and !img commands (aliases)
@bot.message_handler(func=lambda message: message.text.startswith(('.img', '!img')))
def alias_commands(message):
    # Replace .img or !img with /img and call the /img handler
    message.text = message.text.replace('.img', '/img').replace('!img', '/img', 1)
    send_images(message)

# Handler for /quantity command
@bot.message_handler(commands=["quantity"])
def set_quantity(message):
    # Extract the desired quantity from the message
    text = message.text.strip()
    if len(text.split(maxsplit=1)) > 1:
        try:
            quantity = int(text.split(maxsplit=1)[1])
            if 1 <= quantity <= 5:
                user_quantity[message.chat.id] = quantity
                bot.reply_to(message, f"✅ Quantity set to {quantity} images per request.")
            else:
                bot.reply_to(message, "⚠️ Please choose a quantity between 1 and 5.")
        except ValueError:
            bot.reply_to(message, "⚠️ Please provide a valid number between 1 and 5.")
    else:
        bot.reply_to(message, "⚠️ Please specify a quantity. Example: `/quantity 3`",parse_mode="Markdown")

# Start the bot
print("Bot is running... 🚀")
bot.polling(non_stop=True)
