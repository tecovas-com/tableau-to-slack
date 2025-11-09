# Tableau to Slack Bot
This repository contains a Python script that retrieves images from Tableau dashboards and posts them to a specified Slack channel.

## Building Docker Image and Pushing to Google Container Registry

#### Build the Docker image
```bash
docker buildx build --platform linux/amd64 -t tableau-slack-bot:latest .
```

#### Run the Docker container
```bash
docker run --env-file .env tableau-slack-bot:latest
```

#### Tag the Docker image for Google Container Registry
```bash
docker tag tableau-slack-bot:latest us-central1-docker.pkg.dev/tecovas-production/data-tecovas/tableau-slack-bot:latest
``` 

#### Add Artifact Registry hosts to Docker configuration
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

##### Push the Docker image to Google Container Registry
```bash
docker push us-central1-docker.pkg.dev/tecovas-production/data-tecovas/tableau-slack-bot:latest
```
