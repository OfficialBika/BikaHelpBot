from __future__ import annotations

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.loader import mongo_db


def get_db() -> Optional[AsyncIOMotorDatabase]:
    return mongo_db


def is_mongo_available() -> bool:
    return mongo_db is not None


def get_collection(name: str) -> Optional[AsyncIOMotorCollection]:
    if mongo_db is None:
        return None
    return mongo_db[name]


async def ping_mongo() -> bool:
    if mongo_db is None:
        return False
    try:
        await mongo_db.command("ping")
        return True
    except Exception:
        return False


async def init_mongo_indexes() -> None:
    if mongo_db is None:
        return

    index_map: dict[str, list[IndexModel]] = {
        "chat_settings": [IndexModel([("chat_id", ASCENDING)], unique=True)],
        "notes": [IndexModel([("chat_id", ASCENDING), ("name", ASCENDING)], unique=True)],
        "filters": [IndexModel([("chat_id", ASCENDING), ("keyword", ASCENDING)], unique=True)],
        "warns": [IndexModel([("chat_id", ASCENDING), ("user_id", ASCENDING)], unique=True)],
        "blacklists": [IndexModel([("chat_id", ASCENDING), ("word", ASCENDING)], unique=True)],
        "tickets": [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)]),
        ],
        "support_admins": [IndexModel([("user_id", ASCENDING)], unique=True)],
    }

    for collection_name, indexes in index_map.items():
        collection = mongo_db[collection_name]
        await collection.create_indexes(indexes)


async def set_chat_setting(chat_id: int, key: str, value: Any) -> bool:
    collection = get_collection("chat_settings")
    if collection is None:
        return False

    await collection.update_one({"chat_id": chat_id}, {"$set": {key: value, "chat_id": chat_id}}, upsert=True)
    return True


async def get_chat_setting(chat_id: int, key: str, default: Any = None) -> Any:
    collection = get_collection("chat_settings")
    if collection is None:
        return default

    doc = await collection.find_one({"chat_id": chat_id})
    if not doc:
        return default
    return doc.get(key, default)


async def get_all_chat_settings(chat_id: int) -> dict[str, Any]:
    collection = get_collection("chat_settings")
    if collection is None:
        return {}

    doc = await collection.find_one({"chat_id": chat_id})
    if not doc:
        return {}

    doc.pop("_id", None)
    return doc


async def replace_chat_settings(chat_id: int, data: dict[str, Any]) -> bool:
    collection = get_collection("chat_settings")
    if collection is None:
        return False

    payload = {"chat_id": chat_id}
    for key, value in data.items():
        if key in {"_id", "chat_id"}:
            continue
        payload[key] = value

    await collection.update_one({"chat_id": chat_id}, {"$set": payload}, upsert=True)
    return True


async def delete_chat_setting(chat_id: int, key: str) -> bool:
    collection = get_collection("chat_settings")
    if collection is None:
        return False

    await collection.update_one({"chat_id": chat_id}, {"$unset": {key: ""}}, upsert=False)
    return True


async def add_note(chat_id: int, name: str, data: dict[str, Any]) -> bool:
    collection = get_collection("notes")
    if collection is None:
        return False

    name = name.strip().lower()
    payload = {"chat_id": chat_id, "name": name, **data}

    await collection.update_one({"chat_id": chat_id, "name": name}, {"$set": payload}, upsert=True)
    return True


async def get_note(chat_id: int, name: str) -> Optional[dict[str, Any]]:
    collection = get_collection("notes")
    if collection is None:
        return None

    return await collection.find_one({"chat_id": chat_id, "name": name.strip().lower()})


async def delete_note(chat_id: int, name: str) -> bool:
    collection = get_collection("notes")
    if collection is None:
        return False

    result = await collection.delete_one({"chat_id": chat_id, "name": name.strip().lower()})
    return result.deleted_count > 0


async def list_notes(chat_id: int, limit: int = 100) -> list[dict[str, Any]]:
    collection = get_collection("notes")
    if collection is None:
        return []

    cursor = collection.find({"chat_id": chat_id}).sort("name", 1).limit(limit)
    return await cursor.to_list(length=limit)


async def get_warn_settings(chat_id: int) -> dict[str, Any]:
    return {
        "warn_limit": await get_chat_setting(chat_id, "warn_limit", 3),
        "warn_action": await get_chat_setting(chat_id, "warn_action", "mute"),
    }


async def set_warn_limit(chat_id: int, limit: int) -> bool:
    return await set_chat_setting(chat_id, "warn_limit", int(limit))


async def set_warn_action(chat_id: int, action: str) -> bool:
    return await set_chat_setting(chat_id, "warn_action", action.strip().lower())


async def add_support_admin(user_id: int, added_by: int) -> bool:
    collection = get_collection("support_admins")
    if collection is None:
        return False

    await collection.update_one({"user_id": user_id}, {"$set": {"user_id": user_id, "added_by": added_by}}, upsert=True)
    return True


async def remove_support_admin(user_id: int) -> bool:
    collection = get_collection("support_admins")
    if collection is None:
        return False

    result = await collection.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def is_support_admin(user_id: int) -> bool:
    collection = get_collection("support_admins")
    if collection is None:
        return False

    doc = await collection.find_one({"user_id": user_id})
    return doc is not None


async def list_support_admins(limit: int = 100) -> list[dict[str, Any]]:
    collection = get_collection("support_admins")
    if collection is None:
        return []

    cursor = collection.find({}).sort("user_id", 1).limit(limit)
    return await cursor.to_list(length=limit)


async def export_chat_backup(chat_id: int) -> dict[str, Any]:
    settings = await get_all_chat_settings(chat_id)

    notes_col = get_collection("notes")
    filters_col = get_collection("filters")
    blacklists_col = get_collection("blacklists")

    notes = []
    filters = []
    blacklists = []

    if notes_col is not None:
        notes = await notes_col.find({"chat_id": chat_id}).sort("name", 1).to_list(length=10000)

    if filters_col is not None:
        filters = await filters_col.find({"chat_id": chat_id}).sort("keyword", 1).to_list(length=10000)

    if blacklists_col is not None:
        blacklists = await blacklists_col.find({"chat_id": chat_id}).sort("word", 1).to_list(length=10000)

    for item in notes:
        item.pop("_id", None)
    for item in filters:
        item.pop("_id", None)
    for item in blacklists:
        item.pop("_id", None)

    return {
        "chat_id": chat_id,
        "chat_settings": settings,
        "notes": notes,
        "filters": filters,
        "blacklists": blacklists,
    }


async def import_chat_backup(chat_id: int, payload: dict[str, Any]) -> dict[str, int]:
    settings_data = payload.get("chat_settings", {})
    notes_data = payload.get("notes", [])
    filters_data = payload.get("filters", [])
    blacklists_data = payload.get("blacklists", [])

    imported = {"settings": 0, "notes": 0, "filters": 0, "blacklists": 0}

    if isinstance(settings_data, dict):
        ok = await replace_chat_settings(chat_id, settings_data)
        imported["settings"] = 1 if ok else 0

    notes_col = get_collection("notes")
    filters_col = get_collection("filters")
    blacklists_col = get_collection("blacklists")

    if notes_col is not None and isinstance(notes_data, list):
        for item in notes_data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip().lower()
            if not name:
                continue
            clean_item = {k: v for k, v in item.items() if k not in {"_id", "chat_id"}}
            await notes_col.update_one(
                {"chat_id": chat_id, "name": name},
                {"$set": {"chat_id": chat_id, "name": name, **clean_item}},
                upsert=True,
            )
            imported["notes"] += 1

    if filters_col is not None and isinstance(filters_data, list):
        for item in filters_data:
            if not isinstance(item, dict):
                continue
            keyword = str(item.get("keyword", "")).strip().lower()
            if not keyword:
                continue
            clean_item = {k: v for k, v in item.items() if k not in {"_id", "chat_id"}}
            await filters_col.update_one(
                {"chat_id": chat_id, "keyword": keyword},
                {"$set": {"chat_id": chat_id, "keyword": keyword, **clean_item}},
                upsert=True,
            )
            imported["filters"] += 1

    if blacklists_col is not None and isinstance(blacklists_data, list):
        for item in blacklists_data:
            if not isinstance(item, dict):
                continue
            word = str(item.get("word", "")).strip().lower()
            if not word:
                continue
            await blacklists_col.update_one(
                {"chat_id": chat_id, "word": word},
                {"$set": {"chat_id": chat_id, "word": word}},
                upsert=True,
            )
            imported["blacklists"] += 1

    return imported
