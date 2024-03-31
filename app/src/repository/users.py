from libgravatar import Gravatar
from sqlalchemy.orm import Session

from app.src.database.models import User
from app.src.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> User | None:
    """
    Retrieves a user with the specified email.

    :param email: The email of the user to retrieve.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: The user with the specified email, or None if it does not exist.
    :rtype: User | None
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    Creates a new user.

    :param body: The data for the user to create.
    :type body: UserModel
    :param db: The database session.
    :type db: Session
    :return: The newly created user.
    :rtype: User
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
    Updates a token for a specific user.

    :param user: The user to update the token for.
    :type user: User
    :param token: The token to update.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: None.
    :rtype: None
    """
    user.refresh_token = token
    db.commit()


async def update_avatar(email: str, url: str, db: Session) -> User:
    """
    Updates an avatar for a specific user.

    :param email: Email of the specific user to update an avatar for.
    :type email: str
    :param url: The URL of the avatar.
    :type url: str
    :param db: The database session.
    :type db: Session
    :return: Updated user.
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def confirmed_email(email: str, db: Session) -> None:
    """
    Change param of confirmation email for specific user.

    :param email: The email of the user to confirm.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    if user.id == 1:
        user.role = "admin"
    db.commit()


def change_user_role(user: User, role: str, db: Session) -> User:
    """
    Change param of role for specific user.

    :param user: The user to change role.
    :type user: User
    :param role: New role for user.
    :type role: str
    :param db: The database session.
    :type db: Session
    :return: Updated user.
    :rtype: User
    """
    user.role = role
    db.commit()
    return user


def ban_user(user: User, db: Session) -> str:
    """
    Ban user.

    :param user: The user to ban.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: Message with username of banned user.
    :rtype: str
    """
    user.banned = True
    db.commit()
    return f"{user.username} has been banned"


def unban_user(user: User, db: Session) -> str:
    """
    Unban user.

    :param user: The user to unban.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: Message with username of unbanned user.
    :rtype: str
    """
    user.banned = False
    db.commit()
    return f"{user.username} has been unbanned"
