# VestNaija

VestNaija is a Django prototype for a Nigerian demo investment wallet and IPO trading platform.

The application runs in demo/sandbox mode only:

- No real money is accepted.
- No real securities are traded.
- No SEC, NGX, CSCS, bank, broker, or Dangote Refinery API integration is claimed or implemented.
- Future real integrations should be added through the provider interfaces after licensing, authorization, credentials, and official documentation are available.

## Local Setup

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

If PostgreSQL environment variables from `.env.example` are present, Django uses PostgreSQL. Without them, it falls back to local SQLite for development and tests.

Demo login:

```text
nasir@example.com
DemoPass123!
```

## Provider Boundaries

- `payments.providers.PaymentProvider`
- `payments.providers.MockPaymentProvider`
- `trading.providers.TradingProvider`
- `trading.providers.BrokerProvider`
- `trading.providers.MockTradingProvider`
- `accounts.kyc.KYCProvider`
- `accounts.kyc.MockKYCProvider`

Official providers intentionally raise `NotImplementedError` until real compliance and integration requirements are supplied.
