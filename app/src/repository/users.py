from operator import not_
from libgravatar import Gravatar
from sqlalchemy.orm import Session

from app.src.database.models import User, Photo, Comment
from app.src.schemas import UserModel, RoleOptions


async def get_user_by_id(user_id: int, db: Session) -> User | None:
    """
    Retrieves a user with the specified id.
    Args:
        photo_id (int): id of the user to retrieve.
        db (Session): database session
    Returns:
        User or None: The user with the specified email, or None if it does not exist.
    """
    return db.query(User).filter(User.id == user_id).first()


async def get_user_by_email(email: str, db: Session) -> User | None:
    """
    Retrieves a user with the specified email.

    Args:
        email (str): The email of the user to retrieve.
        db (Session, optional): database session.
    Returns:
        User | None: The user with the specified email, or None if it does not exist.

    """
    return db.query(User).filter(User.email == email).first()


async def get_user_by_username(username: str, db: Session) -> User | None:
    """
    Retrieves a user with the specified username.

    Args:
        username (str): The username of the user to retrieve.
        db (Session, optional): database session.
    Returns:
        User | None: The user with the specified username, or None if it does not exist.

    """
    return db.query(User).filter(User.username == username).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    Create a new user

    Args:
        body (UserModel): The data for the user to create.
        db (Session): database session.

    Returns:
        [User]: he newly created user
    """    
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.dict(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    Update refresh token in the database

    Args:
        user (User): The user to update the token for.
        token (str): The token to update.
        db (Session): The database session.
    """    
    user.refresh_token = token
    db.commit()


async def update_avatar(email: str, url: str, db: Session) -> User:
    """
    Update user's avatar

    Args:
        email (str):  Email of the specific user to update an avatar for.
        url (str): The URL of the avatar picture.
        db (Session): The database session.

    Returns:
        [User]: Updated user.
    """    
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def confirmed_email(email: str, db: Session) -> None:
    """
    Check email confirmation flag in the database

    Args:
        email (str): The email of the user to confirm.
        db (Session): The email of the user to confirm.
    Returns:
        None
    """    
    user = await get_user_by_email(email, db)
    user.confirmed = True
    if user.id == 1:
        user.role = "admin"
    db.commit()


async def change_user_role(user: User, role: RoleOptions, db: Session) -> User:
    """
    Change the role of the user

    Args:
        user (User): The user to change role.
        role (RoleOptions): New role for user.
        db (Session): The database session.

    Returns:
        [User]: Updated user.
    """    
    user.role = role
    db.commit()
    return user


async def ban_user(user: User, banned: bool, db: Session) -> str:
    """
    Set user ban flag in the database

    Args:
        user (User): The user to ban.
        banned (bool): True = banned, False = unbanned
        db (Session): The database session.

    Returns:
        [str]: Message with the username of banned user.
    """    
    user.banned = banned
    db.commit()
    return f'User {user.username} has been {"un"*not_(banned)}banned'


async def change_user_username(user: User, username: str, db: Session) -> User:
    """
    Change the username of the user

    Args:
        user (User): The user to change username.
        username (str): New username for user.
        db (Session): The database session.

    Returns:
        [User]: Updated user.
    """
    user.username = username
    db.commit()
    return user


async def change_user_email(user: User, email: str, db: Session) -> User:
    """
    Change the email of the user

    Args:
        user (User): The user to change email.
        email (str): New email for user.
        db (Session): The database session.

    Returns:
        [User]: Updated user.
    """
    user.email = email
    user.confirmed = False
    db.commit()
    return user


def get_users_photos(user: User, db: Session) -> list:
    """
    Get list of user's photos.

    Args:
        user (User): The user to get photos.
        db (Session): The database session.

    Returns:
        [list]: User's photos list.
    """
    return db.query(Photo).filter(Photo.owner_id == user.id).all()


def get_users_comments(user: User, db: Session) -> list:
    """
    Get list of user's comments.

    Args:
        user (User): The user to get comments.
        db (Session): The database session.

    Returns:
        [list]: User's comments list.
    """
    return db.query(Comment).filter(Comment.user_id == user.id).all()
