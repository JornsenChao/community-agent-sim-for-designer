# create backend/requirements.txt:

'''
pip-chill | Out-File -Encoding utf8 requirements.txt
or
pip freeze | Out-File -Encoding UTF8 requirements.txt
'''

# docker-postgis-flask

start docker
'''
cd backend
docker-compose build #
docker-compose up -d
'''

stop docker
'''
docker-compose stop
docker-compose rm
'''
