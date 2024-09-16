# BTD6 Maplist Bot

A Discord bot to check data with the BTD6 Maplist project.

## Running

1. Generate RSA keys, you only need the private one to sign messages. The public one is meant for [the API](https://github.com/SartoRiccardo/btd6maplist-api), to make sure messages come from the bot.
   - If you've already generated a key pair, simply move the private key here.
```bash
openssl genrsa -out btd6maplist-bot.pem 3072
openssl rsa -in btd6maplist-bot.pem -pubout -out btd6maplist-bot.pub.pem
```
2. Copy/rename `config.example.py` into `config.py` and fill it out accordingly
3. Copy/rename `bot/utils/emojis.example.py` into `bot/utils/emojis.py`.
   - Change the emotes into custom ones *(optional)*

