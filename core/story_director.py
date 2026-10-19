import re
import logging

logger = logging.getLogger("StoryDirector")

def craft_viral_story(lot, seller_contact="@твой_юзернейм"):
    """
    Crafts high-retention viral storylines, dramatic hooks, and voiceover scripts
    custom-tailored to the specific account traits.
    """
    price = round(lot.get("price", 250))
    trophies = lot.get("trophies", 0)
    brawlers = lot.get("brawlers", 0)
    primes = lot.get("primes", 0)
    est_price = round(lot.get("est_tg_price", price * 2.2))
    desc_lower = lot.get("desc", "").lower()
    contact = seller_contact if seller_contact.startswith("@") else f"@{seller_contact}"

    # Archetype 1: OG Legacy / 3 AM Mystery find
    if any(k in desc_lower for k in ["шелли", "shelly", "рикошет", "кольт", "вирус", "2018", "2019", "гейл", "колетт"]):
        hook_headline = "НАШЕЛ В 3 ЧАСА НОЧИ ЗА КОПЕЙКИ... 💀"
        voice_script = (
            f"Я листал биржу в три часа ночи и не поверил своим глазам. "
            f"Владелец забросил игру много лет назад и выставил древний олд-аккаунт с редкими архивными скинами "
            f"всего за {price} рублей, думая что это обычный мусор! "
            f"Реальная цена этой основы — больше {est_price} рублей! "
            f"Я отдаю его первому в закрепе своего Телеграм-канала. Ссылка в шапке профиля — успевай!"
        )
        sub_text_2 = "👑 Редкие архивные скины"

    # Archetype 2: "Parents selling account / Bad grade drama" (for high trophies)
    elif trophies >= 25000:
        hook_headline = "РОДИТЕЛИ СЛИВАЮТ АКК ЗА ДВОЙКУ! 😭"
        voice_script = (
            f"Школьника заставили продать любимый аккаунт из-за двойки в четверти! "
            f"Чел в слезах выставил мощную основу на {trophies:,} кубков и {brawlers} бойцов "
            f"всего за {price} рублей! "
            f"Я успел выкупить этот аккаунт и отдаю его первому в закрепе своего Телеграм-канала. "
            f"Забирай по ссылке в шапке профиля!"
        )
        sub_text_2 = f"🏆 {trophies:,} кубков основы"

    # Archetype 3: "Mystery bargain / Maxed brawlers"
    elif brawlers >= 75 or primes >= 10:
        hook_headline = "ВЛАДЕЛЕЦ ДАЖЕ НЕ ЗНАЛ ЦЕНУ... 😱"
        voice_script = (
            f"Купил готовый аккаунт на бирже за {price} рублей, думая что это скам. "
            f"Но когда вошел на почту — у меня отвисла челюсть! "
            f"Тут целых {brawlers} бойцов и {primes} персонажей одиннадцатого уровня! "
            f"Срочно выложил этот аккаунт в свой Телеграм-канал. Ссылка в шапке профиля — забирай!"
        )
        sub_text_2 = f"⚡ {primes} праймов 11 уровня"

    # Archetype 4: Default high-speed flip
    else:
        hook_headline = "КУПИЛ САМЫЙ ДЕШЕВЫЙ АККАУНТ НА БИРЖЕ! 😳"
        voice_script = (
            f"Купил самый дешевый аккаунт в Brawl Stars всего за {price} рублей! "
            f"Родная чистая почта, полная перепривязка и отличная прокачка. "
            f"Выложил этот акк по себестоимости в закреп Телеграм-канала. Ссылка в шапке профиля!"
        )
        sub_text_2 = "🔒 Родная почта и гарантия"

    return {
        "hook_headline": hook_headline,
        "voice_script": voice_script,
        "sub_text_2": sub_text_2,
        "price": price,
        "est_price": est_price,
        "contact": contact
    }
