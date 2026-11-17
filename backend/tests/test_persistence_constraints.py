"""PostgreSQL-enforced persistence invariants for the NexDrop data model."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, async_sessionmaker
from sqlalchemy.orm.exc import StaleDataError

import nexdrop_api.db.models  # noqa: F401
from nexdrop_api.db.base import Base
from nexdrop_api.db.models import Transfer, User


async def create_user(connection: AsyncConnection, suffix: str) -> UUID:
    user_id = uuid4()
    email = f"{suffix}-{user_id.hex[:10]}@example.test"
    await connection.execute(
        text(
            "INSERT INTO users (id, email, email_normalized, status, locale) "
            "VALUES (:id, :email, :normalized, 'active', 'fr')"
        ),
        {"id": user_id, "email": email, "normalized": email.lower()},
    )
    return user_id


async def create_device(connection: AsyncConnection, user_id: UUID) -> UUID:
    device_id = uuid4()
    await connection.execute(
        text(
            "INSERT INTO devices "
            "(id, user_id, installation_id, name, platform, status) "
            "VALUES (:id, :user_id, :installation, 'Test PC', 'windows', 'active')"
        ),
        {"id": device_id, "user_id": user_id, "installation": uuid4()},
    )
    return device_id


async def create_session(
    connection: AsyncConnection, user_id: UUID, device_id: UUID | None = None
) -> UUID:
    session_id = uuid4()
    await connection.execute(
        text(
            "INSERT INTO sessions (id, user_id, device_id, expires_at) "
            "VALUES (:id, :user_id, :device_id, :expires_at)"
        ),
        {
            "id": session_id,
            "user_id": user_id,
            "device_id": device_id,
            "expires_at": datetime.now(UTC) + timedelta(days=2),
        },
    )
    return session_id


async def create_transfer(connection: AsyncConnection, sender_id: UUID) -> UUID:
    transfer_id = uuid4()
    plan_id = await connection.scalar(text("SELECT id FROM plans WHERE code = 'free'"))
    assert plan_id is not None
    await connection.execute(
        text(
            "INSERT INTO transfers "
            "(id, created_by_user_id, plan_id, status, total_bytes, item_count, "
            "plan_code_snapshot, max_transfer_bytes_snapshot, expires_at) "
            "VALUES (:id, :sender, :plan, 'awaiting_receiver', 1234, 1, "
            "'free', 10000000000, :expires_at)"
        ),
        {
            "id": transfer_id,
            "sender": sender_id,
            "plan": plan_id,
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
        },
    )
    return transfer_id


async def create_participant(
    connection: AsyncConnection,
    transfer_id: UUID,
    user_id: UUID,
    role: str,
) -> UUID:
    participant_id = uuid4()
    await connection.execute(
        text(
            "INSERT INTO transfer_participants "
            "(id, transfer_id, user_id, role, response_status) "
            "VALUES (:id, :transfer, :user, :role, :response)"
        ),
        {
            "id": participant_id,
            "transfer": transfer_id,
            "user": user_id,
            "role": role,
            "response": "accepted" if role == "sender" else "pending",
        },
    )
    return participant_id


@pytest.mark.asyncio
async def test_model_metadata_registers_all_thirteen_business_tables() -> None:
    expected = {
        "users",
        "devices",
        "sessions",
        "session_refresh_tokens",
        "plans",
        "transfers",
        "transfer_participants",
        "transfer_invitations",
        "transfer_invitation_redemptions",
        "transfer_events",
        "transfer_usage_records",
        "subscriptions",
        "payments",
    }
    assert set(Base.metadata.tables) == expected


@pytest.mark.asyncio
async def test_free_plan_has_approved_decimal_ten_gb_limit(migrated_test_db) -> None:
    result = await migrated_test_db.execute(
        text("SELECT name, max_transfer_bytes, is_active FROM plans WHERE code = 'free'")
    )
    row = result.one()
    assert row.name == "Free"
    assert row.max_transfer_bytes == 10_000_000_000
    assert row.is_active is True


@pytest.mark.asyncio
async def test_database_allows_only_one_sender_and_one_recipient_per_transfer(
    migrated_test_db,
) -> None:
    sender_id = await create_user(migrated_test_db, "sender")
    second_sender_id = await create_user(migrated_test_db, "sender-two")
    recipient_id = await create_user(migrated_test_db, "recipient")
    second_recipient_id = await create_user(migrated_test_db, "recipient-two")
    transfer_id = await create_transfer(migrated_test_db, sender_id)

    await create_participant(migrated_test_db, transfer_id, sender_id, "sender")
    await create_participant(migrated_test_db, transfer_id, recipient_id, "recipient")

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await create_participant(migrated_test_db, transfer_id, second_sender_id, "sender")

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await create_participant(
                migrated_test_db, transfer_id, second_recipient_id, "recipient"
            )


@pytest.mark.asyncio
async def test_session_cannot_reference_another_users_device(migrated_test_db) -> None:
    owner_id = await create_user(migrated_test_db, "device-owner")
    other_user_id = await create_user(migrated_test_db, "other-user")
    device_id = await create_device(migrated_test_db, owner_id)

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await create_session(migrated_test_db, other_user_id, device_id)


@pytest.mark.asyncio
async def test_only_one_unconsumed_refresh_token_can_exist_per_session(
    migrated_test_db,
) -> None:
    user_id = await create_user(migrated_test_db, "session-user")
    session_id = await create_session(migrated_test_db, user_id)
    first_token_id = uuid4()
    second_token_id = uuid4()
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=1)

    await migrated_test_db.execute(
        text(
            "INSERT INTO session_refresh_tokens "
            "(id, session_id, token_hash, issued_at, expires_at) "
            "VALUES (:id, :session, :hash, :issued, :expires)"
        ),
        {
            "id": first_token_id,
            "session": session_id,
            "hash": b"a" * 32,
            "issued": now,
            "expires": expires_at,
        },
    )

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO session_refresh_tokens "
                    "(id, session_id, token_hash, issued_at, expires_at) "
                    "VALUES (:id, :session, :hash, :issued, :expires)"
                ),
                {
                    "id": second_token_id,
                    "session": session_id,
                    "hash": b"b" * 32,
                    "issued": now,
                    "expires": expires_at,
                },
            )

    await migrated_test_db.execute(
        text("UPDATE session_refresh_tokens SET consumed_at = :now WHERE id = :id"),
        {"now": now, "id": first_token_id},
    )
    await migrated_test_db.execute(
        text(
            "INSERT INTO session_refresh_tokens "
            "(id, session_id, token_hash, issued_at, expires_at) "
            "VALUES (:id, :session, :hash, :issued, :expires)"
        ),
        {
            "id": second_token_id,
            "session": session_id,
            "hash": b"b" * 32,
            "issued": now,
            "expires": expires_at,
        },
    )


@pytest.mark.asyncio
async def test_invitation_redemption_cannot_cross_transfer_boundaries(
    migrated_test_db,
) -> None:
    sender_a = await create_user(migrated_test_db, "sender-a")
    sender_b = await create_user(migrated_test_db, "sender-b")
    recipient_b = await create_user(migrated_test_db, "recipient-b")
    transfer_a = await create_transfer(migrated_test_db, sender_a)
    transfer_b = await create_transfer(migrated_test_db, sender_b)
    participant_b = await create_participant(migrated_test_db, transfer_b, recipient_b, "recipient")
    invitation_id = uuid4()
    now = datetime.now(UTC)

    await migrated_test_db.execute(
        text(
            "INSERT INTO transfer_invitations "
            "(id, transfer_id, created_by_user_id, kind, token_digest, expires_at) "
            "VALUES (:id, :transfer, :creator, 'link', :digest, :expires)"
        ),
        {
            "id": invitation_id,
            "transfer": transfer_a,
            "creator": sender_a,
            "digest": b"i" * 32,
            "expires": now + timedelta(hours=1),
        },
    )

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO transfer_invitation_redemptions "
                    "(id, invitation_id, participant_id, transfer_id, user_id) "
                    "VALUES (:id, :invitation, :participant, :transfer, :user)"
                ),
                {
                    "id": uuid4(),
                    "invitation": invitation_id,
                    "participant": participant_b,
                    "transfer": transfer_a,
                    "user": recipient_b,
                },
            )


@pytest.mark.asyncio
async def test_usage_record_is_unique_and_bound_to_its_participant(migrated_test_db) -> None:
    sender_id = await create_user(migrated_test_db, "usage-sender")
    recipient_id = await create_user(migrated_test_db, "usage-recipient")
    transfer_id = await create_transfer(migrated_test_db, sender_id)
    participant_id = await create_participant(
        migrated_test_db, transfer_id, recipient_id, "recipient"
    )
    record_id = uuid4()

    values = {
        "id": record_id,
        "transfer": transfer_id,
        "participant": participant_id,
        "user": recipient_id,
        "bytes": 1234,
    }
    insert = text(
        "INSERT INTO transfer_usage_records "
        "(id, transfer_id, participant_id, user_id, bytes_transferred) "
        "VALUES (:id, :transfer, :participant, :user, :bytes)"
    )
    await migrated_test_db.execute(insert, values)

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(insert, {**values, "id": uuid4()})


@pytest.mark.asyncio
async def test_only_one_effective_subscription_is_allowed_per_user(migrated_test_db) -> None:
    user_id = await create_user(migrated_test_db, "subscriber")
    pro_plan_id = uuid4()
    await migrated_test_db.execute(
        text(
            "INSERT INTO plans (id, code, name, max_transfer_bytes, is_active) "
            "VALUES (:id, 'test-pro', 'Test Pro', NULL, false)"
        ),
        {"id": pro_plan_id},
    )

    insert = text(
        "INSERT INTO subscriptions (id, user_id, plan_id, status) "
        "VALUES (:id, :user, :plan, 'active')"
    )
    await migrated_test_db.execute(insert, {"id": uuid4(), "user": user_id, "plan": pro_plan_id})

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                insert, {"id": uuid4(), "user": user_id, "plan": pro_plan_id}
            )


@pytest.mark.asyncio
async def test_payment_subscription_must_belong_to_the_same_user(migrated_test_db) -> None:
    subscriber_id = await create_user(migrated_test_db, "paying-user")
    other_user_id = await create_user(migrated_test_db, "different-user")
    plan_id = await migrated_test_db.scalar(text("SELECT id FROM plans WHERE code = 'free'"))
    subscription_id = uuid4()
    await migrated_test_db.execute(
        text(
            "INSERT INTO subscriptions (id, user_id, plan_id, status) "
            "VALUES (:id, :user, :plan, 'active')"
        ),
        {"id": subscription_id, "user": subscriber_id, "plan": plan_id},
    )

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO payments "
                    "(id, user_id, subscription_id, provider, amount_minor, currency, status) "
                    "VALUES (:id, :user, :subscription, 'test', 100, 'USD', 'pending')"
                ),
                {
                    "id": uuid4(),
                    "user": other_user_id,
                    "subscription": subscription_id,
                },
            )


@pytest.mark.asyncio
async def test_negative_transfer_size_is_rejected_by_postgresql(migrated_test_db) -> None:
    sender_id = await create_user(migrated_test_db, "size-sender")
    plan_id = await migrated_test_db.scalar(text("SELECT id FROM plans WHERE code = 'free'"))

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO transfers "
                    "(id, created_by_user_id, plan_id, status, total_bytes, item_count, "
                    "plan_code_snapshot, max_transfer_bytes_snapshot, expires_at) "
                    "VALUES (:id, :user, :plan, 'awaiting_receiver', -1, 1, "
                    "'free', 10000000000, :expires)"
                ),
                {
                    "id": uuid4(),
                    "user": sender_id,
                    "plan": plan_id,
                    "expires": datetime.now(UTC) + timedelta(hours=1),
                },
            )


@pytest.mark.asyncio
async def test_transfer_cannot_exceed_its_recorded_plan_limit(migrated_test_db) -> None:
    sender_id = await create_user(migrated_test_db, "quota-sender")
    plan_id = await migrated_test_db.scalar(text("SELECT id FROM plans WHERE code = 'free'"))

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO transfers "
                    "(id, created_by_user_id, plan_id, status, total_bytes, item_count, "
                    "plan_code_snapshot, max_transfer_bytes_snapshot, expires_at) "
                    "VALUES (:id, :user, :plan, 'awaiting_receiver', 10000000001, 1, "
                    "'free', 10000000000, :expires)"
                ),
                {
                    "id": uuid4(),
                    "user": sender_id,
                    "plan": plan_id,
                    "expires": datetime.now(UTC) + timedelta(hours=1),
                },
            )


@pytest.mark.asyncio
async def test_refresh_token_rotation_cannot_cross_sessions(migrated_test_db) -> None:
    user_id = await create_user(migrated_test_db, "rotation-owner")
    session_a = await create_session(migrated_test_db, user_id)
    session_b = await create_session(migrated_test_db, user_id)
    now = datetime.now(UTC)
    expires = now + timedelta(days=1)
    token_a = uuid4()
    token_b = uuid4()

    insert = text(
        "INSERT INTO session_refresh_tokens "
        "(id, session_id, token_hash, issued_at, expires_at) "
        "VALUES (:id, :session, :hash, :issued, :expires)"
    )
    await migrated_test_db.execute(
        insert,
        {"id": token_a, "session": session_a, "hash": b"c" * 32, "issued": now, "expires": expires},
    )
    await migrated_test_db.execute(
        insert,
        {"id": token_b, "session": session_b, "hash": b"d" * 32, "issued": now, "expires": expires},
    )

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text("UPDATE session_refresh_tokens SET replaced_by_id = :target WHERE id = :id"),
                {"target": token_b, "id": token_a},
            )


@pytest.mark.asyncio
async def test_invitation_redemption_requires_recipient_participant(migrated_test_db) -> None:
    sender_id = await create_user(migrated_test_db, "redemption-sender")
    transfer_id = await create_transfer(migrated_test_db, sender_id)
    sender_participant = await create_participant(
        migrated_test_db, transfer_id, sender_id, "sender"
    )
    invitation_id = uuid4()
    await migrated_test_db.execute(
        text(
            "INSERT INTO transfer_invitations "
            "(id, transfer_id, created_by_user_id, kind, token_digest, expires_at) "
            "VALUES (:id, :transfer, :creator, 'link', :digest, :expires)"
        ),
        {
            "id": invitation_id,
            "transfer": transfer_id,
            "creator": sender_id,
            "digest": b"r" * 32,
            "expires": datetime.now(UTC) + timedelta(hours=1),
        },
    )

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO transfer_invitation_redemptions "
                    "(id, invitation_id, participant_id, transfer_id, user_id) "
                    "VALUES (:id, :invitation, :participant, :transfer, :user)"
                ),
                {
                    "id": uuid4(),
                    "invitation": invitation_id,
                    "participant": sender_participant,
                    "transfer": transfer_id,
                    "user": sender_id,
                },
            )


@pytest.mark.asyncio
async def test_invitation_is_single_use_in_v1(migrated_test_db) -> None:
    sender_id = await create_user(migrated_test_db, "single-use-sender")
    transfer_id = await create_transfer(migrated_test_db, sender_id)

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO transfer_invitations "
                    "(id, transfer_id, created_by_user_id, kind, token_digest, "
                    "expires_at, max_uses) "
                    "VALUES (:id, :transfer, :creator, 'link', :digest, :expires, 2)"
                ),
                {
                    "id": uuid4(),
                    "transfer": transfer_id,
                    "creator": sender_id,
                    "digest": b"s" * 32,
                    "expires": datetime.now(UTC) + timedelta(hours=1),
                },
            )


@pytest.mark.asyncio
async def test_transfer_event_requires_json_object(migrated_test_db) -> None:
    sender_id = await create_user(migrated_test_db, "event-sender")
    transfer_id = await create_transfer(migrated_test_db, sender_id)

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO transfer_events "
                    "(id, transfer_id, event_type, event_data) "
                    "VALUES (:id, :transfer, 'invalid_test', '[1, 2]'::jsonb)"
                ),
                {"id": uuid4(), "transfer": transfer_id},
            )


@pytest.mark.asyncio
async def test_session_expiry_must_be_after_creation(migrated_test_db) -> None:
    user_id = await create_user(migrated_test_db, "expired-session")

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO sessions (id, user_id, expires_at) VALUES (:id, :user, :expires)"
                ),
                {
                    "id": uuid4(),
                    "user": user_id,
                    "expires": datetime.now(UTC) - timedelta(seconds=1),
                },
            )


@pytest.mark.asyncio
async def test_invitation_expiry_must_be_after_creation(migrated_test_db) -> None:
    sender_id = await create_user(migrated_test_db, "expired-invitation")
    transfer_id = await create_transfer(migrated_test_db, sender_id)

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO transfer_invitations "
                    "(id, transfer_id, created_by_user_id, kind, token_digest, expires_at) "
                    "VALUES (:id, :transfer, :creator, 'link', :digest, :expires)"
                ),
                {
                    "id": uuid4(),
                    "transfer": transfer_id,
                    "creator": sender_id,
                    "digest": b"e" * 32,
                    "expires": datetime.now(UTC) - timedelta(seconds=1),
                },
            )


@pytest.mark.asyncio
async def test_recipient_response_requires_response_timestamp(migrated_test_db) -> None:
    sender_id = await create_user(migrated_test_db, "consent-sender")
    recipient_id = await create_user(migrated_test_db, "consent-recipient")
    transfer_id = await create_transfer(migrated_test_db, sender_id)

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text(
                    "INSERT INTO transfer_participants "
                    "(id, transfer_id, user_id, role, response_status) "
                    "VALUES (:id, :transfer, :user, 'recipient', 'accepted')"
                ),
                {"id": uuid4(), "transfer": transfer_id, "user": recipient_id},
            )


@pytest.mark.asyncio
async def test_completed_transfer_requires_acceptance_and_completion_timestamps(
    migrated_test_db,
) -> None:
    sender_id = await create_user(migrated_test_db, "completion-sender")
    transfer_id = await create_transfer(migrated_test_db, sender_id)

    with pytest.raises(IntegrityError):
        async with migrated_test_db.begin_nested():
            await migrated_test_db.execute(
                text("UPDATE transfers SET status = 'completed' WHERE id = :id"),
                {"id": transfer_id},
            )


@pytest.mark.asyncio
async def test_transfer_metadata_does_not_include_file_names_or_paths() -> None:
    transfer_columns = set(Base.metadata.tables["transfers"].columns.keys())
    forbidden_columns = {
        "file_name",
        "file_names",
        "source_path",
        "destination_path",
        "manifest_json",
        "file_content",
        "payload",
    }
    assert transfer_columns.isdisjoint(forbidden_columns)


@pytest.mark.asyncio
async def test_transfer_uses_optimistic_versioning_for_concurrent_updates(
    migrated_test_engine,
) -> None:
    session_factory = async_sessionmaker(migrated_test_engine, expire_on_commit=False)
    user_id = uuid4()
    transfer_id = uuid4()
    email = f"version-{user_id.hex}@example.test"

    async with session_factory() as setup_session:
        plan_id = await setup_session.scalar(text("SELECT id FROM plans WHERE code = 'free'"))
        setup_session.add(
            User(
                id=user_id,
                email=email,
                email_normalized=email,
                status="active",
                locale="fr",
            )
        )
        await setup_session.flush()
        setup_session.add(
            Transfer(
                id=transfer_id,
                created_by_user_id=user_id,
                plan_id=plan_id,
                status="awaiting_receiver",
                total_bytes=100,
                item_count=1,
                plan_code_snapshot="free",
                max_transfer_bytes_snapshot=10_000_000_000,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        await setup_session.commit()

    try:
        async with session_factory() as first_session, session_factory() as second_session:
            first_copy = await first_session.get(Transfer, transfer_id)
            second_copy = await second_session.get(Transfer, transfer_id)
            assert first_copy is not None
            assert second_copy is not None
            assert first_copy.version == second_copy.version == 1

            first_copy.total_bytes = 200
            await first_session.commit()
            assert first_copy.version == 2

            second_copy.item_count = 2
            with pytest.raises(StaleDataError):
                await second_session.commit()
            await second_session.rollback()
    finally:
        async with migrated_test_engine.begin() as connection:
            await connection.execute(
                text("DELETE FROM transfers WHERE id = :id"), {"id": transfer_id}
            )
            await connection.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
