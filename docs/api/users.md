# Project Setup and Assumptions

## Setting Up the Project

### Fork and Clone Repository
1. Fork the repository to your GitHub account.
2. Clone the forked repository to your local environment using:
   ```bash
   git clone <repository-url>
   ```

### Running the Project with Docker
1. Run the following command to build and start the services:
   ```bash
   docker-compose up
   ```
2. If you encounter an error related to the working directory not being specified in the Docker Compose `django` service environment, fix this by adding the working directory to the service configuration.
3. After fixing the configuration, rebuild and start the Docker containers:
   ```bash
   docker-compose up --build
   ```

### Creating a Superuser
1. SSH into the Docker container:
   ```bash
   docker exec -it <container_name> bash
   ```
2. Create a superuser to access admin functionalities:
   ```bash
   python manage.py createsuperuser
   ```

---

## Views and Endpoints Implemented

### Endpoints Overview
Below is the list of view classes, functions, and serializers implemented:

### Retrieve user details

**Request**:

`GET` `/users/:user_id/`

*Note:* **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
200 OK


{
    "id": "daa20e78-eca9-41cd-84c9-35059f390420",
    "username": "richard",
    "first_name": "Richard",
    "last_name": "Hendriks"
}
```
### List all users

**Request**:

`GET` `/users/`

*Note:* **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
200 OK

{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "daa20e78-eca9-41cd-84c9-35059f390420",
            "username": "richard",
            "first_name": "Richard",
            "last_name": "Hendriks"
        },
        {
            "id": "ae90fb3b-6904-4284-9ce9-67819203d9cc",
            "username": "micheal",
            "first_name": "Micheal",
            "last_name": "Scotland"
        }
    ]
}
```
### Deposit money to a user account

**Request**:

`POST` `/users/:user_id/deposits`

| Name       | Type   | Required | Description                       |
|------------|--------|----------|-----------------------------------|
| amount     | integer| Yes      | The amount to be deposited.       |

*Note:* **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
201 Created

{
    "message": "Deposit successful",
    "new_balance": 10.0,
    "transaction_reference": "DEP-8bf9b975"
}
```

### Withdraw money from a user account

**Request**:

`POST` `/users/:user_id/withdrawals`

| Name       | Type   | Required | Description                       |
|------------|--------|----------|-----------------------------------|
| amount     | integer| Yes      | The amount to be withdrawn.       |

*Note:* **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
201 Created

{
    "message": "Withdrawal successful",
    "new_balance": 0.0,
    "transaction_reference": "WDL-5c867546"
}
```

### Transfer money between accounts

**Request**:

`POST` `/account/:sender_account_id/transfers/:recipient_account_id`

| Name       | Type   | Required | Description                       |
|------------|--------|----------|-----------------------------------|
| amount     | integer| Yes      | The amount to be withdrawn.       |

*Note:* **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
201 Created

{
    "message": "Transfer successful",
    "sender_new_balance": 19990.0,
    "recipient_new_balance": 1000023.0,
    "transaction_reference": "TRF-b2e69065"
}
```

### Retrieve transactions for a specific account

**Request**:

`GET` `/account/:account_id/transactions`

*Note:* **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
200 OK

{
    "count": 4,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "344e4cdc-5353-4183-a1c1-9be9534dae7d",
            "reference": "TRF-6d524887",
            "status": "Successful",
            "amount": 10.0,
            "new_balance": 1000023.0
        },
        {
            "id": "c7b49882-0419-4c7b-b304-16b8c5428774",
            "reference": "TRF-01b1504d",
            "status": "Successful",
            "amount": 999999.0,
            "new_balance": 1000013.0
        },
        {
            "id": "7324a965-dd0b-4022-aa70-c75537b32798",
            "reference": "TRF-21fe151a",
            "status": "Successful",
            "amount": 4.0,
            "new_balance": 14.0
        },
        {
            "id": "923f7b15-b8c6-4d48-a74b-410d6bb60fb9",
            "reference": "DEP-43694ba4",
            "status": "Successful",
            "amount": 10.0,
            "new_balance": 10.0
        }
    ]
}
```

### Retrieve details of a specific transaction.

**Request**:

`GET` `/account/:account_id/transactions/:transaction_id`

*Note:* **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
200 OK

{
    "id": "344e4cdc-5353-4183-a1c1-9be9534dae7d",
    "reference": "TRF-6d524887",
    "status": "Successful",
    "amount": 10.0,
    "new_balance": 1000023.0
}
```

---

## Observations and Assumptions

### Logical Flaws in the Model
- The `Balance` model is associated only with a `User` (`owner` field) but not with a `Bank`. This does not align with real-world scenarios where each balance should belong to a specific bank account.
- The `Bank` model is tied to a `User` (`owner` field) but not explicitly linked to `Balance`, creating ambiguity about which balance corresponds to which bank.
- There is no direct relationship between `Transaction` and `Bank`. This is problematic because transactions like bank transfers logically depend on a specific bank.

### Assumptions Made
To retrieve transaction details:
1. `Balance` was mapped to a `User`.
2. A `Transaction` record was created and linked to a `User`.

### Suggested Improvements
- Map `Balance` to `Bank`:
  Add a ForeignKey relationship between `Balance` and `Bank` to associate balances with specific bank accounts.
- Associate `Transaction` with both `User` and `Balance`:
  Add a ForeignKey to the `Transaction` model for `Balance` to make it clear which balance is being affected.

---

# API Documentation

## Users
Supports registering, viewing, and updating user accounts.

### Register a New User Account

**Request**:

`POST` `/users/`

| Name       | Type   | Required | Description                       |
|------------|--------|----------|-----------------------------------|
| username   | string | Yes      | The username for the new user.    |
| password   | string | Yes      | The password for the new account. |
| first_name | string | No       | The user's given name.            |
| last_name  | string | No       | The user's family name.           |
| email      | string | No       | The user's email address.         |

*Note:* Not Authorization Protected

**Response**:

```json
Content-Type application/json
201 Created

{
  "id": "6d5f9bae-a31b-4b7b-82c4-3853eda2b011",
  "username": "richard",
  "first_name": "Richard",
  "last_name": "Hendriks",
  "email": "richard@piedpiper.com",
  "auth_token": "132cf952e0165a274bf99e115ab483671b3d9ff6"
}
```

The `auth_token` returned with this response should be stored by the client for authenticating future requests to the API. See [Authentication](authentication.md).

### Get a User's Profile Information

**Request**:

`GET` `/users/:id`

*Note:* **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
200 OK

{
  "id": "6d5f9bae-a31b-4b7b-82c4-3853eda2b011",
  "username": "richard",
  "first_name": "Richard",
  "last_name": "Hendriks",
  "email": "richard@piedpiper.com"
}
```

### Update Your Profile Information

**Request**:

`PUT/PATCH` `/users/:id`

| Name       | Type   | Description                     |
|------------|--------|---------------------------------|
| first_name | string | The first name of the user.     |
| last_name  | string | The last name of the user.      |
| email      | string | The user's email address.       |

*Note:* All parameters are optional. **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
200 OK

{
  "id": "6d5f9bae-a31b-4b7b-82c4-3853eda2b011",
  "username": "richard",
  "first_name": "Richard",
  "last_name": "Hendriks",
  "email": "richard@piedpiper.com"
}
