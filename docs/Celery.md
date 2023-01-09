# CELERY INTEGRATION

1. To start using celery first install all the modules listed in requirements.
2. Add the config of broker and database in `setting.py`
	```bash
	CELERY_BROKER_URL = "redis://localhost:6379"
	CELERY_RESULT_BACKEND = "db+mysql://root@localhost:3306/BrowserStackAutomation"
	```
3. Import the required modules in `Access.celery_helper.py` .
4. You are all set to run celery task from terminal or by calling `generate_celery_task`  function.
5. To start a worker use the following command:
	```bash
	python3 -m celery -A BrowserStackAutomation worker -n worker1 -l DEBUG
	```
6. To use the celery function from the terminal follow below steps:
	```bash
	python3 manage.py shell
	from Access.celery_helper import generate_celery_task
	generate_celery_task.delay("dummy_func", (1,2))
	```
7. Requirements:
	```bash
	django==4.1.3
	social-auth-app-django==5.0.0
	djangorestframework==3.14.0
	mysqlclient==2.1.1
	django-celery-results==2.4.0
	sqlalchemy==1.4.45
	redis==4.4.0
	celery==5.2.7
	```

