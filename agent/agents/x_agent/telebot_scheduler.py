from pydantic_ai import messages
import telebot
import os 
from dotenv import load_dotenv
import logging
from x_agent import x_agent
import time
import schedule
load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"), parse_mode="Markdown") # You can set parse_mode by default. HTML or MARKDOWN

def cutStrings(start: int, end: int , string : str ):
    subString: str = ""

    for index in range(start, end):
        if index >= start and index <= end:
            subString+= string[index]
        if index> end:
            break
    return subString



def splitMessage(message : str) -> list[str]:
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


@bot.message_handler(commands=['report'])
def report(message):
    '''
    Report handles that handles the call of the x_agent() and the return of the messages
    '''
    def send_message(chat_id: int, text: str, message_thread_id= None , parse_mode= None):
        '''
        Sends a message via the python Telebot package to telegram
        Args:
        '''

        if not message_thread_id:
            bot.send_message( 
                    chat_id= chat_id,
                    text= text,
                    parse_mode = None if not parse_mode else parse_mode
                )
        else:
            bot.send_message( 
                    chat_id= chat_id,
                    text= text,
                    message_thread_id= message_thread_id,
                    parse_mode = None if not parse_mode else parse_mode
                )
        return

    responseMD:str = ''
    msg_thread_id= None if not message.message_thread_id else message.message_thread_id
    chat_id: int = message.chat.id

    try:

        print(f"""
Here is : 

msg_thread_id = { msg_thread_id }
chat_id = { chat_id }
        """)
        return
        send_message(
            chat_id= chat_id,
            text = "Generating a report... This might take a while",
            message_thread_id= msg_thread_id
        )

        responseMD = x_agent()

        if responseMD == None:
            raise Exception("Something went wrong with the agent...")

        fighterMessages = splitMessage(responseMD['fighters'])

        for msg in fighterMessages:
            send_message(
                chat_id= chat_id,
                text = msg,
                message_thread_id= msg_thread_id,
                parse_mode= "Markdown"
            )

        eventMessages = splitMessage(responseMD['events'])
        for msg in eventMessages:
            send_message(
                chat_id= chat_id,
                text = msg,
                message_thread_id= msg_thread_id,
                parse_mode= "Markdown"
            )

    except Exception as e:
        print(f'Error : {e}')
        send_message(
            chat_id= chat_id,
            text = msg,
            message_thread_id= msg_thread_id,
        )


    return


def report_no_handler( chat_id=None , message_thread_id= None):
    '''
    Report handles that handles the call of the x_agent() and the return of the messages
    '''
    def send_message(chat_id: int, text: str, message_thread_id= None , parse_mode= None):
        '''
        Sends a message via the python Telebot package to telegram
        Args:
        '''

        if not message_thread_id:
            bot.send_message( 
                    chat_id= chat_id,
                    text= text,
                    parse_mode = None if not parse_mode else parse_mode
                )
        else:
            bot.send_message( 
                    chat_id= chat_id,
                    text= text,
                    message_thread_id= message_thread_id,
                    parse_mode = None if not parse_mode else parse_mode
                )
        return

    responseMD:str = ''
    # msg_thread_id= None if not message_thread_id else message_thread_id 
    msg_thread_id= os.getenv("BUSINNES_MEN_MSG_THREAD_ID")
    # chat_id: int = chat_id
    chat_id: int = os.getenv("BUSINNES_MEN_CHAT_ID")

    try:
        send_message(
            chat_id= chat_id,
            text = "Generating a report... This might take a while",
            message_thread_id= msg_thread_id
        )

        responseMD = x_agent()

        if responseMD == None:
            raise Exception("Something went wrong with the agent...")

        fighterMessages = splitMessage(responseMD['fighters'])

        for msg in fighterMessages:
            send_message(
                chat_id= chat_id,
                text = msg,
                message_thread_id= msg_thread_id,
                parse_mode= "Markdown"
            )

        eventMessages = splitMessage(responseMD['events'])
        for msg in eventMessages:
            send_message(
                chat_id= chat_id,
                text = msg,
                message_thread_id= msg_thread_id,
                parse_mode= "Markdown"
            )

    except Exception as e:
        print(f'Error : {e}')
        send_message(
            chat_id= chat_id,
            text = msg,
            message_thread_id= msg_thread_id,
        )


    return




if __name__== "__main__":
    # bot.infinity_polling()
    
    schedule.every().day.at("9:00").do(report_no_handler)

    while True:
        schedule.run_pending()
        time.sleep(1)

    # report_no_handler(os.getenv("PERSONAL_CHAT_ID"), message_thread_id=None)
    # report_no_handler(os.getenv("BUSINNES_MEN_CHAT_ID"), message_thread_id=os.getenv("BUSINNES_MEN_MSG_THREAD_ID"))
