# Users
Supports registering, viewing, and retrieving user accounts.

---

## Register a New User Account

**Request**:

`POST` `/users/`

### Parameters:

| Name       | Type   | Required | Description                           |
|------------|--------|----------|---------------------------------------|
| username   | string | Yes      | The username for the new user.        |
| password   | string | Yes      | The password for the new user account.|
| first_name | string | No       | The user's given name.                |
| last_name  | string | No       | The user's family name.               |
| email      | string | No       | The user's email address.             |

*Note:*
- This endpoint does not require authorization.

**Response**:

```json
Content-Type: application/json
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

The `auth_token` returned in this response should be stored by the client for authenticating future requests to the API. See [Authentication](authentication.md).

---

## Retrieve a List of Users

**Request**:

`GET` `/users/`

### Description:

Retrieves a paginated list of user accounts. The response depends on the role of the authenticated user:
- **Admin/Superuser**: Retrieves all user accounts.
- **Regular User**: Retrieves only the account of the authenticated user.

*Note:*
- This endpoint requires authentication.

**Response**:

```json
Content-Type: application/json
200 OK

{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "6d5f9bae-a31b-4b7b-82c4-3853eda2b011",
      "username": "richard",
      "first_name": "Richard",
      "last_name": "Hendriks",
      "email": "richard@piedpiper.com"
    },
    {
      "id": "6d5f9bae-a31b-4b7b-82c4-3853eda2b012",
      "username": "gilfoyle",
      "first_name": "Bertram",
      "last_name": "Gilfoyle",
      "email": "gilfoyle@piedpiper.com"
    }
  ]
}
```

---

## Behavior Notes:

- **Pagination**: Responses are paginated by default. Use query parameters like `page` and `limit` to navigate through results.
- **Authorization**: Only authenticated users can access this endpoint.
- **Filtering**: Admins see all users; regular users see only their own account details.


## Get a user's profile information

**Request**:

`GET` `/users/:id`

Parameters:

*Note:*

- **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
200 OK

{
  "id": "6d5f9bae-a31b-4b7b-82c4-3853eda2b011",
  "username": "richard",
  "first_name": "Richard",
  "last_name": "Hendriks",
  "email": "richard@piedpiper.com",
}
```


## Update your profile information

**Request**:

`PUT/PATCH` `/users/:id`

Parameters:

Name       | Type   | Description
-----------|--------|---
first_name | string | The first_name of the user object.
last_name  | string | The last_name of the user object.
email      | string | The user's email address.



*Note:*

- All parameters are optional
- **[Authorization Protected](authentication.md)**

**Response**:

```json
Content-Type application/json
200 OK

{
  "id": "6d5f9bae-a31b-4b7b-82c4-3853eda2b011",
  "username": "richard",
  "first_name": "Richard",
  "last_name": "Hendriks",
  "email": "richard@piedpiper.com",
}
```
