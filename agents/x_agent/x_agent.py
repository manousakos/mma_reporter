import json
from typing import Literal
from dotenv import load_dotenv
from pydantic_ai.models import Model
import requests
import datetime
import os
import time
from pydantic_ai import Agent , ModelSettings, UnexpectedModelBehavior, settings


from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.ollama import OllamaModel

from report import *
from logger  import logger


load_dotenv()





x_accounts = [
    "danawhite",
    "ChampRDS",
    "arielhelwani",
    "realkevink",
]

def getPostsById(id: str , cursor: str | None = None) -> tuple:
    """
    This is an RAPID api available at : https://rapidapi.com/alexanderxbx/api/twitter-api45/
    that allows to get all the recent posts from a given X id.
    This call returns the 19 most recent posts of a X user with ID: <id>, along with prev
    and next page pointers.

    Args:
        - id : str, the X id of profile
        - cursor : str , the "next_page" of the posts ( used by the RAPID API)
    Returns:
        - tuple :
            - dict : a dictionary that contains the output of the API Call
            - string : a cursor (next_page pointer) to the next page of 19 posts of the user

    The api follows the below structure:
        curl --request GET \
            --url 'https://twitter-api45.p.rapidapi.com/timeline.php?screenname=DovySimuMMA' \
            --header 'Content-Type: application/json' \
            --header 'x-rapidapi-host: twitter-api45.p.rapidapi.com' \
            --header 'x-rapidapi-key: 3279362f39msh18933dc9449f741p14d976jsn5f331005d583'
    """

    url = 'https://twitter-api45.p.rapidapi.com/timeline.php'
    headers = {
	    'Content-Type': 'application/json',
	    'x-rapidapi-host': 'twitter-api45.p.rapidapi.com',
	    'x-rapidapi-key':  os.getenv("RAPID_API_KEY")
    }
    params={
        'screenname': id,
    }

    if cursor != None:
        params['cursor'] = cursor

    response = requests.get(url, headers=headers, params= params)

    if response.ok:
        response = response.json()
        next_cursor = response["next_cursor"]
        return response, next_cursor

    else:
        print(f"Error: {response.status_code}")
        return None,None

def getTodaysPostsById(id) -> list:
    """
    Get all the X posts of a user with ID : <id> from withing a day from the time of the call.
    Args:
        - id : string, the X ID of the user
    Returns:
        - list(strings): a list of the texts of all the posts of a user from withing 24 hours
            from the time of the request
    """
    def transformDate(dt: str)-> datetime.datetime:
        """
        Transorms a "created_at" string to a datetime.datetime object
        Args:
            - dt : a string of a date
        Returns:
            - datetime.datetime
        """
        try:
            date_object = datetime.datetime.strptime(dt, '%a %b %d %H:%M:%S %z %Y')
        except Exception as e:
            print(e)
            print(f"Date : {dt}")
        return date_object

    dateNow= datetime.datetime.now(datetime.timezone.utc)
    postDate : datetime.datetime | None= None
    texts = []
    responseDict , cursor = getPostsById(id)
    print(f"Starting for id: {id}...")
    for post in responseDict['timeline']:
        texts.append(post["text"])
        if transformDate(post["created_at"]) == None:
            continue
        postDate= transformDate(post["created_at"])

    if(postDate):
        while (dateNow - postDate).days < 1 and cursor:
            print("Getting more posts...")
            responseDict, cursor = getPostsById(id, cursor)
            for post in responseDict['timeline']:
                postDate = transformDate(post["created_at"])
                if (dateNow - postDate).days < 1:
                    texts.append(post["text"])
                else:
                    break

    return texts

def createPostList(account_ids: list):
    texts : list= []
    counter = 0

    for account_id in account_ids:
        while counter< 3:
            try:
                response_texts = getTodaysPostsById(account_id)
                texts.append(response_texts)
                break
            except Exception as e:
                print(f"For id : {account_id} ,times : {counter+1}\nException {e} ")
                counter += 1
                continue
        counter = 0

    return texts


def createAgent(modelType : Literal['mistral', 'ollama'] = 'mistral')-> Agent:
    '''
    Simple Pydantic agent that returns a text output
    '''
    try:

        sysPrompt: str=""
        with open("./prompts/reportAgentSPrompt.txt", "r") as fl:
            sysPrompt= fl.read()

        model : Model
        if modelType == "ollama":
            model = OllamaModel(
                model_name=os.getenv("OLLAMA_MODEL") or "ministral-3:8b",
                provider=OllamaProvider(base_url=os.getenv("OLLAMA_URL") or "http://localhost:11434/v1")
            )
        if modelType == "mistral":
            model = MistralModel(
                model_name =  os.getenv("MISTRAL_SMALL") or "mistral-small-latest",
                provider = MistralProvider(api_key=os.getenv("MISTRAL_API_KEY"))
            )
        agent = Agent(
            model= model,
            instructions= sysPrompt,
            model_settings= ModelSettings(temperature=0.2),
            retries=3
        )

        return agent

    except Exception as e:
        print(e)
        raise Exception(e)

def x_agent() -> dict:
    accounts: dict= {}
    logger.info("\033[91m[x-agent] Starting Generating Report\033[0m")
    with open("./accountsX.json" , "r") as fl:
        try:
            accounts = json.loads(fl.read())
        except Exception as e:
            print(f"Exception {e}")
    texts = createPostList(accounts["account_ids"])

    agent= createAgent(modelType = 'mistral')

    input = {
        "texts" : texts
    }
    
    finalReport = Report()
    output ={
        "fighters" : f"Report {finalReport.created_at}\n",
        "events" : f"Report {finalReport.created_at}\n"
    } 

    extractionSysPrompt = ''
    with open('./prompts/entitiesExtractionSysPrompt.txt', 'r') as fl:
        extractionSysPrompt = fl.read()

        if len(extractionSysPrompt) == 0:
            raise Exception("Could not load Entities Extraction System Prompt...")
    report =  agent.run_sync(
        user_prompt= "Below follow the posts: " + json.dumps(input) ,
        instructions=  extractionSysPrompt,
        output_type= ReportComponents
    )

    if len(report.output.fighters) >0:
        logger.info(f'[\033[91mx-agent] Found {len(report.output.fighters)}\033[0m')
    if len(report.output.events) >0:
        logger.info(f'[\033[91mx-agent] Found {len(report.output.events)}\033[0m')

    fighterPrompt = ''
    with open('./prompts/fighterReportsSysPrompt.txt', 'r') as fl:
        fighterPrompt = fl.read()
        if len(fighterPrompt) ==0:
            raise Exception("Could not load Fighter Reports System Prompt...")

    output['fighters'] += "`FIGHTS:`\n"

    logger.info("\033[91m[x-agent] Starting generating per Fighter Reports\033[0m")
    smallcounter =0

    time.sleep(5)
    for fighter in report.output.fighters:
        # if smallcounter == 5:
        #     break
        logger.info(f"\033[91m[x-agent] [Fighter] Generating report for fighter : {fighter.fullname} --- {smallcounter+1}/{len(report.output.fighters)}\033[0m")
        try:
            fighterReports = agent.run_sync(
                user_prompt= f"Fill the in information for the Fighter : {fighter.fullname} from the given posts. Below follow the posts: " + json.dumps(input),
                output_type= FighterReports,
                instructions=fighterPrompt
            )

            time.sleep(5)
            finalReport.fighters[fighter.fullname] = fighterReports.output.reports

            if len(fighterReports.output.reports)>0:
                output['fighters'] += f"*{fighter.fullname}*:\n"
                for smallReps in fighterReports.output.reports:
                    output['fighters']+= f"\t- {smallReps}\n"
        except UnexpectedModelBehavior as e:
            logger.info(f"[x-agent] Encountered Error: {e}")
            continue
        smallcounter+=1

        logger.info(f"\033[91m[x-agent] [Fighter] Completed report for fighter : {fighter.fullname} ✅\033[0m")

    eventPrompt=''
    with open('./prompts/eventReportsSysPrompt.txt', 'r') as fl:
        eventPrompt = fl.read()
        if len(eventPrompt) ==0:
            raise Exception("Could not load Event Reports System Prompt...")

    output['events'] += "`EVENTS:`\n"

    smallcounter = 0
    for event in report.output.events:
        logger.info(f"\033[91m[x-agent] [Event] Generating report for event : {event.name} --- {smallcounter+1}/{len(report.output.events)}\033[0m")
        try:
            eventReports =   agent.run_sync(
                user_prompt= f"Fill the in information for the event : {event.name} from the given posts. Below follow the posts: " + json.dumps(input),
                output_type= EventReports,
                instructions=eventPrompt
            )
            time.sleep(5)

            finalReport.events[event.name] = eventReports.output.reports

            if len(eventReports.output.reports)>0:
                output['events'] += f"*{event.name}*:\n"
                for smallReps in eventReports.output.reports:
                    output['events']+= f"\t- {smallReps}\n"
        except UnexpectedModelBehavior as e:
            logger.info(f"\n\n[x-agent] Encountered Error: {e}")
            continue
        smallcounter+=1
        logger.info(f"\033[91m[x-agent] [x-agent][Event] Completed report for event : {event.name} ✅\033[0m")

    logger.info("\033[91mReport Complete\033[0m")

    if output["events"] == None and output['fighters'] == None:
        return {
            "events" : "This is empty",
            "fighters": "This is empty"
        }
    

    # if output['fighters'] != None:
    #     output["fighters"] = output["fighters"].encode("utf-8").decode("unicode_escape")
    #     with open('./misc/fighterReport.txt' , 'w') as fl:
    #         fl.write(output['fighters'])
    #
    # if output['events'] != None:
    #     output["events"] = output["events"].encode("utf-8").decode("unicode_escape")
    #     with open('./misc/eventReport.txt' , 'w') as fl:
    #         fl.write(output['events'])


    with open('./misc/latestReport.txt', 'w') as fl:
        filestr = ''
        for text in output['fighters']:
            filestr += text
        for text in output['events']:
            filestr += text
        fl.write(filestr)
        
    return output

    return response.output

if __name__ == "__main__":
    x_agent()
