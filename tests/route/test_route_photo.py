import pytest

# create photo
def test_create_photo_ok(client, token, photo):
    # authenticate
    # mock cloudinary request
    response = client.post(
        f"/api/photo/{photo['id']}",
        json=photo,
        headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert data["detail"] == "Photo successfully uploaded"
    # db entry exists

def test_create_photo_failure_cloudinary(client, token, photo):
    # authenticate
    # mock cloudinary request
    response = client.post(
        f"/api/photo/{photo['id']}",
        json=photo,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 500

# delete photo
def test_delete_photo_ok_user(client, token, photo):
    # authenticate as owner user
    response = client.delete(
        f"/api/photo/{photo['id']}",
        headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == 200
    assert data["detail"] == "Photo succesfuly deleted"
    # no entry in DB
    # no response by URL

def test_delete_photo_ok_admin(client, admin_token, photo):
    # authenticate as admin
    response = client.delete(
        f"/api/photo/{photo['id']}",
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    data = response.json()
    assert response.status_code == 200
    assert data["detail"] == "Photo succesfuly deleted"
    # no entry in DB
    # no response by URL

def test_delete_photo_fail_moder(client, token, photo):
    # authenticate as moder
    response = client.delete(
        f"/api/photo/{photo['id']}",
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 401

def test_delete_photo_fail_not_found(client, token, photo):
    # authenticate
    response = client.delete(
        f"/api/photo/{photo['id']}",
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 404

def test_delete_photo_fail_no_permissions_user(client, token02, photo):
    # authenticate as non-owner user
    response = client.delete(
        f"/api/photo/{photo['id']}",
        headers={'Authorization': f'Bearer {token02}'}
    )
    assert response.status_code == 401

def test_delete_photo_fail_no_permissions_moder(client, moder_token, photo):
    # authenticate as moder
    response = client.delete(
        f"/api/photo/{photo['id']}",
        headers={'Authorization': f'Bearer {moder_token}'}
    )
    assert response.status_code == 401

# read photo
def test_read_photo_ok(client, photo):
    response = client.get(
        f"/api/photo/{photo['id']}"
    )
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data["photo_url"], str) 

def test_read_photo_fail_not_found(client, photo):
    response = client.get(
        f"/api/photo/{photo['id']}"
    )
    assert response.status_code == 404

# update tags
def test_update_photo_tags_ok_user(client, token, photo):
    # Authenticate as owner user
    response = client.get(
        f"/api/photo/{photo['id']}/tags",
        headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data["photo_url"], str) 

def test_update_photo_tags_ok_admin(client, admin_token, photo):
    # Authenticate as admin
    response = client.get(
        f"/api/photo/{photo['id']}/tags",
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data["photo_url"], str) 

def test_update_photo_tags_fail_no_permissions_user(client, token02, photo):
    # Authenticate as non-owner user
    response = client.get(
        f"/api/photo/{photo['id']}/tags",
        headers={'Authorization': f'Bearer {token02}'}
    )
    assert response.status_code == 401

def test_update_photo_tags_fail_no_permissions_moder(client, moder_token, photo):
    # Authenticate as moder
    response = client.get(
        f"/api/photo/{photo['id']}/tags",
        headers={'Authorization': f'Bearer {moder_token}'}
    )
    assert response.status_code == 401

def test_update_photo_tags_fail_not_found(client, token, photo):
    # authenticate
    response = client.get(
        f"/api/photo/{photo['id']}/tags",
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 404

def test_update_photo_tags_fail_error(client, token, photo):
    # authenticate
    response = client.get(
        f"/api/photo/{photo['id']}/tags",
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 422

# update description
def test_update_description_ok():
    ...

# transform
def transform_photo():
    ...

# qr
def test_get_photo_qr_ok():
    ...