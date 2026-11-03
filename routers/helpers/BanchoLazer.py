import os
import firebase_admin
from firebase_admin import credentials, firestore
from ossapi import GameMode, Ossapi

from routers.helpers.bancho import mods_to_legacy_id
from routers.helpers.calculation import id_to_mods

OSU_CLIENT_ID = int(os.getenv("OSU_CLIENT_ID", 0))
OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET", "")
token_directory=os.getenv("OSSAPI_TOKEN_DIRECTORY", "/tmp") if os.getenv("ENVIRONMENT") == "production" else None
api = Ossapi(
        OSU_CLIENT_ID,
        OSU_CLIENT_SECRET,
        # if in production, else remove this line to use default token directory
        token_directory=token_directory
    )

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
            "userAvatar": user_data.avatar_url,
        })

    def batch_insert_users(self, list_user_id: list[int]):
        batch = db.batch()
        users_ref = db.collection("users")

        for user_id in list_user_id:
            user_data = api.user(user_id)
            user_doc_ref = users_ref.document(str(user_id))
            batch.set(user_doc_ref, {
                "id": user_data.id,
                "name": user_data.username,
                "userAvatar": user_data.avatar_url,
            })

        batch.commit()
        print(f"Inserted {len(list_user_id)} users into Firestore.")

    def get_users(self, list_user_id: list[int]):
        users = []
        not_found_ids = []
        
        refs = [db.collection("users").document(str(doc_id)) for doc_id in list_user_id]
        docs = db.get_all(refs)

        for doc in docs:
            if doc.exists:
                users.append(doc.to_dict())
            else:
                not_found_ids.append(int(doc.id))

        if len(not_found_ids) > 0:
            self.batch_insert_users(not_found_ids)
            # Fetch the newly inserted users
            users.extend(user for user in self.get_users(not_found_ids))  # Recursive call to get the newly inserted users

        return users

    def getBeatmapLeaderboardBanchoLazer(self, beatmap_id: int, modeNum: int):
        try:
            mode = GameMode(modeNum)
        except ValueError:
            mode = GameMode.OSU
        leaderboard = api.beatmap_scores(beatmap_id, mode=mode, limit=50).scores

        list_user_id = [score.user_id for score in leaderboard]
        users = self.get_users(list_user_id)
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
                                "name": next((user['name'] for user in users if user['id'] == score.user_id), None),
                                "userAvatar": f'https://a.ppy.sh/{score.user_id}',
                            },
                            "mods": {
                            "name": ''.join(mod.acronym for mod in score.mods),
                            "id":  mods_to_legacy_id(''.join(mod.acronym for mod in score.mods)),
                            }
                        }
        
            data.append(score_data)
        return data
            
