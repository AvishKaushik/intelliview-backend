# IntelliView Backend

> 🔗 **Frontend Repository:** [IntelliView Frontend](https://github.com/avishkaushik/intelliview-frontend)

IntelliView is a serverless backend built with **AWS Lambda**, **API Gateway**, **DynamoDB**, **Amazon Bedrock**, and **Cognito (OIDC)** to power an AI-driven interview preparation platform. The backend handles AI-generated interview sessions, skill aggregation, feedback generation, and session management.

---

## 🧠 Lambda Functions Overview

This backend consists of **five Lambda functions**, each with a dedicated role, deployed using **AWS SAM (Serverless Application Model)**:

| Route        | Lambda Function             | Description                                                                  |
| ------------ | --------------------------- | ---------------------------------------------------------------------------- |
| `/feedback`  | `generateFeedbackFunction`  | Analyzes interview transcripts and generates feedback using Claude (Bedrock) |
| `/interview` | `generateInterviewQuestion` | Generates real-time interview responses based on user messages               |
| `/review`    | `fetchSession`              | Fetches full message history for a given interview session                   |
| `/sessions`  | `listSessions`              | Lists previous interview sessions for a user (via GSI query on DynamoDB)     |
| `/skills`    | `aggregateSkillsFunction`   | Aggregates skill ratings across sessions (technical, communication, etc.)    |

---

## 🏗️ How This Application Uses AWS Lambda

### Purpose of Using Lambda:

IntelliView uses **AWS Lambda** to create a fully serverless and scalable backend without managing any infrastructure. Each Lambda is responsible for a single unit of logic (microservice-style), resulting in clean separation of responsibilities and high cohesion.

### Lambda Integration in Detail:

1. **Stateless Execution:**
   All five Lambdas are stateless and execute on-demand via **API Gateway** triggers. There are no always-on servers.

2. **Direct Integration with Other AWS Services:**

   * **Amazon Bedrock:**

     * Used in `generateInterviewQuestion` and `generateFeedbackFunction` to invoke **Claude 3 Sonnet** models for content generation.
   * **DynamoDB:**

     * All Lambdas interact with a centralized table `InterviewSession`.
     * `generateInterviewQuestion` and `fetchSession` store or retrieve user interviews.
     * `listSessions` uses **Global Secondary Index (GSI)** `userId-ts-index` to list all sessions of a user.
     * `aggregateSkillsFunction` scans and computes skill analytics.

3. **Authentication:**

   * All endpoints are accessed via the **frontend**, which uses **AWS Cognito with OIDC** to authenticate users securely.

4. **API Gateway as Trigger:**

   * Every Lambda is mapped to a specific route in **API Gateway**, enabling RESTful HTTP invocation from the frontend.

5. **Security and Isolation:**

   * IAM roles are tightly scoped.
   * Each Lambda has permission only to access the necessary services (e.g., logs, Bedrock, DynamoDB).

6. **Environment Variables:**

   * Each Lambda fetches secrets like `MODEL_ID`, `TABLE_NAME`, and `REGION` from environment variables, making them reusable and portable.

7. **Resilience:**

   * Retry policies and logging are enabled.
   * Exceptions are handled gracefully and return structured JSON error responses.

---

## 🧾 Folder Structure

```
intelliview-backend/
│
├── generateInterviewQuestion/     # Lambda 1
├── fetchSession/                  # Lambda 2
├── generateFeedbackFunction/      # Lambda 3
├── listSessions/                  # Lambda 4
├── aggregateSkillsFunction/       # Lambda 5
```

Each folder includes:

* `template.yml`: AWS SAM deployment config
* `src/lambda_handler.py`: Lambda function logic

---

## 🔐 Authentication

* Uses **AWS Cognito** (OIDC flow) on the frontend.
* Tokens are used to identify users (`userId`) when sending requests to API Gateway.
* User-specific session data is stored and queried securely via DynamoDB.

---

## 🧪 Local Testing & Deployment

> Ensure AWS CLI and AWS SAM CLI are installed.

```bash
# Build all Lambdas
sam build

# Deploy a single Lambda (e.g., generateInterviewQuestion)
sam deploy --guided --template-file generateInterviewQuestion/template.yml
```

---

## ✅ Summary of AWS Services Used

| Service         | Purpose                                   |
| --------------- | ----------------------------------------- |
| Lambda          | Stateless backend logic for each feature  |
| API Gateway     | Public HTTP interface for the frontend    |
| DynamoDB        | Session and feedback storage              |
| Amazon Bedrock  | AI model inference using Claude 3         |
| Cognito (OIDC)  | Authentication of users from the frontend |
| CloudWatch Logs | Monitoring and debugging                  |

---

## 📬 Contact

If you find any bugs or have feedback, feel free to raise an issue or reach out on the frontend repository.

---

Made with ❤️ using AWS by [Avish Kaushik](https://github.com/avishkaushik)
