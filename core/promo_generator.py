import re
import html

def generate_viral_promo_pack(lot, seller_contact="@твой_юзернейм"):
    """
    Generates a viral TikTok / YouTube Shorts / Reels promo pack.
    Contains:
      - High-converting 3-second visual hook text
      - Ultra-short 10-12s voiceover script (<30 words)
      - Music/Phonk recommendations
      - Publication caption & viral hashtags (one-tap copy)
    """
    price = lot.get("price", 200)
    trophies = lot.get("trophies", 0)
    brawlers = lot.get("brawlers", 0)
    primes = lot.get("primes", 0)
    est_price = lot.get("est_tg_price", round(price * 2.2))
    desc_lower = lot.get("desc", "").lower()
    contact = seller_contact if seller_contact.startswith("@") else f"@{seller_contact}"

    # 1. Determine viral hook & voice script angle
    if any(k in desc_lower for k in ["шелли", "shelly", "рикошет", "кольт", "вирус", "гейл", "колетт", "вольт"]):
        hook_text = f"ШКОЛЬНИК НЕ ЗНАЛ ЧТО СЛИВАЕТ ЗА {price:g}₽... 💀"
        voice_script = (
            f"Я нашел древний олд-аккаунт с редкими архивными скинами всего за {price:g} рублей! "
            f"Владелец давно бросил игру, а здесь {brawlers} бойцов и родная почта. "
            f"Отдам первому в закрепе ТГК, ссылка в шапке профиля — успевай!"
        )
    elif trophies >= 25000:
        hook_text = f"ТОПОВУЮ ОСНОВУ {trophies:,} КУБКОВ СЛИЛИ ЗА {price:g}₽ 😱"
        voice_script = (
            f"Владелец за копейки отдал мощную основу на {trophies:,} кубков и {brawlers} бойцов! "
            f"Оценщик дал реальную цену {est_price} рублей. "
            f"Выложил этот акк в наш ТГ-канал по себестоимости, ссылка в шапке — забирай!"
        )
    elif brawlers >= 75 or primes >= 10:
        hook_text = f"АККАУНТ С ФУЛЛ БОЙЦАМИ ЗА {price:g} РУБЛЕЙ?! 😳"
        voice_script = (
            f"Купил готовую основу за {price:g} рублей: целых {brawlers} бойцов и {primes} праймов 11 уровня! "
            f"Отдам первому кто перейдет в ТГК, ссылка в шапке профиля!"
        )
    else:
        hook_text = f"КТО ПЕРВЫЙ НАПИШЕТ — ЗАБИРАЕТ ЗА КОПЕЙКИ! ⚡"
        voice_script = (
            f"Нашел окупной аккаунт в Brawl Stars всего за {price:g} рублей: {trophies:,} кубков и полная перепривязка! "
            f"Забирай в закрепе нашего ТГК, ссылка в шапке профиля!"
        )

    # 2. Viral publication caption & tags
    caption_text = f"Отдам первому в ТГК: {contact} (ссылка в шапке профиля) 🚀 #brawlstars #бравлстарс #бравл #аккаунты #рек #fyp #бравлстарсскины"

    return {
        "hook_text": hook_text,
        "voice_script": voice_script,
        "sound_recommendation": "🔥 Brazilian Phonk (Dxrk - RAVE / Montagem) или Slowed Remix",
        "video_format": "📱 Формат: 9:16 (Карусель фото в TikTok или слайдшоу в CapCut по 0.5-0.8 сек на скриншот)",
        "caption_text": caption_text,
        "contact": contact
    }
