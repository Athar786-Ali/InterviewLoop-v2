from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

from app.core.exceptions import AppError
from app.core.security import JwtService, OtpGenerator, PasswordHasher, RefreshTokenGenerator, TokenHasher, normalize_pem


def generate_rsa_key_pair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def test_password_and_token_hashers_round_trip():
    password_hash = PasswordHasher().hash("secret-password")
    token_hash = TokenHasher().hash("refresh-token")

    assert PasswordHasher().verify("secret-password", password_hash)
    assert not PasswordHasher().verify("wrong", password_hash)
    assert TokenHasher().verify("refresh-token", token_hash)
    assert not TokenHasher().verify("wrong", token_hash)


def test_generators_create_expected_token_shapes():
    otp = OtpGenerator().create()
    refresh = RefreshTokenGenerator().create()

    assert len(otp) == 6
    assert otp.isdigit()
    assert len(refresh) > 40


def test_jwt_service_creates_decodes_and_rejects_wrong_token_type(monkeypatch):
    private_key, public_key = generate_rsa_key_pair()
    monkeypatch.setattr("app.core.security.settings.jwt_private_key", private_key, raising=False)
    monkeypatch.setattr("app.core.security.settings.jwt_public_key", public_key, raising=False)
    monkeypatch.setattr("app.core.security.settings.jwt_algorithm", "RS256", raising=False)

    user_id = uuid4()
    session_id = uuid4()
    token, expires_in = JwtService().create_access_token(user_id, session_id)
    payload = JwtService().decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["sid"] == str(session_id)
    assert expires_in > 0

    wrong_type_token = jwt.encode({"sub": str(user_id), "type": "refresh"}, private_key, algorithm="RS256")
    with pytest.raises(AppError) as error:
        JwtService().decode_access_token(wrong_type_token)

    assert error.value.code == "INVALID_ACCESS_TOKEN"


def test_jwt_service_normalizes_escaped_newline_pem_values(monkeypatch):
    private_key, public_key = generate_rsa_key_pair()
    monkeypatch.setattr("app.core.security.settings.jwt_private_key", private_key.replace("\n", "\\n"), raising=False)
    monkeypatch.setattr("app.core.security.settings.jwt_public_key", public_key.replace("\n", "\\n"), raising=False)
    monkeypatch.setattr("app.core.security.settings.jwt_algorithm", "RS256", raising=False)

    token, _ = JwtService().create_access_token(uuid4(), uuid4())

    assert JwtService().decode_access_token(token)["type"] == "access"
    assert normalize_pem(public_key.replace("\n", "\\n")).startswith("-----BEGIN PUBLIC KEY-----")


def test_jwt_service_configuration_errors(monkeypatch):
    monkeypatch.setattr("app.core.security.settings.jwt_private_key", "", raising=False)

    with pytest.raises(AppError) as error:
        JwtService().create_access_token(uuid4(), uuid4())

    assert error.value.code == "AUTH_CONFIGURATION_ERROR"

    monkeypatch.setattr("app.core.security.settings.jwt_public_key", "", raising=False)

    with pytest.raises(AppError) as decode_error:
        JwtService().decode_access_token("token")

    assert decode_error.value.code == "AUTH_CONFIGURATION_ERROR"
