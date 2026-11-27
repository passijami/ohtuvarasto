"""Ohtuvaraston web-käyttöliittymä."""

from flask import Flask, flash, redirect, render_template, request, url_for

from varasto import Varasto

app = Flask(__name__)
app.config["SECRET_KEY"] = "ohtuvarasto"
app.config["VARASTOT"] = {}


def varastot():
    return app.config["VARASTOT"]


def muotoile(luku):
    return f"{luku:g}"


def ohjaa(viesti, tyyppi):
    flash(viesti, tyyppi)
    return redirect(url_for("index"))


def lue_luku(teksti, nimi):
    try:
        luku = float(teksti.replace(",", "."))
    except ValueError:
        return None, f"{nimi} pitää ilmoittaa lukuna."
    if luku <= 0:
        return None, f"{nimi} pitää olla suurempi kuin nolla."
    return luku, None


def luo_varasto(nimi, tilavuus_teksti):
    if not nimi:
        return "Varaston nimi ei voi olla tyhjä.", "virhe"
    if nimi in varastot():
        return f"Varasto '{nimi}' on jo olemassa.", "virhe"
    tilavuus, virhe = lue_luku(tilavuus_teksti, "Tilavuus")
    if virhe:
        return virhe, "virhe"
    varastot()[nimi] = Varasto(tilavuus)
    return f"Varasto '{nimi}' luotu.", "onnistus"


def lisaa_tavaraa(nimi, maara_teksti):
    varasto = varastot().get(nimi)
    if varasto is None:
        return f"Varastoa '{nimi}' ei ole.", "virhe"
    maara, virhe = lue_luku(maara_teksti, "Lisättävä määrä")
    if virhe:
        return virhe, "virhe"
    vapaa = varasto.paljonko_mahtuu()
    if maara > vapaa:
        return (
            f"Varastoon '{nimi}' ei mahdu {muotoile(maara)}."
            f" Vapaata tilaa on {muotoile(vapaa)}."
        ), "virhe"
    varasto.lisaa_varastoon(maara)
    return f"Lisätty {muotoile(maara)} varastoon '{nimi}'.", "onnistus"


def ota_tavaraa(nimi, maara_teksti):
    varasto = varastot().get(nimi)
    if varasto is None:
        return f"Varastoa '{nimi}' ei ole.", "virhe"
    maara, virhe = lue_luku(maara_teksti, "Poistettava määrä")
    if virhe:
        return virhe, "virhe"
    saldo = varasto.saldo
    if maara > saldo:
        return f"Varastossa '{nimi}' on vain {muotoile(saldo)}.", "virhe"
    varasto.ota_varastosta(maara)
    return f"Otettu {muotoile(maara)} varastosta '{nimi}'.", "onnistus"


@app.route("/")
def index():
    return render_template("index.html", varastot=varastot())


@app.route("/varastot", methods=["POST"])
def luo_varasto_route():
    tulos = luo_varasto(request.form.get("nimi", "").strip(),
                        request.form.get("tilavuus", ""))
    return ohjaa(*tulos)


@app.route("/varastot/lisaa", methods=["POST"])
def lisaa_varastoon_route():
    tulos = lisaa_tavaraa(request.form.get("varasto", ""),
                          request.form.get("maara", ""))
    return ohjaa(*tulos)


@app.route("/varastot/ota", methods=["POST"])
def ota_varastosta_route():
    tulos = ota_tavaraa(request.form.get("varasto", ""),
                        request.form.get("maara", ""))
    return ohjaa(*tulos)
