#!/usr/bin/env bash

# Import envvars
source env.sh

# Build container
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ./environment/ --build-arg CACHEBUST=$(date +%s)

# Push container to ECR
$(aws ecr get-login --no-include-email --region ${ECR_REGION})
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${AWS_ACCOUNT}.dkr.ecr.${ECR_REGION}.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}
docker push ${AWS_ACCOUNT}.dkr.ecr.${ECR_REGION}.amazonaws.com/${IMAGE_NAME}:${IMAGE_TAG}