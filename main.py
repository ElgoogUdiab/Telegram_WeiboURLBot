from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CallbackContext
from telegram.utils.helpers import escape_markdown

from uuid import uuid4
import logging
import convert

def inlinequery(update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query
    try:
        result = convert.convert(query)
        results = [
            InlineQueryResultArticle(
                id=uuid4(), title="转换成功！点这里", input_message_content=InputTextMessageContent(result)
            ),
        ]
    except:
        results = []

    update.inline_query.answer(results)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

if __name__ == "__main__":
    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get token and start
    try:
        with open("token") as f:
            token = f.readline().strip()
    except:
        print("No token! Create file named \"token\" under the same directory with main.py!")
        exit(1)
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    # Inline handler
    dispatcher.add_handler(InlineQueryHandler(inlinequery))

    # Error handler
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()
    updater.idle()
