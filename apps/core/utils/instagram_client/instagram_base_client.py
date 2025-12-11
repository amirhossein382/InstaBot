from abc import ABC, abstractmethod


class InstagramBaseClient(ABC):
    @abstractmethod
    def __init__(self, settings=None, proxy=None):
        pass

    @staticmethod
    def _clean_user_object(user):
        return {
            "user_pk": int(user.pk),
            "username": user.username,
            "full_name": user.full_name,
            "profile_pic_url": str(user.profile_pic_url),
        }

    @staticmethod
    def _clean_profile_object(data, account_pk):
        data["account"] = account_pk
        data["user_pk"] = int(data["pk"])
        data["profile_pic_url"] = str(data["profile_pic_url"])
        return data

    @abstractmethod
    def get_account_client(self, settings, proxy):
        """Get account client"""
        raise NotImplementedError

    @abstractmethod
    def login(self, username: str, password: str, proxy: str, **kwargs):
        """Login user to instagram"""
        raise NotImplementedError

    @abstractmethod
    def logout(self, username: str, password: str):
        """Logout user from instagram"""
        raise NotImplementedError

    @abstractmethod
    def load_profile(self, username: str, **kwargs):
        """Return dict: {username, full_name, bio, followers_count, following_count, profile_pic_url}"""
        raise NotImplementedError

    @abstractmethod
    def load_followers_in_chunk(self, account, **kwargs):
        """Return list of dicts: [{'pk':..., 'username':..., 'full_name':..., 'profile_pic_url':...}, ...]"""
        raise NotImplementedError

    @abstractmethod
    def load_followings_in_chunk(self, account, **kwargs):
        """Return list of dicts: [{'pk':..., 'username':..., 'full_name':..., 'profile_pic_url':...}, ...]"""
        raise NotImplementedError

    @abstractmethod
    def get_session(self) -> dict:
        """Return JSON serializable session."""
        raise NotImplementedError

    @abstractmethod
    def set_session(self, session_data: dict):
        """Load saved session."""
        raise NotImplementedError

    @abstractmethod
    def set_proxy(self, proxy: str):
        """Set proxy to each client."""
        raise NotImplementedError

    @property
    @abstractmethod
    def get_user_id(self):
        """Return user id"""
        raise NotImplementedError
