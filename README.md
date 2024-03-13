# A simple helpdesk API system
placdesk app is a basic CRUD application built on top of FastAPI. This can be extend to a fully operational help desk system

## API server is written in FastAPI and backend database is in PostgreSQL. 

## What is HelpDesk ? 

A help desk is the individual, group, organizational function or external service that an IT user calls to get help with a problem. A help desk can be as simple as a physical desk where a support person takes calls. It also can be a global organization that accepts support requests submitted online or in person from around the world. The help desk function is often outsourced to support specialists.

## What is a Ticket tracking sytem 

A growing customer base is a sign of a growing business. But guess what happens when you have more and more customers?  Countless support issues, hundreds of request emails, and phones ringing non-stop in your customer service department. In the business world, customer problems are inevitable. There will always be customers who need your assistance while making a big purchase, or simply for resetting their account password. To rise above these challenges and stay ahead of the curve, a ticket management system can prove to be a real game-changer for your team. You can handle your current ticket load, scale your operations with ease, and monitor your progress at every step of the way.

![image](https://github.com/pritishpattanaik/helpdesk-fastapi/assets/18005824/e02a300a-1efc-4c69-a34f-4c7e122bf712)





> placdek used below technologies in this project: 

- Python3
- Docker 
- PostgreSQL 
- Postman and Vue.js

## Set up your local laptop as server 
  - download and install postman based on your OS https://www.postman.com/downloads/
  - VS Code is prefered, you may install any other softwares 
  - install docker desktop for Windows and MacOS https://www.docker.com/products/docker-desktop/
  - Install Python 3.8 

### Installation 

> clone this report. 

> change directory 
`$cd helpdeskapi` 

> make sure you have docker up and running on your local machine
> build and run docker-compose, this will run your API server in backend and expose port 5000 on host machine

`$docker compose up -d --build`

> check your container nama and ports its exposed 
`$docker-compose ps` 

> if it's successfullt, then you should see two containers are running helpdesk-api and db. 



### Verify database 
`$docker-compose exec db psql --username=placdesk --dbname=placdesk`


### Verify placdesk end points 


> ping test 
`$curl -X GET http://127.0.0.1:7001/plac` 

> total tickets count 
`$curl -X GET http://127.0.0.1:7001/ticketcount`

> create a new ticket 

 `curl --request POST 'http://127.0.0.1:7001/ticket/'  --data-raw '{"title":"my first ticket","description":"issue with my VPN access","status":"new","agent":"plac.agent1","customer":"plac.customer1","agent_notes":"ticket created with new status"}' -H "Content-Type:application/json"`

> get all tickets

`$curl -X GET http://127.0.0.1:7001/ticket/`

> get single ticket details with ID 

`$curl -X GET http://127.0.0.1:7001/ticket/1/`

> create bulk of tickets using python request and loop 
> you must be in project folder, install requests module using pip if it's missing 
`python3 create_tickets.py`
 > this will create 1000 tickets in your helpdesk where you can play around with UPDATE/DELETE operation. 



### import POSTMAN collection and use all available endpoint for CRUD operations. 

set environment variable url and port based on your set up 
by default url=127.0.0.1 and port=7001



Note - this helpdesk demonstrate only for education purpose, you are welcome to clone and extend the code functionality.

### Planning to develop below features for a fully operational helpdesk system 

- new endpoints such StateUpdate, AgentUpdate, CustomerUpdate, Titleupdate and many more 
- different type of ticket(incident, service request, change request and etc) 
- group - where agents will be mapped. 
- notification over email 
- ticket history 
- Frontend UI - already created in vue.js ( https://github.com/pritishpattanaik/aihelpdesk-vue ) 













