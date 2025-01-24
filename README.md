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
