

# Lab9 - Introduction to cloud computing - AWS services

I used education account so from section `1` I skipped all steps except section `1.3`. Bellow I attach screens that confirms configuration were suecessful. Model files were uploaded to s3 bucket and then retrieved with [aws_utils.py](src/lab09_lib/aws_utils.py). Once retrieved, model files was copied by `COPY large_models ./large_models` command in [Dockerfile](Dockerfile)


## AWS Cli configuration
![Alt text](assets/mlops_lab9_screen1.png)


## Ecr repository with docker image pushed
![Alt text](assets/mlops_lab9_screen2.png)


## Created subnets
![Alt text](assets/mlops_lab9_screen3.png)

## Created VPC
![Alt text](assets/mlops_lab9_screen4.png)

## Load Balancer Configuration

![Alt text](assets/mlops_lab9_screen10.png)
![Alt text](assets/mlops_lab9_screen11.png)
![Alt text](assets/mlops_lab9_screen5.png)
![Alt text](assets/mlops_lab9_screen12.png)




## Fargate Service with running tasks
![Alt text](assets/mlops_lab9_screen6.png)

## Swagger UI in deployed Service
![Alt text](assets/mlops_lab9_screen7.png)

## Working Endpoint example
![Alt text](assets/mlops_lab9_screen8.png)

## Some metrics and logs

![Alt text](assets/mlops_lab9_screen13.png)

![Alt text](assets/mlops_lab9_screen14.png)

![Alt text](assets/mlops_lab9_screen15.png)

## Passed tests
![Alt text](assets/mlops_lab9_screen9.png)

Tests were taken from `lab01` and adjusted to point to deployed API instead of local fastapi `TestClient`.