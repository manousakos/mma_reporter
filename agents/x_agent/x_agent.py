# -------------------------------- IMPORTS --------------------------------
from dotenv import load_dotenv
load_dotenv()
import json
from pydantic_ai.capabilities.thinking import Thinking
from pydantic_ai.models import Model
import os
import time

from typing import Literal

from pydantic_ai import Agent , ModelSettings, UnexpectedModelBehavior
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.ollama import OllamaModel

from report import *
from logger  import logger
from xPostExtractor import createPostList




# -------------------------------- CODE --------------------------------
x_accounts = [
    "danawhite",
    "ChampRDS",
    "arielhelwani",
    "realkevink",
]



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
            model_settings= ModelSettings(
                temperature=0.2,
                thinking=  'high'
            ),
            retries=3
        )

        return agent

    except Exception as e:
        logger.error(e)
        raise Exception(e)


def generateFighterReports( smallcounter , report: Report , agent):
    fighterPrompt = ''
    with open('./prompts/fighterReportsSysPrompt.txt', 'r') as fl:
        fighterPrompt = fl.read()
        if len(fighterPrompt) ==0:
            raise Exception("Could not load Fighter Reports System Prompt...")

    for fighter in report.entities.fighters:
        logger.info(f"\033[91m[x-agent] [Fighter] Generating report for fighter : {fighter.fullname} --- {smallcounter+1}/{len(report.entities.fighters)}\033[0m")
        try:
            fighterReports = agent.run_sync(
                user_prompt= f"Fill the in information for the Fighter : {fighter.fullname} from the given posts. Below follow the posts: " + json.dumps(report.input )+ f"\n\nHere is the current generated report, use it to avoid duplicating, which you must not do: {json.dumps(report.output)}",
                output_type= FighterReports,
                instructions=fighterPrompt
            )

            time.sleep(int(os.getenv("LLM_CALL_TIMEOUT" or 10)))
            report.fighters[fighter.fullname] = fighterReports.output.reports
            print(f'Fighter reports exracted : {fighterReports.output.reports}')

        except UnexpectedModelBehavior as e:
            logger.info(f"[x-agent] Encountered Error: {e}")
            continue
        smallcounter+=1
        logger.info(f"\033[91m[x-agent] [Fighter] Completed report for fighter : {fighter.fullname} ✅\033[0m")
    return smallcounter , report

def generateEventReports(smallcounter , report: Report, agent):
    eventPrompt=''
    with open('./prompts/eventReportsSysPrompt.txt', 'r') as fl:
        eventPrompt = fl.read()
        if len(eventPrompt) ==0:
            raise Exception("Could not load Event Reports System Prompt...")

    for event in report.entities.events:
        logger.info(f"\033[91m[x-agent] [Event] Generating report for event : {event.name} --- {smallcounter+1}/{len(report.entities.events)}\033[0m")
        try:
            eventReports =   agent.run_sync(
                user_prompt= f"Fill the in information for the event : {event.name} from the given posts. Below follow the posts: " + json.dumps(report.input),
                output_type= EventReports,
                instructions=eventPrompt
            )
            time.sleep(int(os.getenv("LLM_CALL_TIMEOUT") or 10))

            report.events[event.name] = eventReports.output.reports

            if len(eventReports.output.reports)>0:
                report.output['events'] += f"*{event.name}*:\n"
                for smallReps in eventReports.output.reports:
                    report.output['events']+= f"\t- {smallReps}\n"
        except UnexpectedModelBehavior as e:
            logger.info(f"\n\n[x-agent] Encountered Error: {e}")
            continue
        smallcounter+=1
        logger.info(f"\033[91m[x-agent] [x-agent][Event] Completed report for event : {event.name} ✅\033[0m")
    return smallcounter , report



def x_agent() -> dict:
    accounts: dict= {}
    logger.info("\033[91m[x-agent] Starting Generating Report\033[0m")
    with open("./accountsX.json" , "r") as fl:
        try:
            accounts = json.loads(fl.read())
        except Exception as e:
            logger.error(f"Exception {e}")
    texts: list= []

    texts = createPostList(accounts["account_ids"])

    with open("./posts.json" ,"w") as fl:
        fl.write(json.dumps({
            "posts": texts
        }))

    # with open("./posts.json" ,"r") as fl:
    #     posts= json.loads(fl.read())
    #     texts = posts["posts"]

    agent= createAgent(modelType = 'mistral')


    finalReport = Report()

    finalReport.input = texts

    finalReport.output ={
        "fighters" : f"Report {finalReport.created_at}\n",
        "events" : f"Report {finalReport.created_at}\n"
    }

    extractionSysPrompt = ''
    with open('./prompts/entitiesExtractionSysPrompt.txt', 'r') as fl:
        extractionSysPrompt = fl.read()

        if len(extractionSysPrompt) == 0:
            raise Exception("Could not load Entities Extraction System Prompt...")
    report =  agent.run_sync(
        user_prompt= "Below follow the posts: " + json.dumps(finalReport.input) +"\n\nIf the only mention of a fighter/fighters is on a fight announcement/scheduling, avoid extracting it on the Fighters part , and extract it on the Events part ( critical distinction)." ,
        instructions=  extractionSysPrompt,
        output_type= ReportComponents
    )

    finalReport.entities= report.output

    if len(report.output.fighters) >0:
        logger.info(f'[\033[91mx-agent] Found {len(report.output.fighters)}\033[0m')
    if len(report.output.events) >0:
        logger.info(f'[\033[91mx-agent] Found {len(report.output.events)}\033[0m')



    logger.info("\033[91m[x-agent] Starting generating per Fighter Reports\033[0m")

    smallcounter = 0
    finalReport.output['events'] += "`EVENTS:`\n"
    smallcounter , finalReport = generateEventReports(smallcounter , finalReport,  agent)

    smallcounter =0
    finalReport.output['fighters'] += "`FIGHTS:`\n"
    smallcounter , finalReport = generateFighterReports(smallcounter , finalReport, agent)


    if finalReport.output["events"] == None and finalReport.output['fighters'] == None:
        return {
            "events" : "This is empty",
            "fighters": "This is empty"
        }

    with open('./misc/latestReport.txt', 'w') as fl:
        filestr = ''
        for text in finalReport.output['fighters']:
            filestr += text
        for text in finalReport.output['events']:
            filestr += text
        fl.write(filestr)

    logger.info("\033[91mReport Complete\033[0m")
    return finalReport.createReport()

if __name__ == "__main__":
    print(json.dumps(x_agent(), indent=2))
    # print(getTodaysPostsById(x_accounts[0]))
