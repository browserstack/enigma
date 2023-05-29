# First User Setup

To setup admin user on enigma, follow these steps:

1. Setup django superuser

- Exec into the Enigma container

  ```bash
  docker exec -it enigma bash
  ```

- Run the following command in the container to create a superuser

  ```bash
  python manage.py createsuperuser
  ```

- Fill in the `username`, `email` and `password` for admin user

  Checkout detailed instructions are on Django documentation [here](https://docs.djangoproject.com/en/4.2/intro/tutorial02/#creating-an-admin-user).

2. Sign-in into the admin site

- Login to the admin site with the credentials created above.

  The admin site should be available at `/admin` with the base url on which enigma is hosted.

  This will be `http://localhost:8000/admin` if you are running this locally

3. Now you can view the Enigma app dashboard, by navigating to enigma url.

   This will be `http://localhost:8000/` if you are running this locally

To create additional users, follow the doc [here](/docs/%E2%80%9CHow-to%E2%80%9D%20guides/Managing%20Groups/Adding%20Users.md).
