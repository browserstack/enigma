# CELERY INTEGRATION

1. To start using celery first install all the modules listed in requirements.
2. Add the config of broker and database in `config.json`
	for background task managment there are two option: celery and Thread.
	This can be configured in config.json file using background_task_manager key

    If you are using celery and want to have some monitoring for the same, enable it by setting
	need_monitoring key inside background_task_manager as true and set the app from below
	options in monitoring_apps key:
    django_celery_results vs django_celery_beat vs django_celery_monitor
	Remember to add the same in requirments.txt file.

	```bash
	CELERY_BROKER_URL = "redis://localhost:6379"
	CELERY_RESULT_BACKEND = "db+mysql://root@localhost:3306/EnigmaAutomation"
	```
3. Import the required modules in `Access.celery_helper.py` .
4. You are all set to run celery task from terminal or by calling `generate_celery_task`  function.
5. To start a worker use the following command:
	```bash
	python3 -m celery -A EnigmaAutomation worker -n worker1 -l DEBUG
	```
6. To use the celery function from the terminal follow below steps:
	```bash
	python3 manage.py shell
	from Access.celery_helper import celery_task
	celery_task.delay("confluence_module", "access_desc", None)

	from Access.background_task_manager import background_task
	requestId=None
	requestObject=None
	accessType=None
	user=None
	approver=None
	background_task('run_access_grant', requestId, requestObject, accessType, user, approver)

	background_task('test_grant')
	```
7. Requirements:
	```bash
	django==4.1.7
	social-auth-app-django==5.0.0
	djangorestframework==3.14.0
	mysqlclient==2.1.1
	django-celery-results==2.4.0
	sqlalchemy==1.4.45
	redis==4.4.0
	celery==5.2.7
	```
