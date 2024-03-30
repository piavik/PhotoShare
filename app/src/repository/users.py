from libgravatar import Gravatar
from sqlalchemy.orm import Session

from app.src.database.models import User
from app.src.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> User | None:
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    **Create user**

    Args:
        body (UserModel): [description]
        db (Session): [description]

    Returns:
        [User]: [description]
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
    **Update refresh token in the database**

    Args:
        user (User): [description]
        token (str): [description]
        db (Session): [description]
    """    
    user.refresh_token = token
    db.commit()


async def update_avatar(email: str, url: str, db: Session) -> User:
    """
    **Update avatar**

    Args:
        email (str): [description]
        url (str): [description]
        db (Session): [description]

    Returns:
        [User]: [description]
    """    
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def confirmed_email(email: str, db: Session) -> None:
    """
    **Check email confirmation flag in the database**

    Args:
        email (str): [description]
        db (Session): [description]
    """    
    user = await get_user_by_email(email, db)
    user.confirmed = True
    if user.id == 1:
        user.role = "admin"
    db.commit()


def change_user_role(user: User, role: str, db: Session) -> User:
    """
    **Change the role of the user**

    Args:
        user (User): [description]
        role (str): [description]
        db (Session): [description]

    Returns:
        [User]: [description]
    """    
    user.role = role
    db.commit()
    return user


def ban_user(user: User, db: Session) -> str:
    """
    **Set user ban flag in the database**

    Args:
        user (User): [description]
        db (Session): [description]

    Returns:
        [str]: [description]
    """    
    user.banned = True
    db.commit()
    return f"{user.username} has been banned"


def unban_user(user: User, db: Session) -> str:
    """
    **Clear user ban flag in the database**

    Args:
        user (User): [description]
        db (Session): [description]

    Returns:
        str: [description]
    """    
    user.banned = False
    db.commit()
    return f"{user.username} has been unbanned"
