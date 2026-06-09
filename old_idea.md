# Ufc Agent

## Main Idea

The purpose of this application is to have a centralised application that keeps **information about the future UFC Events and Fights**, where **access to the information is easy/fast** and the stats are being updated in **real time**.
The application should also be able to send **notifications via telegram**(personal choice of a messenger application).

## Steps
- [ ] State the entities and their contents
- [ ] Select Language and Frameworks to use for the application
- [ ] Create a basic CRUD API for the applications backend
- [ ] Create basic tests for the API
- [ ] Create the basic agent that will be responsible for scraping/updating real time data
- [ ] Create a basic console web-app that allows access to the admin for quick access to data
- [ ] Create a basic web-app for simple users

## Ideas for application

### Invariants:
- last min changes
- fighter injuries
- late notice fights/replacements
- Flight arrivals to event place

### Betting Odds
- real time odds
- odd graphs
- best new odds

### Entities

- Events:
    * eventId
    * fights table
    * fighters
    * arena
    * location
    * startingTime
    * date

- Fights ( between 2 people ):
    * fightId
    * fighterA : fighterId
    * fighterB : fighterId
    * roundsSum

- Fighters:
    * fighterId
    * age
    * reach
    * height
    * stance
    * wld       # wins-losses-draws
    * dob       # date of birth

- Users:
    



