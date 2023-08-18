# lrbot
A Discord bot

## Commands
- [`$crop`](help/crop)
- [`$gas`](help/gas)
- [`$help`](help/help)
- [`$ignore`](help/ignore)
- [`$latex`](help/latex)
- [`$radar`](help/radar)
- [`$remindme`](help/remindme)

## Setup
1. Install [Docker Engine](https://docs.docker.com/engine/install/).
2. Clone the repository and navigate to the base folder
3. Build the Docker image using `docker compose build` (this may require `sudo`). If the image is being rebuilt and the use of cached data is not desired, append `--no-cache` to build it anew.
4. Create a file `secret-token` that contains the token for your [Discord bot application](https://discord.com/developers/applications).
5. Create `config/settings.cfg` from [`config/settings-sample.cfg`](config/settings-sample.cfg), changing `owner` to the User ID of a Discord account that should receive any urgent alerts and be able to perform restricted commands.
5. Run the image in detached mode using `docker compose up -d`. Note that building the image will take a long time (depending on your internet connection) if the cache is not used, since it includes downloading and installing the entirety of TeX Live.

## Configuration
See [`config/settings.cfg`](config/settings-sample.cfg) for most configuration options.

Keyword actions can be created in `config/keywords.json`. See [`config/keywords-sample.json`](config/keywords-sample.json) for reference.

Reminders and reminder reminders can be created in `config/reminders.json` or by using [`$remindme`](help/remindme) once (or if) that feature is completed. See [`config/reminders-sample.json`](config/reminders-sample.json) for reference.

## Development
Development can be done from within a development container, as enabled by [Visual Studio Code.](https://code.visualstudio.com). With the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension active, use the `Reopen in Container` command to create and enter the development container. Within the container, the correct Python version and all necessary packages are automatically installed, enabling code-checking features. The container uses [`docker-outside-of-docker`](https://github.com/devcontainers/features/blob/main/src/docker-outside-of-docker) so that the application container can be used from within the development container. To start the application from within the development container, add `-f docker-compose.dev.yml` to `docker compose` commands when starting the container.