import datetime
import os
from concurrent.futures import ThreadPoolExecutor
import firebase_admin
from firebase_admin import credentials, firestore
from ossapi import GameMode, Mod, Ossapi

from routers.helpers.bancho import mods_to_legacy_id


OSU_CLIENT_ID = int(os.getenv("OSU_CLIENT_ID", 0))
OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET", "")
token_directory=os.getenv("OSSAPI_TOKEN_DIRECTORY", "/tmp") if os.getenv("ENVIRONMENT") == "production" else None

api = Ossapi(
        OSU_CLIENT_ID,
        OSU_CLIENT_SECRET,
        # if in production, else remove this line to use default token directory
        token_directory=token_directory,
    )

print("OSU_CLIENT_ID:", OSU_CLIENT_ID)
print("OSU_CLIENT_SECRET:", OSU_CLIENT_SECRET)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

class BanchoLazer:
    # def __init__(self):
    #     # OSU_API_KEY = os.getenv("OSU_API_KEY")

    def insert_user(self, user_id: int):
        user_data = api.user(user_id)
        db.collection("users").document(str(user_id)).set({
            "id": user_data.id,
            "name": user_data.username,
            "date_inserted": datetime.datetime.now(datetime.timezone.utc)
        })

    def batch_insert_users(self, list_user_id: list[int]):
        def fetch_user(user_id: int):
            user_data = api.user(user_id)
            return {
                "id": user_data.id,
                "name": user_data.username,
                "date_inserted": datetime.datetime.now(datetime.timezone.utc)
            }

        with ThreadPoolExecutor(max_workers=min(10, len(list_user_id))) as executor:
            user_data = list(executor.map(fetch_user, list_user_id))

        batch = db.batch()
        users_ref = db.collection("users")

        for user in user_data:
            user_doc_ref = users_ref.document(str(user["id"]))
            batch.set(user_doc_ref, user)

        batch.commit()
        print(f"Updated {len(list_user_id)} users into Firestore.")
        return user_data

    def batch_upsert_users(self, users: list[dict]):
        if not users:
            return

        batch = db.batch()
        users_ref = db.collection("users")
        for user in users:
            batch.set(users_ref.document(str(user["id"])), user)
        batch.commit()

    def get_users(self, list_user_id: list[int]):
        users = []
        not_found_ids = []

        refs = [db.collection("users").document(str(doc_id)) for doc_id in list_user_id]
        docs = db.get_all(refs)
        now = datetime.datetime.now(datetime.timezone.utc)

        for doc in docs:
            if doc.exists:
                # Check if date_inserted is older than 1 day
                user = doc.to_dict()
                date_inserted = user.get("date_inserted")
                # print(f"User ID: {doc.id}, Date Inserted: {date_inserted}")
                
                THRESHOLD_DAYS = 3  # Define the threshold in days
                if date_inserted is None or (now - date_inserted).days > THRESHOLD_DAYS:
                    # Update the user data if it's older than 1 day
                    not_found_ids.append(int(doc.id))
                else:
                    users.append(user)
            else:
                not_found_ids.append(int(doc.id))

        if not_found_ids:
            users.extend(self.batch_insert_users(not_found_ids))

        return users

    def getBeatmapLeaderboardBanchoLazer(self, beatmap_id: int, modeNum: int, mods: list[Mod] | None = None, legacy_only: bool = False):
        try:
            mode = GameMode(modeNum)
        except ValueError:
            mode = GameMode.OSU
        leaderboard = api.beatmap_scores(beatmap_id, mode=mode, limit=50, mods=mods, legacy_only=legacy_only).scores

        user_names = {}
        compact_users = []
        for score in leaderboard:
            user = getattr(score, "user", None)
            username = getattr(user, "username", None)
            if username:
                user_names[score.user_id] = username
                compact_users.append({
                    "id": score.user_id,
                    "name": username,
                    "date_inserted": datetime.datetime.now(datetime.timezone.utc),
                })

        # Persist the users returned with the leaderboard in one write batch.
        # This avoids a profile request for every new leaderboard user.
        self.batch_upsert_users(compact_users)

        missing_user_ids = list(dict.fromkeys(
            score.user_id for score in leaderboard
            if score.user_id not in user_names
        ))
        if missing_user_ids:
            user_names.update({
                user["id"]: user["name"]
                for user in self.get_users(missing_user_ids)
            })

        data = []

        for score in leaderboard:
            score_data = {
                            "rank": score.rank.value if score.rank else None,
                            "pp": score.pp if score.pp is not None else 0.0,
                            "accuracy": score.accuracy * 100,
                            "score": {
                                "total": score.total_score,
                            },
                            "combo": {
                                "max": score.max_combo,
                            },
                            "user": {
                                "id": score.user_id,
                                "name": user_names.get(score.user_id),
                                "userAvatar": f'https://a.ppy.sh/{score.user_id}',
                            },
                            "mods": {
                                "name": ''.join(mod.acronym for mod in score.mods),
                                "id":  mods_to_legacy_id(''.join(mod.acronym for mod in score.mods)),
                            }
                        }
        
            data.append(score_data)
        return data
            
