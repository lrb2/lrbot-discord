# lrbot
A Discord bot

## Commands
- [`$crop`](help/crop)
- [`$latex`](help/latex)

## Setup
1. Install [Docker Engine](https://docs.docker.com/engine/install/).
2. Clone the repository and navigate to the base folder
3. Build the Docker image using `docker compose build` (this may require `sudo`). If the image is being rebuilt and the use of cached data is not desired, append `--no-cache` to build it anew.
4. Create a file `secret-token` that contains the token for your [Discord bot application](https://discord.com/developers/applications).
5. Run the image in detached mode using `docker compose up -d`.