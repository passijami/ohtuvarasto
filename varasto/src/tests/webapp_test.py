import html
import unittest

from webapp import app


class TestWebApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["VARASTOT"].clear()
        self.client = app.test_client()

    def luo_varasto(self, nimi="Mehu", tilavuus="10"):
        return self.client.post(
            "/varastot",
            data={"nimi": nimi, "tilavuus": tilavuus},
            follow_redirects=True,
        )

    def teksti(self, vastaus):
        return html.unescape(vastaus.get_data(as_text=True))

    def lisaa(self, nimi="Mehu", maara="4"):
        return self.client.post(
            "/varastot/lisaa",
            data={"varasto": nimi, "maara": maara},
            follow_redirects=True,
        )

    def ota(self, nimi="Mehu", maara="2"):
        return self.client.post(
            "/varastot/ota",
            data={"varasto": nimi, "maara": maara},
            follow_redirects=True,
        )

    def test_paasivulla_on_lomakkeet(self):
        vastaus = self.client.get("/")
        self.assertEqual(vastaus.status_code, 200)
        teksti = self.teksti(vastaus)
        otsikot = ("Uusi varasto", "Varastot", "Lisää tavaraa", "Ota tavaraa")
        for otsikko in otsikot:
            self.assertIn(otsikko, teksti)

    def test_varaston_luonti_nayttyy_listassa(self):
        vastaus = self.luo_varasto()
        teksti = self.teksti(vastaus)
        self.assertIn("Varasto 'Mehu' luotu.", teksti)
        self.assertIn("<strong>Mehu</strong>", teksti)
        self.assertIn("tilavuus 10", teksti)
        self.assertIn("saldo 0", teksti)
        self.assertIn("vapaata tilaa 10", teksti)
        self.assertEqual(app.config["VARASTOT"]["Mehu"].tilavuus, 10)

    def test_lisays_kasvattaa_saldoa(self):
        self.luo_varasto()
        vastaus = self.lisaa(maara="4")
        self.assertIn("Lisätty 4 varastoon 'Mehu'.",
                      self.teksti(vastaus))
        self.assertAlmostEqual(app.config["VARASTOT"]["Mehu"].saldo, 4)

    def test_ottaminen_vahentaa_saldoa(self):
        self.luo_varasto()
        self.lisaa(maara="8")
        vastaus = self.ota(maara="3")
        self.assertIn("Otettu 3 varastosta 'Mehu'.",
                      self.teksti(vastaus))
        self.assertAlmostEqual(app.config["VARASTOT"]["Mehu"].saldo, 5)

    def test_ylitetty_tilavuus_estetaan(self):
        self.luo_varasto(tilavuus="10")
        vastaus = self.lisaa(maara="11")
        teksti = self.teksti(vastaus)
        self.assertIn("ei mahdu 11", teksti)
        self.assertIn("Vapaata tilaa on 10", teksti)
        self.assertAlmostEqual(app.config["VARASTOT"]["Mehu"].saldo, 0)

    def test_liian_suuri_poisto_estetaan(self):
        self.luo_varasto()
        self.lisaa(maara="5")
        vastaus = self.ota(maara="6")
        self.assertIn("Varastossa 'Mehu' on vain 5.",
                      self.teksti(vastaus))
        self.assertAlmostEqual(app.config["VARASTOT"]["Mehu"].saldo, 5)

    def test_virheellinen_luku_ilmoitetaan(self):
        vastaus = self.luo_varasto(tilavuus="kymmenen")
        self.assertIn("Tilavuus pitää ilmoittaa lukuna.",
                      self.teksti(vastaus))
        self.assertNotIn("Mehu", app.config["VARASTOT"])

    def test_sama_nimi_estetaan(self):
        self.luo_varasto()
        vastaus = self.luo_varasto(tilavuus="20")
        self.assertIn("on jo olemassa", self.teksti(vastaus))
        self.assertEqual(len(app.config["VARASTOT"]), 1)

    def test_tuntematon_varasto_ilmoitetaan(self):
        vastaus = self.lisaa(nimi="Puuttuva")
        self.assertIn("Varastoa 'Puuttuva' ei ole.", self.teksti(vastaus))

    def test_negatiivinen_maara_ilmoitetaan(self):
        self.luo_varasto()
        vastaus = self.lisaa(maara="-1")
        self.assertIn("Lisättävä määrä pitää olla suurempi kuin nolla.",
                      self.teksti(vastaus))
        self.assertAlmostEqual(app.config["VARASTOT"]["Mehu"].saldo, 0)

    def test_tyhja_nimi_ilmoitetaan(self):
        vastaus = self.luo_varasto(nimi="   ")
        self.assertIn("Varaston nimi ei voi olla tyhjä.", self.teksti(vastaus))
        self.assertEqual(app.config["VARASTOT"], {})

    def test_poisto_tuntemattomasta_varastosta_ilmoitetaan(self):
        vastaus = self.ota(nimi="Puuttuva")
        self.assertIn("Varastoa 'Puuttuva' ei ole.", self.teksti(vastaus))

    def test_virheellinen_poistettava_maara_ilmoitetaan(self):
        self.luo_varasto()
        vastaus = self.ota(maara="kaksi")
        self.assertIn("Poistettava määrä pitää ilmoittaa lukuna.",
                      self.teksti(vastaus))
