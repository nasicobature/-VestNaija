class KYCProvider:
    def submit(self, user, data):
        raise NotImplementedError

    def get_status(self, user):
        raise NotImplementedError


class ManualReviewKYCProvider(KYCProvider):
    """No external identity API is called. A staff member checks the
    submitted BVN/NIN and ID document in Django admin and approves or
    rejects the submission by hand."""

    def submit(self, user, data):
        from .models import KYCSubmission

        return KYCSubmission.objects.create(user=user, **data)

    def get_status(self, user):
        return user.profile.kyc_status


class OfficialKYCProvider(KYCProvider):
    """Swap ManualReviewKYCProvider for this once you have credentials for a
    real BVN/NIN verification vendor (e.g. Dojah, Youverify, Prembly)."""

    def submit(self, user, data):
        raise NotImplementedError("Real KYC API integration requires provider credentials and documentation.")

    def get_status(self, user):
        raise NotImplementedError("Real KYC status lookup requires provider credentials.")


def get_kyc_provider():
    from django.conf import settings

    if getattr(settings, "KYC_PROVIDER", "manual") == "manual":
        return ManualReviewKYCProvider()
    return OfficialKYCProvider()
