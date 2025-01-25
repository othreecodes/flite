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