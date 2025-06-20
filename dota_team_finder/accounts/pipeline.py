from requests import request
from transliterate import translit


def fill_customuser_fields(strategy, details, user=None, *args, **kwargs):
    if user is None:
        return

    # Получаем данные Steam
    social = user.social_auth.filter(provider='steam').first()
    if social:
        data = social.extra_data.get('player', {})
        user.slug = translit(data.get('personaname', ''), language_code='ru', reversed=True)
        user.steam_id = social.uid
        user.steam_avatar = data.get('avatarfull', '')
        user.steam_nickname = data.get('personaname', '')
        user.url = data.get('profileurl', '')

    # Получаем данные OpenDota
    if user.steam_id and user.mmr is None:
        steam32 = int(user.steam_id) - 76561197960265728
        try:
            response = request('GET', f'https://api.opendota.com/api/players/{steam32}')
            response.raise_for_status()
            response_wl = request('GET', f'https://api.opendota.com/api/players/{steam32}/wl')
            response_wl.raise_for_status()
        except Exception as e:
            print(f'Ошибка запроса к OpenDota: {e}')
            return
        user_data = response.json()
        user_data_wl = response_wl.json()
        user.mmr = int(user_data.get('rank_tier') or 0)
        user.wins = user_data_wl.get('win', 0)
        user.losses = user_data_wl.get('lose', 0)
        total = user.wins + user.losses
        user.win_rate = round((user.wins / total) * 100, 2) if total > 0 else 0
        user.rank = f"{str(user.mmr)[0]}-{str(user.mmr)[1]}" if user.mmr else None

    user.save() 