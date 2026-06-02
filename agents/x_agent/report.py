from pydantic import BaseModel, Field
import datetime

from pydantic_core import ValidationError

class FighterName(BaseModel):
    fullname: str = Field(
        description="The FULL name of the Fighter (First ,Middle, Last name) as displayed in the texts, avoid duplicates.",
        default=''
    )

class EventName(BaseModel):
    name: str = Field(
        description="The full name of the Event as displayed in the texts, avoid duplicates.",
        default=''
    )

class FighterReports(BaseModel):
    reports: list[str] =Field(
        description="A list of reports for the Fighter the **User** asked for. The reports must be at **max 1 sentences** long and in **plaintext**, no markdown and make the reports consice. IMPORTANT: Fight announcement between fighters two fighters **SHOULD NOT** be reported, ignore them",
        default=[]
    )

class EventReports(BaseModel):
    reports: list[str]= Field(
        description="A list of reports for the event. The reports must be at **max 1 sentences** long and in **plaintext**, no markdown and make the reports consice. Stuff like Fight announcement between 2 fighters must be included here",
        default= []
    )

class ReportComponents(BaseModel):
    fighters: list[FighterName] = Field(description="The names of all the fightes listed")
    events: list[EventName]= Field(description="The names of all the events listed")



class Report:
    created_at: datetime.datetime
    entities: ReportComponents
    fighters:  dict = {}
    events: dict = {}
    input: list[str]= []
    output= dict={}
    report: str = ""

    def __init__(self):
        self.created_at = datetime.datetime.now().strftime("%A %d %B %Y")
