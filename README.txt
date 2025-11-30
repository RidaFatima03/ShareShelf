In order to build, use the following commands on terminal (Make sure that Docker application is open):

	docker build –t shareshelfapp .
	docker compose up -d

You can reach the service at http://localhost:5000/

In order for 'Reset Password' functionality to work, copy .env.example to .env and fill in your own values. The .env file is ignored by git as it is declared in out .gitignore file. Do not use your gmail password directly. Instead, follow this link to generate a one:

	https://myaccount.google.com/apppasswords