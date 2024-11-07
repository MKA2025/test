import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from orpheus.core import Orpheus, DownloadTypeEnum, MediaIdentification
from orpheus.music_downloader import beauty_format_seconds

# Logging ကို setup လုပ်ပါမယ်
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = 'YOUR_BOT_TOKEN_HERE'

# OrpheusDL instance
orpheus = Orpheus()

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('OrpheusDL Bot ကို ကြိုဆိုပါတယ်! သီချင်း link တစ်ခုခု ပို့ပေးပါ သို့မဟုတ် /search command သုံးပြီး ရှာဖွေနိုင်ပါတယ်။')

def handle_link(update: Update, context: CallbackContext) -> None:
    link = update.message.text
    try:
        update.message.reply_text('သီချင်းကို download လုပ်နေပါတယ်...')
        
        # OrpheusDL ကို သုံးပြီး သီချင်းကို download လုပ်ပါမယ်
        orpheus.orpheus_core_download({orpheus.service_name: [MediaIdentification(media_type=DownloadTypeEnum.track, media_id=link)]}, {}, 'default', './downloads')
        
        # Download လုပ်ပြီးသား ဖိုင်ကို ရှာပြီး user ဆီ ပို့ပေးပါမယ်
        for root, dirs, files in os.walk('./downloads'):
            for file in files:
                if file.endswith('.mp3') or file.endswith('.flac'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'rb') as audio_file:
                        update.message.reply_audio(audio_file)
                    os.remove(file_path)  # ဖိုင်ကို ပို့ပြီးရင် ဖျက်ပစ်ပါမယ်
                    return
        
        update.message.reply_text('သီချင်း download လုပ်တာ မအောင်မြင်ပါ။')
    except Exception as e:
        logger.error(f"Error downloading: {str(e)}")
        update.message.reply_text(f'အမှား တစ်ခုဖြစ်သွားပါတယ်: {str(e)}')

def search(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text('ကျေးဇူးပြု၍ ရှာဖွေလိုသော သီချင်းအမည်ကို ထည့်သွင်းပါ။ ဥပမာ - /search Wonderwall')
        return

    query = ' '.join(context.args)
    try:
        # OrpheusDL ကို သုံးပြီး ရှာဖွေပါမယ်
        results = orpheus.module.search(DownloadTypeEnum.track, query, limit=5)
        
        if not results:
            update.message.reply_text('ရှာဖွေမှု ရလဒ် မတွေ့ရှိပါ။')
            return

        keyboard = []
        for i, item in enumerate(results):
            text = f"{item.name} - {', '.join(item.artists)} [{beauty_format_seconds(item.duration)}]"
            callback_data = f"download_{item.result_id}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('ရှာဖွေမှု ရလဒ်များ:', reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        update.message.reply_text(f'ရှာဖွေရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့သည်: {str(e)}')

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data.startswith("download_"):
        track_id = query.data.split("_")[1]
        query.edit_message_text(text=f"သီချင်းကို download လုပ်နေပါတယ်...")

        try:
            # OrpheusDL ကို သုံးပြီး သီချင်းကို download လုပ်ပါမယ်
            orpheus.orpheus_core_download({orpheus.service_name: [MediaIdentification(media_type=DownloadTypeEnum.track, media_id=track_id)]}, {}, 'default', './downloads')
            
            # Download လုပ်ပြီးသား ဖိုင်ကို ရှာပြီး user ဆီ ပို့ပေးပါမယ်
            for root, dirs, files in os.walk('./downloads'):
                for file in files:
                    if file.endswith('.mp3') or file.endswith('.flac'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'rb') as audio_file:
                            query.message.reply_audio(audio_file)
                        os.remove(file_path)  # ဖိုင်ကို ပို့ပြီးရင် ဖျက်ပစ်ပါမယ်
                        return

            query.edit_message_text(text='သီချင်း download လုပ်တာ မအောင်မြင်ပါ။')
        except Exception as e:
            logger.error(f"Error downloading from button: {str(e)}")
            query.edit_message_text(text=f'အမှား တစ်ခုဖြစ်သွားပါတယ်: {str(e)}')

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("search", search))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    updater.start_polling()
    updater.
