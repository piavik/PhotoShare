import pytest

from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import UploadFile

from app.src.schemas import PhotoModel

from app.src.services import cloudinary_services

# @patch("app.src.service.cloudinary_services.upload_photo", )
@pytest.mark.skip(reason="not ready - issues with cloudinary api mock")
def test_create_photo_ok(client, token, photo, monkeypatch):
    # authenticate
    # mock cloudinary request - there are issues with it, not working
    mock_cloudinary = MagicMock()
    monkeypatch.setattr("app.src.services.cloudinary_services.upload_photo", mock_cloudinary)
    access_token = token["access_token"] 
    response = client.post(
        f"/api/photos/upload",
        data={"file": MagicMock(spec=PhotoModel), "description": photo.description, "tags": []},
        headers={'Authorization': f'Bearer {access_token}'}
    )
    data = response.json()
    print(data)
    assert data["detail"] == "Photo successfully uploaded"
    # db entry exists

# @patch("app.src.service.cloudinary_services.upload_photo")
@pytest.mark.skip(reason="not ready - issues with cloudinary api mock")
def test_create_photo_failure_cloudinary(client, token, photo):
    # authenticate
    access_token = token["access_token"] 
    # mock cloudinary request
    cloudinary_services.upload_photo.return_value.error = { "message": "Failed to upload photo"}
    response = client.post(
        f"/api/photos/upload",
        json=photo,
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 500

# delete photo
@pytest.mark.skip(reason="not ready - need to fit photo.user_id = user.id")
def test_delete_photo_ok_user(client, token, photo):
    # authenticate as owner user
    access_token = token["access_token"] 
    response = client.delete(
        f"/api/photos/upload",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    data = response.json()
    assert response.status_code == 200
    assert data["detail"] == "Photo succesfuly deleted"
    # no entry in DB
    # no response by URL

def test_delete_photo_ok_admin(client, admin_token, photo):
    # authenticate as admin
    access_token = admin_token["access_token"] 
    response = client.delete(
        f"/api/photos/{photo.id}",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    data = response.json()
    assert response.status_code == 200
    assert data["detail"] == "Photo succesfuly deleted"
    # no entry in DB
    # no response by URL

def test_delete_photo_fail_moder(client, moder_token, photo):
    # authenticate as moder
    access_token = moder_token["access_token"] 
    response = client.delete(
        f"/api/photos/{photo.id}",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 403

def test_delete_photo_fail_not_found(client, token):
    # authenticate
    access_token = token["access_token"] 
    response = client.delete(
        f"/api/photos/99999999",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 404

def test_delete_photo_fail_no_permissions_user(client, token, photo):
    # authenticate as non-owner user
    access_token = token["access_token"] 
    response = client.delete(
        f"/api/photos/{photo.id}",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 403

def test_delete_photo_fail_no_permissions_moder(client, moder_token, photo):
    # authenticate as moder
    access_token = moder_token["access_token"] 
    response = client.delete(
        f"/api/photos/{photo.id}",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 403

# read photo
def test_read_photo_ok(client, photo):
    response = client.get(
        f"/api/photos/{photo.id}"
    )
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data["photo_url"], str) 

def test_read_photo_fail_not_found(client, photo):
    response = client.get(
        f"/api/photos/99999999"
    )
    assert response.status_code == 404

# update tags
@pytest.mark.skip(reason="not ready - need to fit photo.user_id = user.id")
def test_update_photo_tags_ok_user(client, token, photo):
    # Authenticate as owner user
    access_token = token["access_token"] 
    response = client.patch(
        f"/api/photos/{photo.id}/tags",
        data={"tags": 'tag1 tag2 tag_new'},
        headers={'Authorization': f'Bearer {access_token}'}
    )
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data["photo_url"], str) 

def test_update_photo_tags_ok_admin(client, admin_token, photo):
    # Authenticate as admin
    access_token = admin_token["access_token"] 
    response = client.patch(
        f"/api/photos/{photo.id}/tags",
        data={"tags": 'tag1 tag2 tag_new'},
        headers={'Authorization': f'Bearer {access_token}'}
    )
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data["photo_url"], str) 

def test_update_photo_tags_fail_no_permissions_user(client, token, photo):
    # Authenticate as non-owner user
    access_token = token["access_token"] 
    response = client.patch(
        f"/api/photos/{photo.id}/tags",
        data={"tags": 'tag1 tag2 tag_new'},
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 403

def test_update_photo_tags_fail_no_permissions_moder(client, moder_token, photo):
    # Authenticate as moder
    access_token = moder_token["access_token"] 
    response = client.patch(
        f"/api/photos/{photo.id}/tags",
        data={"tags": 'tag1 tag2 tag_new'},
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 403

def test_update_photo_tags_fail_not_found(client, token, photo):
    # authenticate
    access_token = token["access_token"] 
    response = client.patch(
        f"/api/photos/99999999/tags",
        data={"tags": 'tag1 tag2 tag_new'},
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 404

def test_update_photo_tags_fail_error(client, token, photo):
    # authenticate
    access_token = token["access_token"] 
    response = client.patch(
        f"/api/photos/{photo.id}/tags",
        data={"tags": 'unwalid_tag_very_logh_here_blablablablabla'},
        headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == 422

# # update description
# def test_update_description_ok():
#     ...

# # transform
# def transform_photo():
#     ...

# # qr
# def test_get_photo_qr_ok():
#     ...


if __name__ == "__main__":
    unittest.main()    
    