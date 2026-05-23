import os
from dotenv import load_dotenv
import logging
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.error import BadRequest


import x_agent

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def cutStrings(start: int, end: int , string : str ):
    subString: str = ""
    # index : int = 0

    for index in range(start, end):
        if index >= start and index <= end:
            subString+= string[index]
        if index> end:
            break
    return subString



def splitMessage(message : str) -> list:
    splitCounter= 2
    returningStrings = []
    messageCheckpoints = set()
    messageCheckpoints.add(0)
    prevCheckpoint = 0
    tempStr=""

    if len(message) > 4000:
        while( int(len(message)/splitCounter) > 4000):
            splitCounter+=1

        div = int(len(message) / splitCounter)
        for i in range(1,splitCounter+1):
            if i == splitCounter:
                messageCheckpoints.add( int (len(message) ))
                break
            messageCheckpoints.add(prevCheckpoint + div)
            prevCheckpoint = prevCheckpoint + div

        messageCheckpoints = sorted(messageCheckpoints)
        print(messageCheckpoints)

        prevCheckpoint= 0
        for checkpoint in messageCheckpoints:
            if checkpoint== 0:
                continue
            returningStrings.append(cutStrings(prevCheckpoint, checkpoint, message))
            prevCheckpoint = checkpoint

        return returningStrings

    else:
        returningStrings.append(message)

    return returningStrings

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Report handles that handles the call of the x_agent() and the return of the messages
    '''
    async def send_message(chat_id, msg , message_thread_id= None):
        '''
        Sends a message via the Python Telegram Bot package to telegram
        Args:
            chat_id : str
            msg: str
            message_thread_id: str or None
        '''
        if not update.message.direct_messages_topic:
            await context.bot.send_message(
                chat_id = chat_id,
                text = msg,
            )
        else :
            await context.bot.send_message(
                chat_id = chat_id,
                text = msg,
                message_thread_id = message_thread_id,
            )
        return

    responseMD:str = ''

    try:
        await send_message(
            chat_id = update.effective_chat.id,
            msg = "Generating a report... This might take a while",
            message_thread_id= None if not update.message.reply_to_message.message_thread_id else update.message.reply_to_message.message_thread_id
        )
        responseMD = await x_agent.x_agent()
        if responseMD == None:
            raise Exception("Something went wrong with the agent...")
    except Exception as e:
        print(f'Error : {e}')
        await send_message(
            chat_id = update.effective_chat.id,
            msg = "Sorry , something went wrong with the agent...",
            message_thread_id = update.message.reply_to_message.message_thread_id,
        )

    if not update.message.direct_messages_topic:       # if this was posted in a thread or topic , post it there too
        fighterMessages = splitMessage(responseMD['fighters'])
        for msg in fighterMessages:
            await context.bot.send_message(
                chat_id = update.effective_chat.id,
                text = msg,
                # parse_mode= 'Markdown'
            )

        eventMessages = splitMessage(responseMD['events'])
        for msg in eventMessages:
            await context.bot.send_message(
                chat_id = update.effective_chat.id,
                text = msg,
                # parse_mode= 'Markdown'
            )

    else :
        fighterMessages = splitMessage(responseMD['fighters'])
        for msg in fighterMessages:
            try:
                await context.bot.send_message(
                    chat_id = update.effective_chat.id,
                    text = msg,
                    parse_mode= 'Markdown'
                )
            except BadRequest as e:
                print(e)
                await context.bot.send_message(
                    chat_id = update.effective_chat.id,
                    text = msg,
                )

        eventMessages = splitMessage(responseMD['events'])
        for msg in eventMessages:
            try:
                await context.bot.send_message(
                    chat_id = update.effective_chat.id,
                    text = msg,
                    parse_mode= 'Markdown'
                )
            except BadRequest as e :
                print(e)
                await context.bot.send_message(
                    chat_id = update.effective_chat.id,
                    text = msg,
                )
    return




if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN") or "").build()

    report_handler = CommandHandler('report', report)
    application.add_handler(report_handler)

    application.run_polling()
