from core.db.session import async_session_factory, UnitOfWork
from core.exceptions.friends import (
    AlreadySentRequest,
    AlreadyReceivedRequest,
    AlreadyFriends,
    SameUser,
    FriendshipNotFound
)
from app.user.models import User
from app.user.service import UserService
from .friendship_status_enum import FriendshipStatusEnum
from .repository import FriendsRepository
from .models import Friendship
from .schemas import FriendshipOut


class FriendshipService:
    def __init__(self):
        self.friendship_repository = FriendsRepository()
        self.user_service = UserService()

    async def get_friends(self, user_id: str) -> list[FriendshipOut]:
        async with UnitOfWork(async_session_factory()) as uow:
            res = await self.friendship_repository.find_friends_by_user_id(uow.session, user_id)

        return [await self._construct_friendship(friendship) for friendship in res]

    async def get_sent_friendship_requests(self, user_id: str):
        async with UnitOfWork(async_session_factory()) as uow:
            res = await self.friendship_repository.find_sent_requests_by_user_id(uow.session, user_id)

        return [await self._construct_friendship(friendship) for friendship in res]

    async def get_received_friendship_requests(self, user_id: str):
        async with UnitOfWork(async_session_factory()) as uow:
            res = await self.friendship_repository.find_received_requests_by_user_id(uow.session, user_id)

        return [await self._construct_friendship(friendship) for friendship in res]

    async def send_friend_request(self, user_id: str, friend_id: str) -> FriendshipOut:
        if user_id == friend_id:
            raise SameUser()
        async with UnitOfWork(async_session_factory()) as uow:
            request_in_db: Friendship = await self.friendship_repository.find_by_requester_id_address_id(
                session=uow.session,
                requester_id=user_id,
                addressee_id=friend_id
            )

            if request_in_db:
                if request_in_db.status == FriendshipStatusEnum.accepted:
                    raise AlreadyFriends()
                if request_in_db.status == FriendshipStatusEnum.sent:
                    raise AlreadySentRequest()
                if request_in_db.status == FriendshipStatusEnum.pending:
                    raise AlreadyReceivedRequest()

            request_sent, request_pending = await self.friendship_repository.add(
                session=uow.session,
                requester_id=user_id,
                addressee_id=friend_id
            )

            # refresh the session to get the updated values
            await uow.refresh(request_sent)

        return await self._construct_friendship(request_sent)

    async def accept_friendship_request(self, friendship_id: str) -> FriendshipOut:
        async with UnitOfWork(async_session_factory()) as uow:
            friendship = await self.friendship_repository.find_by_id(session=uow.session, friendship_id=friendship_id)
            if not friendship:
                raise FriendshipNotFound()

            friendship.status = FriendshipStatusEnum.accepted

            await uow.commit()
            await uow.refresh(friendship)

        return await self._construct_friendship(friendship)

    async def delete_friendship(self, friendship_id: str) -> None:
        raise NotImplementedError()

    async def decline_friendship_request(self, friendship_id: str) -> None:
        raise NotImplementedError()

    async def is_users_friends(self, user_id: str, friend_id: str) -> bool:
        async with UnitOfWork(async_session_factory()) as uow:
            friendship = await self.friendship_repository.find_by_requester_id_address_id(
                session=uow.session,
                requester_id=user_id,
                addressee_id=friend_id
            )

        if friendship:
            return friendship.status == FriendshipStatusEnum.accepted

        return False

    async def _construct_friendship(self, friendship: Friendship) -> FriendshipOut:
        return FriendshipOut.model_validate({
            **friendship.__dict__,
            "user": await self.user_service.set_presigned_url_to_user(friendship.addressee)
        })
