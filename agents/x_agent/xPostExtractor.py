import requests
import datetime
from logger  import logger
import os



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
        logger.error(f"Error: {response.status_code}")
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
            logger.error(e)
        return date_object

    dateNow= datetime.datetime.now(datetime.timezone.utc)
    postDate : datetime.datetime | None= None
    texts = []
    responseDict , cursor = getPostsById(id)
    textObjects= []                                 # contains dicts of {"text", "created_at"}
    logger.debug(f"Starting for id: {id}...")

    for post in responseDict['timeline']:           #  get the texts with their created_at dates
        texts.append(post["text"])
        if transformDate(post["created_at"]) == None:
            continue
        textObjects.append({
            "text" : post["text"],
            "created_at" : transformDate(post["created_at"])
        })

    for txt in textObjects:
        if (dateNow - txt["created_at"]).days >= 1:
            continue
        texts.append(txt["text"])
    # while (dateNow - postDate).days < 1 and cursor:
    #     logger.debug("Getting more posts...")
    #     responseDict, cursor = getPostsById(id, cursor)
    #     for post in responseDict['timeline']:
    #         postDate = transformDate(post["created_at"])
    #         if (dateNow - postDate).days < 1:
    #             texts.append(post["text"])
    #         else:
    #             break

    return texts

def createPostList(account_ids: list[str]) -> list:
    texts : list= []
    counter = 0

    for account_id in account_ids:
        while counter< 3:
            try:
                response_texts = getTodaysPostsById(account_id)
                texts.append(response_texts)
                break
            except Exception as e:
                logger.error(f"For id : {account_id} ,times : {counter+1}\nException {e} ")
                counter += 1
                continue
        counter = 0

    return texts

if __name__ == '__main__':
    import json
    with open("./accountsX.json", 'r') as fl:
        texts = json.loads(fl.read())
        print(createPostList(texts['account_ids']))
