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
        description="A list of reports for the Fighter the **User** asked for. The reports must be at **max 1 sentences** long and in **plaintext**, no markdown and make the reports consice. Do not add reports that do not belong to the Figher",
        default=[]
    )

class EventReports(BaseModel):
    reports: list[str]= Field(
        description="A list of reports for the event. The reports must be at **max 1 sentences** long and in **plaintext**, no markdown and make the reports consice",
        default= []
    )

class ReportComponents(BaseModel):
    fighters: list[FighterName] = Field(description="The names of all the fightes listed")
    events: list[EventName]= Field(description="The names of all the events listed")



class Report:
    created_at: datetime.datetime
    fighters:  dict = {}
    events: dict = {}

    def __init__(self):
        self.created_at = datetime.datetime.now().strftime("%A %d %B %Y")
