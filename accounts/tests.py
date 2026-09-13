from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import KYCSubmission, UserProfile
from .services import review_kyc, send_verification_email, submit_kyc
from .tokens import email_verification_token


def _fake_document():
    return SimpleUploadedFile("id.jpg", b"fake-image-bytes", content_type="image/jpeg")


class KYCServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ada@example.com", email="ada@example.com", password="StrongPass123!")
        self.staff = User.objects.create_user(username="staff@example.com", email="staff@example.com", password="StrongPass123!", is_staff=True)

    def test_submit_kyc_sets_profile_pending(self):
        submission = submit_kyc(
            self.user,
            {
                "full_name": "Ada Lovelace",
                "date_of_birth": "1990-01-01",
                "id_type": KYCSubmission.IDType.NIN,
                "id_number": "12345678901",
                "id_document": _fake_document(),
                "address": "1 Lagos Way",
            },
        )
        self.user.profile.refresh_from_db()
        self.assertEqual(submission.status, KYCSubmission.Status.PENDING)
        self.assertEqual(self.user.profile.kyc_status, UserProfile.KYCStatus.PENDING)

    def test_review_kyc_approve_verifies_profile(self):
        submission = submit_kyc(
            self.user,
            {
                "full_name": "Ada Lovelace",
                "date_of_birth": "1990-01-01",
                "id_type": KYCSubmission.IDType.BVN,
                "id_number": "12345678901",
                "id_document": _fake_document(),
                "address": "1 Lagos Way",
            },
        )
        review_kyc(submission, approve=True, reviewer=self.staff)
        self.user.profile.refresh_from_db()
        submission.refresh_from_db()
        self.assertEqual(submission.status, KYCSubmission.Status.VERIFIED)
        self.assertEqual(self.user.profile.kyc_status, UserProfile.KYCStatus.VERIFIED)
        self.assertEqual(submission.reviewed_by, self.staff)
        self.assertIsNotNone(submission.reviewed_at)

    def test_review_kyc_approve_sends_notification_email(self):
        submission = submit_kyc(
            self.user,
            {
                "full_name": "Ada Lovelace",
                "date_of_birth": "1990-01-01",
                "id_type": KYCSubmission.IDType.BVN,
                "id_number": "12345678901",
                "id_document": _fake_document(),
                "address": "1 Lagos Way",
            },
        )
        mail.outbox.clear()
        review_kyc(submission, approve=True, reviewer=self.staff)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_review_kyc_reject_records_reason(self):
        submission = submit_kyc(
            self.user,
            {
                "full_name": "Ada Lovelace",
                "date_of_birth": "1990-01-01",
                "id_type": KYCSubmission.IDType.BVN,
                "id_number": "12345678901",
                "id_document": _fake_document(),
                "address": "1 Lagos Way",
            },
        )
        review_kyc(submission, approve=False, reviewer=self.staff, reason="Blurry document")
        self.user.profile.refresh_from_db()
        submission.refresh_from_db()
        self.assertEqual(submission.status, KYCSubmission.Status.REJECTED)
        self.assertEqual(submission.rejection_reason, "Blurry document")
        self.assertEqual(self.user.profile.kyc_status, UserProfile.KYCStatus.REJECTED)


class KYCFormValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ada@example.com", email="ada@example.com", password="StrongPass123!")
        self.user.profile.email_verified = True
        self.user.profile.save(update_fields=["email_verified"])
        self.client.login(username="ada@example.com", password="StrongPass123!")

    def test_bvn_must_be_11_digits(self):
        response = self.client.post(
            reverse("kyc_submit"),
            {
                "full_name": "Ada Lovelace",
                "date_of_birth": "1990-01-01",
                "id_type": KYCSubmission.IDType.BVN,
                "id_number": "123",
                "address": "1 Lagos Way",
                "id_document": _fake_document(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(KYCSubmission.objects.count(), 0)

    def test_unverified_email_blocks_kyc_submission(self):
        self.user.profile.email_verified = False
        self.user.profile.save(update_fields=["email_verified"])
        response = self.client.get(reverse("kyc_submit"))
        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(KYCSubmission.objects.count(), 0)

    def test_valid_submission_redirects_to_profile(self):
        response = self.client.post(
            reverse("kyc_submit"),
            {
                "full_name": "Ada Lovelace",
                "date_of_birth": "1990-01-01",
                "id_type": KYCSubmission.IDType.BVN,
                "id_number": "12345678901",
                "address": "1 Lagos Way",
                "id_document": _fake_document(),
            },
        )
        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(KYCSubmission.objects.count(), 1)


@override_settings(PAYMENT_PROVIDER="flutterwave")
class WithdrawalKYCGateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ada@example.com", email="ada@example.com", password="StrongPass123!")
        self.user.profile.email_verified = True
        self.user.profile.save(update_fields=["email_verified"])
        self.client.login(username="ada@example.com", password="StrongPass123!")

    def test_unverified_user_is_redirected_to_kyc(self):
        response = self.client.get(reverse("withdraw"))
        self.assertRedirects(response, reverse("kyc_submit"))

    def test_verified_user_can_reach_withdraw_form(self):
        self.user.profile.kyc_status = UserProfile.KYCStatus.VERIFIED
        self.user.profile.save(update_fields=["kyc_status"])
        response = self.client.get(reverse("withdraw"))
        self.assertEqual(response.status_code, 200)


class EmailVerificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ada@example.com", email="ada@example.com", password="StrongPass123!")

    def test_registration_sends_verification_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "full_name": "New User",
                "email": "newuser@example.com",
                "phone": "+2348012345678",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "accepted_terms": "on",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("newuser@example.com", mail.outbox[0].to)
        self.assertIn("/verify-email/", mail.outbox[0].body)

    def test_valid_token_marks_email_verified(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = email_verification_token.make_token(self.user)
        response = self.client.get(reverse("verify_email", kwargs={"uidb64": uidb64, "token": token}))
        self.assertRedirects(response, reverse("login"))
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.email_verified)
        self.assertIsNotNone(self.user.profile.email_verified_at)

    def test_invalid_token_does_not_verify(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(reverse("verify_email", kwargs={"uidb64": uidb64, "token": "bogus-token"}))
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.email_verified)

    def test_token_is_single_use_for_re_verification_state(self):
        # A token generated before verification should not verify again
        # once the profile's verified state has already changed via a
        # different token, since the hash incorporates email_verified.
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = email_verification_token.make_token(self.user)
        self.user.profile.email_verified = True
        self.user.profile.save(update_fields=["email_verified"])
        self.assertFalse(email_verification_token.check_token(self.user, token))

    def test_resend_when_unverified_sends_email(self):
        self.client.login(username="ada@example.com", password="StrongPass123!")
        response = self.client.get(reverse("resend_verification"))
        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(len(mail.outbox), 1)

    def test_resend_when_already_verified_sends_nothing(self):
        self.user.profile.email_verified = True
        self.user.profile.save(update_fields=["email_verified"])
        self.client.login(username="ada@example.com", password="StrongPass123!")
        self.client.get(reverse("resend_verification"))
        self.assertEqual(len(mail.outbox), 0)
