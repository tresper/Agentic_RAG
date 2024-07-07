# Follow directions in backend README and frontend README
*Notes*

* `docker compose up` - build images (if not built yet), create containers and start all services  
* `docker compose up -d` - the same in a background process  
* `docker compose down` - stop running services and remove containers, images, networks and volumes created by up 
* `docker compose down --remove-orphans` - additional cleanup, removes containers for services not defined in docker-compose.yml
* `docker compose build` - only build images  
* `docker compose up --build` - rebuild images and start all services (useful after making changes in the code)
* `docker compose start` - start containers
* `docker compose stop` - stop container without removing them

FUll list of docker compose options: https://docs.docker.com/compose/reference/

### Application UI URL
http://localhost:8501
