# Setup
## Virtual Environment
Create a virtual environment for python named `env` by using below command,
```
python3 -m venv env
``` 
And activate it based on your OS.
## Install Required Packages
Install the Required Packages for server to run
```
pip install -r requirements.txt
```
## Environment Variables
Create a `.env` file at the root of project and enter following values
```
export GOOGLE_OAUTH2_CLIENT_ID = <CLIENT-ID>
export GOOGLE_OAUTH2_CLIENT_SECRET = <CLIENT-SECRET>
export BASE_FRONTEND_URL="http://127.0.0.1:3000"
export EMAIL_HOST_USER = "example@gmail.com"
export EMAIL_HOST_PASSWORD = <PASSWORD>
export SESSION_COOKIE_DOMAIN = "127.0.0.1"
export CSRF_COOKIE_DOMAIN = "127.0.0.1"
export CSRF_ALLOW_ORIGIN = "http://127.0.0.1:3000"

# export SESSION_COOKIE_DOMAIN = ".bookself.site"
# export CSRF_COOKIE_DOMAIN = ".bookself.site"
```

# Running Server
Run Server on whole local network at port 8000 
```
python manage.py runserver 0.0.0.0:8000
```
## Admin Creadential
```
Email : `admin2@gmail.com`
Password: `1922`
```