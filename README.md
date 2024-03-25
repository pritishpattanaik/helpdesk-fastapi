# PlacDesk: A Simple Helpdesk API System

PlacDesk is a basic CRUD application built on top of FastAPI, designed to be extended into a fully operational help desk system.

## Technologies Used

- **FastAPI**: API server framework
- **PostgreSQL**: Backend database
- **Python3**: Programming language
- **Docker**: Containerization
- **Postman** and **Vue.js**: Used for testing and frontend development respectively

## Understanding HelpDesk

A help desk serves as the primary point of contact for IT users seeking assistance with technical issues. It can range from a physical desk manned by support personnel to a global organization handling support requests worldwide.

## Ticket Tracking System

As businesses grow, so do customer support needs. A ticket management system centralizes support requests, streamlining issue resolution and allowing teams to scale operations efficiently. PlacDesk aims to address these challenges effectively.

![Helpdesk](https://github.com/pritishpattanaik/helpdesk-fastapi/assets/18005824/e02a300a-1efc-4c69-a34f-4c7e122bf712)

## Local Setup

To set up PlacDesk on your local machine:

1. Download and install [Postman](https://www.postman.com/downloads/) for API testing.
2. Preferably use VS Code for development, or any other preferred code editor.
3. Install Docker Desktop for [Windows and MacOS](https://www.docker.com/products/docker-desktop/).
4. Ensure Python 3.8 is installed on your system.

### Installation Steps

1. Clone this repository
   ```bash
    $ git clone https://github.com/pritishpattanaik/helpdesk-fastapi.git
   ```
3. Navigate to the cloned directory:
   ```bash
   $ cd helpdesk-fastapi/
   ```
4. Ensure Docker is running,then create network plac-net (for first time setup)
   ```bash
   $ docker network create plac-net
   ```
5. Then run below to make sure containers are down
   ```bash
   $ docker compose down
   ```
6. Then build and run Docker Compose to start the API server:
   ```bash
   $ docker compose up -d --build
   ```
7. Verify containers are running successfully:
   ```bash
   $ docker compose ps
   ```
   
### Database Verification

To verify the database:

```bash
$ docker compose exec db psql --username=placdesk --dbname=placdesk
```

### Endpoint Verification

Test PlacDesk endpoints using the following commands:

- Ping test:
  ```bash
  $ curl -X GET http://127.0.0.1:7001/plac
  ```

- Total tickets count:
  ```bash
  $ curl -X GET http://127.0.0.1:7001/ticketcount
  ```

- Create a new ticket:
  ```bash
  $ curl --request POST 'http://127.0.0.1:7001/ticket/'  --data-raw '{"title":"my first ticket","description":"issue with my VPN access","status":"new","agent":"plac.agent1","customer":"plac.customer1","agent_notes":"ticket created with new status"}' -H "Content-Type:application/json"
  ```

- Get all tickets:
  ```bash
  $ curl -X GET http://127.0.0.1:7001/ticket/
  ```

- Get details of a single ticket by ID:
  ```bash
  $ curl -X GET http://127.0.0.1:7001/ticket/1/
  ```

- Create bulk tickets using Python script:
  Ensure you are in the project folder and have the `requests` module installed via pip:
  ```bash
  $ python3 create_tickets.py
  ```

### Postman Collection
go to http://127.0.0.1:7001/docs and download the swagger spec. Import it to postman. 



**Note**: This helpdesk demonstration is for educational purposes only. Feel free to clone and extend its functionality.

## Planned Features

In the future, PlacDesk aims to incorporate the following features for a fully operational helpdesk system:

- Additional endpoints such as StateUpdate, AgentUpdate, CustomerUpdate, TitleUpdate, and more.
- Support for different types of tickets (incident, service request, change request, etc.).
- Group functionality for mapping agents.
- Email notifications.
- Ticket history tracking.
- Frontend UI already created in Vue.js ([GitHub Repo](https://github.com/pritishpattanaik/aihelpdesk-vue)).
