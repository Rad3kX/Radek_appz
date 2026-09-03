# YouTube Transcript → Markdown

Streamlit aplikace, která z YouTube videa stáhne titulky (přes [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api)), seskupí je do čitelných odstavců s časovými značkami a umožní výsledek zobrazit i stáhnout jako `.md` soubor.

## Funkce

- Textové pole pro vložení YouTube odkazu (nebo přímo video ID)
- Volba preferovaných jazyků titulků (v pořadí priority, např. `cs, en`)
- Volitelné povolení automaticky generovaných titulků
- Seskupení přepisu do odstavců podle pauz v řeči a maximální délky odstavce (nastavitelné)
- Náhled výsledku jako Markdown přímo v aplikaci
- Stažení výsledku jako `.md` souboru

## Lokální spuštění

Vyžaduje Python 3.10+.

```bash
# 1. Vytvoř a aktivuj virtuální prostředí
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux

# 2. Nainstaluj závislosti
pip install -r requirements.txt

# 3. Spusť aplikaci
streamlit run app.py
```

Aplikace se otevře na `http://localhost:8501`.

## Nasazení na Streamlit Community Cloud

1. Nahraj repozitář (`app.py`, `requirements.txt`, `README.md`) na GitHub.
2. Jdi na [share.streamlit.io](https://share.streamlit.io) a přihlas se GitHub účtem.
3. Klikni na **New app**, vyber tento repozitář, branch (`main`) a soubor `app.py`.
4. Klikni na **Deploy** – Streamlit Cloud si sám nainstaluje závislosti z `requirements.txt`.
5. Po nasazení dostaneš veřejnou URL adresu aplikace (lze změnit v nastavení app).

### Poznámky k nasazení

- Aplikace nepotřebuje žádné API klíče ani secrets – `youtube-transcript-api` stahuje titulky přímo z YouTube.
- Pokud YouTube z IP adresy Streamlit Cloud dočasně blokuje požadavky (rate limiting), zkus to znovu později nebo spusť aplikaci lokálně.
- Pro soukromá/omezená videa nebo videa bez povolených titulků aplikace zobrazí chybovou hlášku.

## Poznámka k formátu titulků

Seskupování do odstavců je heuristické – nový odstavec začíná, když je pauza mezi větami delší než nastavený práh (výchozí 2 s) nebo když odstavec přesáhne nastavenou maximální délku (výchozí 500 znaků). Obojí lze upravit v sekci „Pokročilé nastavení seskupování odstavců“.
