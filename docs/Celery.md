# CELERY INTEGRATION

1. To start using celery, Add the config of broker and database in `config.json`
	For background task managment there are two options:

	i. celery

	ii. threading

	This can be configured in `config.json` file using `["background_task_manager"]["type"]` key.

	```bash
		"background_task_manager": {
        	"type": "<celery+or+threading>",
			....
		}
	```

2. If you are using celery and want to have monitoring for the same, enable it by setting `need_monitoring` key inside as **true** and set one of the following applications in `monitoring_apps` key in `config.json`:

	i. django_celery_results

	ii. django_celery_beat

	iii. django_celery_monitor

	```bash
		....
		"background_task_manager": {
			"type": "celery",
			"config": {
				"broker": "redis://localhost:6379/0",
				"backend": "redis://localhost:6379/0",
				"need_monitoring": true,
				"monitoring_apps": "django_celery_results"
			}
		}
		....
	```
	Note: Add the same in `requirements.txt` file.

3. Add the config of broker and database in `config.json`
	-  For self-hosted celery:
		```bash
			celery-broker-url="redis://localhost:6379/0"
			celery-result-backend-url="redis://localhost:6379/0"
		```

	-  For self-hosted databases:
		```bash
			celery-broker-url="redis://localhost:6379/0"
			celery-result-backend-url="db+mysql://root@localhost:3306/<name_of_db>"
		```


4. To start a worker use the following command:
	```bash
	python3 -m celery -A EnigmaAutomation worker -n worker1 -l DEBUG
	```
