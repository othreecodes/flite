
# Project Setup Guide

This guide will walk you through setting up the project locally using Docker.

## Prerequisites

Before you begin, ensure you have the following installed:

- Docker
- Docker Compose
- Git

## Setup Steps

1. **Clone the Project**

   First, clone the project repository from GitHub:

   ```bash
   git clone <repository-url>
   ```

2. **Navigate to the Project Directory**

   Change into the project directory:

   ```bash
   cd <project-directory>
   ```

3. **Start Docker Containers**

   Run the following command to start the Docker containers:

   ```bash
   docker-compose up
   ```

   This will set up the necessary services defined in the `docker-compose.yml` file.

4. **Set Up the Environment Variables**

   Copy the contents of the `.env-example` file and save it as `.env` in the project directory:

   ```bash
   cp .env-example .env
   ```

   This will configure the environment variables needed for the project.

5. **Run the Application**

   After the containers are up and the environment variables are set, you can proceed with running the application as needed.

## Additional Information

- If you encounter any issues during setup, check the logs with `docker-compose logs` for troubleshooting.
- For any further configurations, refer to the project documentation or consult the team.

# Project Endpoints

# 1. User Deposit

Supports depositing funds into a user's account.

## Deposit funds into a user's account

**Request**:

`POST` `/api/v1/users/:user_id/deposits/`

Parameters:

Name       | Type   | Required | Description
-----------|--------|----------|------------
amount     | float  | Yes      | The amount to be deposited. Must be greater than zero.

*Note:*

- **Authorization Protected**: You must include a valid authentication token in the request header.
- The `user_id` in the URL should be the UUID of the user making the deposit.
- The deposit amount must be a positive number.


## Example Request in Postman

1. Set the request method to `POST`.
2. Set the URL to: `http://localhost:8000/api/v1/users/<user_id>/deposits/`.
3. In the request body, set the type to `raw` and choose `JSON` format. Then enter the following JSON:

```json
{
  "amount": 100.0
}
```

4. Include the authentication token in the request header:

```text
Authorization: Token <your_token>
```

5. Send the request, and you should receive a response with the updated balance.

---

**Response**:

### Success Response

```json
Content-Type application/json
201 Created

{
  "message": "Deposit successful",
  "status": 201,
  "old_balance": 0.0,
  "available_balance": 100.0
}
```

- **message**: A success message indicating that the deposit was successful.
- **status**: The HTTP status code (`201 Created`).
- **old_balance**: The balance of the user's account before the deposit was made.
- **available_balance**: The balance of the user's account after the deposit was made.

### Error Response (Bad Request)

```json
Content-Type application/json
400 Bad Request

{
  "error": "Deposit must be greater than zero",
  "status": 400
}
```

- **error**: A description of what went wrong (e.g., the deposit amount is invalid).
- **status**: The HTTP status code (`400 Bad Request`).

---

## Assumptions

- Once a `POST` request is made to this endpoint with a valid amount, the user's account is credited.

---


# 2. User Withdrawal

Supports withdrawing funds from a user's account.

## Withdraw funds from a user's account

**Request**:

`POST` `/api/v1/users/:user_id/withdrawals/`

### Parameters:

| Name     | Type   | Required | Description                                                   |
|----------|--------|----------|---------------------------------------------------------------|
| amount   | float  | Yes      | The amount to be withdrawn. Must be greater than zero and less than or equal to the available balance. |

**Note**:

- **Authorization Protected**: You must include a valid authentication token in the request header.
- The `user_id` in the URL should be the UUID of the user making the withdrawal.
- The withdrawal amount must be a positive number and cannot exceed the available balance.

---

### Example Request in Postman

1. Set the request method to `POST`.
2. Set the URL to: `http://localhost:8000/api/v1/users/<user_id>/withdrawals/`.
3. In the request body, set the type to `raw` and choose `JSON` format. Then enter the following JSON:

```json
{
  "amount": 200.0
}
```

4. Include the authentication token in the request header:

```text
Authorization: Token <your_token>
```

5. Send the request, and you should receive a response with the updated balance.

---

**Response**:

### Success Response

```json
Content-Type: application/json
200 OK

{
  "message": "Withdrawal successful",
  "status": 200,
  "old_balance": 1000.0,
  "available_balance": 800.0
}
```

- **message**: A success message indicating that the withdrawal was successful.
- **status**: The HTTP status code (`200 OK`).
- **old_balance**: The balance of the user's account before the withdrawal was made.
- **available_balance**: The balance of the user's account after the withdrawal was made.

### Error Response (Insufficient Funds)

```json
Content-Type: application/json
400 Bad Request

{
  "message": "Insufficient funds",
  "balance": 0.0,
  "amount": 200,
  "status": 400
}
```

- **message**: A description of what went wrong (e.g., the withdrawal amount exceeds the available balance).
- **status**: The HTTP status code (`400 Bad Request`).

### Error Response (Balance Not Found)

```json
Content-Type: application/json
400 Bad Request

{
  "message": "Balance record not found",
  "status": 400
}
```

- **message**: A description of what went wrong (e.g., no balance record found for the user).
- **status**: The HTTP status code (`400 Bad Request`).

---

## Assumptions

- Once a `POST` request is made to this endpoint with a valid amount, the user's account is debited.

---

# 3. Fund Transfer

Supports transferring funds from one user's account to another user's account.

## Transfer funds between users

**Request**:

`POST` `/api/v1/account/:sender_account_id/transfers/:recipient_account_id/`

### Parameters:

| Name                   | Type   | Required | Description                                                                 |
|------------------------|--------|----------|-----------------------------------------------------------------------------|
| amount                 | float  | Yes      | The amount to be transferred. Must be greater than zero and less than or equal to the sender's available balance. |
| sender_account_id      | int    | Yes      | The ID of the sender's account (authenticated user's account).             |
| recipient_account_id   | int    | Yes      | The ID of the recipient's account.                                          |

**Note**:

- **Authorization Protected**: You must include a valid authentication token in the request header.
- The `sender_account_id` in the URL should correspond to the authenticated user's account.
- The `recipient_account_id` should be the ID of the user receiving the funds.
- The `amount` must be a positive number and cannot exceed the sender's available balance.

---

### Example Request in Postman

1. Set the request method to `POST`.
2. Set the URL to: `http://localhost:8000/api/v1/account/<sender_account_id>/transfers/<recipient_account_id>/`.
3. In the request body, set the type to `raw` and choose `JSON` format. Then enter the following JSON:

```json
{
  "amount": 200.0
}
```

4. Include the authentication token in the request header:

```text
Authorization: Token <your_token>
```

5. Send the request, and you should receive a response with the updated balances.

---

**Response**:

### Success Response

```json
Content-Type: application/json
200 OK

{
  "message": "Transfer successful",
  "status": 200,
  "sender_old_balance": 1000.0,
  "sender_new_balance": 800.0,
  "recipient_old_balance": 500.0,
  "recipient_new_balance": 700.0
}
```

- **message**: A success message indicating that the transfer was successful.
- **status**: The HTTP status code (`200 OK`).
- **sender_old_balance**: The balance of the sender's account before the transfer was made.
- **sender_new_balance**: The balance of the sender's account after the transfer was made.
- **recipient_old_balance**: The balance of the recipient's account before the transfer was made.
- **recipient_new_balance**: The balance of the recipient's account after the transfer was made.

### Error Response (Insufficient Funds)

```json
Content-Type: application/json
400 Bad Request

{
  "message": "Insufficient funds",
  "status": 400
}
```

- **message**: A description of what went wrong (e.g., the transfer amount exceeds the sender's available balance).
- **status**: The HTTP status code (`400 Bad Request`).

### Error Response (Sender Balance Not Found)

```json
Content-Type: application/json
400 Bad Request

{
  "message": "Sender balance record not found",
  "status": 400
}
```

- **message**: A description of what went wrong (e.g., no balance record found for the sender).
- **status**: The HTTP status code (`400 Bad Request`).

### Error Response (Recipient Balance Not Found)

```json
Content-Type: application/json
400 Bad Request

{
  "message": "Recipient balance record not found",
  "status": 400
}
```

- **message**: A description of what went wrong (e.g., no balance record found for the recipient).
- **status**: The HTTP status code (`400 Bad Request`).

### Error Response (Recipient User Not Found)

```json
Content-Type: application/json
400 Bad Request

{
  "message": "Recipient user not found",
  "status": 400
}
```

- **message**: A description of what went wrong (e.g., the recipient user does not exist).
- **status**: The HTTP status code (`400 Bad Request`).

---

## Assumptions

- Once a `POST` request is made to this endpoint with a valid amount, the sender's account is debited, and the recipient's account is credited.

# 4. Transaction List

Supports retrieving a paginated list of transactions for the authenticated user.

## Retrieve User Transactions

**Request**:

`GET` `/api/v1/account/:account_id/transactions/`

### Parameters:

| Name | Type   | Required | Description                                                                 |
|------|--------|----------|-----------------------------------------------------------------------------|
| id   | int    | Yes      | The ID of the authenticated user whose transactions are to be retrieved.    |

**Note**:

- **Authorization Protected**: You must include a valid authentication token in the request header.
- The `id` in the URL must correspond to the authenticated user's ID (`request.user.id`).
- Transactions are returned in ascending order of their `created_at` timestamp.

---

### Example Request in Postman

1. Set the request method to `GET`.
2. Set the URL to: `http://localhost:8000/api/v1/account/<account_id>/transactions/` (replace `<account_id>` with the authenticated user's ID).
3. Include the authentication token in the request header:

```text
Authorization: Token <your_token>
```

4. Send the request, and you should receive a paginated response with the user's transactions.

---

### Response

#### Success Response (200 OK)

```json
Content-Type: application/json
200 OK

{
  "count": 5,
  "next": "http://localhost:8000/api/v1/user/123/transactions/?page=2",
  "previous": null,
  "results": [
    {
            "id": "b28da037-0fb1-4375-a373-3d14082fb98c",
            "created": "2025-01-24T13:21:41+0100",
            "modified": "2025-01-24T13:21:41+0100",
            "reference": "d81c7f88-e017-4d73-896a-bbaaad483cc7",
            "amount": 10000.0,
            "new_balance": 10000.0,
            "type": "Deposit",
            "created_at": "2025-01-24T13:21:41+0100",
            "owner": "e4b2080c-66b8-4546-b435-cdbe474b81f7",
            "sender": null,
            "recipient": null
    },
    {
            "id": "0bbdc3f6-c7fc-4e77-8cbf-05827d1bbcbf",
            "created": "2025-01-24T13:21:44+0100",
            "modified": "2025-01-24T13:21:44+0100",
            "reference": "cd1417ba-9061-4a8f-9605-388e4ef726d1",
            "amount": 100.0,
            "new_balance": 10100.0,
            "type": "Deposit",
            "created_at": "2025-01-24T13:21:44+0100",
            "owner": "e4b2080c-66b8-4546-b435-cdbe474b81f7",
            "sender": null,
            "recipient": null
    }
  ]
}
```

- **count**: Total number of transactions for the user.
- **next**: URL for the next page of results (if applicable).
- **previous**: URL for the previous page of results (if applicable).
- **results**: A list of transactions with their details.

---

### Error Responses

#### Unauthorized Access (403 Forbidden)

```json
Content-Type: application/json
403 Forbidden

{
  "message": "You are not authorized to view this user's transactions",
  "status": 403
}
```

- **message**: Explains that the authenticated user is not authorized to view the transactions for the given user ID.
- **status**: The HTTP status code (`403 Forbidden`).

---

#### No Transactions Found (200 OK)

```json
Content-Type: application/json
200 OK

{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

- **count**: Indicates no transactions were found for the user.
- **results**: An empty list indicating no transactions are available.

---

#### Error Response (400 Bad Request)

```json
Content-Type: application/json
400 Bad Request

{
  "errors": "Some error message",
  "status": 400
}
```

- **errors**: Describes the specific error encountered during the request.
- **status**: The HTTP status code (`400 Bad Request`).

---

# 5. Transaction Detail

Supports retrieving the details of a specific transaction for an authenticated user.

## Retrieve a transaction detail

**Request**:

`GET` `/api/v1/account/:account_id/transactions/:transaction_id/`

### Parameters:

| Name            | Type   | Required | Description                                                           |
|-----------------|--------|----------|-----------------------------------------------------------------------|
| user_id         | int    | Yes      | The ID of the authenticated user whose transaction is being retrieved.|
| transaction_id  | int    | Yes      | The ID of the specific transaction to retrieve.                       |

**Note**:

- **Authorization Protected**: You must include a valid authentication token in the request header.
- The `user_id` in the URL must match the authenticated user's ID.
- The `transaction_id` must belong to a transaction owned by the authenticated user.

---

### Example Request in Postman

1. Set the request method to `GET`.
2. Set the URL to: `http://localhost:8000/api/v1/account/<account_id>/transactions/<transaction_id>/`.
3. Include the authentication token in the request header:

```text
Authorization: Token <your_token>
```

4. Send the request, and you should receive the details of the specified transaction.

---

**Response**:

### Success Response

```json
Content-Type: application/json
200 OK

{
    "id": "b28da037-0fb1-4375-a373-3d14082fb98c",
    "created": "2025-01-24T13:21:41+0100",
    "reference": "d81c7f88-e017-4d73-896a-bbaaad483cc7",
    "amount": 10000.0,
    "new_balance": 10000.0,
    "type": "Deposit",
    "created_at": "2025-01-24T13:21:41+0100",
    "owner": "e4b2080c-66b8-4546-b435-cdbe474b81f7",
    "sender": null,
    "recipient": null
}
```

- **id**: The unique identifier (UUID) of the transaction.
- **created**: The timestamp when the transaction was created.
- **reference**: A unique reference for the transaction.
- **amount**: The amount involved in the transaction.
- **new_balance**: The user's updated balance after the transaction.
- **type**: The type of transaction (e.g., `Deposit`, `Withdrawal`).
- **created_at**: The timestamp when the transaction was created (duplicate of `created`).
- **owner**: The UUID of the user who owns the transaction.
- **sender**: The UUID of the sender (if applicable, otherwise `null`).
- **recipient**: The UUID of the recipient (if applicable, otherwise `null`).

---

### Error Response (Unauthorized Access)

```json
Content-Type: application/json
403 Forbidden

{
  "message": "You are not authorized to view this user's transactions",
  "status": 403
}
```

- **message**: Indicates that the authenticated user is not authorized to access this transaction.
- **status**: The HTTP status code (`403 Forbidden`).

---

### Error Response (Transaction Not Found)

```json
Content-Type: application/json
404 Not Found

{
  "message": "Transaction not found",
  "status": 404
}
```

- **message**: Indicates that the specified transaction does not exist for the user.
- **status**: The HTTP status code (`404 Not Found`).

---

### Error Response (Other Errors)

```json
Content-Type: application/json
400 Bad Request

{
  "errors": "Error message describing what went wrong",
  "status": 400
}
```

- **errors**: A description of the error encountered.
- **status**: The HTTP status code (`400 Bad Request`).

---

Here is the updated documentation based on the provided response structure:

---