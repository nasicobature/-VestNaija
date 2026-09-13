class KYCProvider:
    def start_verification(self, user):
        raise NotImplementedError

    def get_status(self, user):
        raise NotImplementedError


class MockKYCProvider(KYCProvider):
    def start_verification(self, user):
        return {"status": "demo_only", "message": "KYC is a placeholder in demo mode."}

    def get_status(self, user):
        return user.profile.kyc_status


class OfficialKYCProvider(KYCProvider):
    def start_verification(self, user):
        raise NotImplementedError("Official KYC requires approved provider documentation, credentials, and compliance review.")

    def get_status(self, user):
        raise NotImplementedError("Official KYC status is unavailable in demo mode.")
