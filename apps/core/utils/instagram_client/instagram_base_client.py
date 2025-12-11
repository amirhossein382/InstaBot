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
        pass

    @abstractmethod
    def login(self, username: str, password: str):
        """Login user to instagram"""
        pass

    @abstractmethod
    def logout(self, username: str, password: str):
        """Logout user from instagram"""
        pass

    @abstractmethod
    def load_profile(self, username: str, **kwargs):
        """Return dict: {username, full_name, bio, followers_count, following_count, profile_pic_url}"""
        pass

    @abstractmethod
    def load_followers_in_chunk(self, account, **kwargs):
        """Return list of dicts: [{'pk':..., 'username':..., 'full_name':..., 'profile_pic_url':...}, ...]"""
        pass

    @abstractmethod
    def load_followings_in_chunk(self, account, **kwargs):
        """Return list of dicts: [{'pk':..., 'username':..., 'full_name':..., 'profile_pic_url':...}, ...]"""
        pass

    @abstractmethod
    def get_session(self) -> dict:
        """Return JSON serializable session."""
        pass

    @abstractmethod
    def set_session(self, session_data: dict):
        """Load saved session."""
        pass

    @abstractmethod
    def set_proxy(self, proxy: str):
        """Set proxy to each client."""
        pass
